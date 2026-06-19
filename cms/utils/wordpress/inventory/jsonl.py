"""Deterministic JSON Lines rendering for inventory manifests."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
import json

from .canonical import canonical_json, sha256_bytes
from .models import InventoryIssue, InventoryManifest, InventoryScope, ManifestRecord


def iter_manifest_jsonl_lines(manifest: InventoryManifest) -> Iterator[str]:
    header = {
        "kind": "manifest_header",
        "schema_version": manifest.schema_version,
        "scope": manifest.scope.value,
        "environment": manifest.environment,
        "base_url": manifest.base_url,
        "observed_at": manifest.observed_at,
        "metadata": manifest.metadata,
        "record_count": len(manifest.records),
        "issue_count": len(manifest.issues),
    }
    yield canonical_json(header)

    for record in manifest.records:
        yield canonical_json({"kind": "record", **record.to_dict()})

    for issue in manifest.issues:
        yield canonical_json({"kind": "issue", **issue.to_dict()})

    yield canonical_json(
        {
            "kind": "manifest_trailer",
            "schema_version": manifest.schema_version,
            "scope": manifest.scope.value,
            "record_count": len(manifest.records),
            "issue_count": len(manifest.issues),
            "content_sha256": manifest.content_sha256,
            "manifest_sha256": manifest.manifest_sha256,
        }
    )


def render_manifest_jsonl(manifest: InventoryManifest) -> bytes:
    return ("\n".join(iter_manifest_jsonl_lines(manifest)) + "\n").encode("utf-8")


def manifest_jsonl_sha256(manifest: InventoryManifest) -> str:
    return sha256_bytes(render_manifest_jsonl(manifest))


def read_manifest_jsonl(path: str | Path) -> InventoryManifest:
    """Load a manifest produced by this module's render format."""

    source_path = Path(path)
    lines = source_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Manifest JSONL file is empty: {source_path}")

    header = _parse_line(lines[0], kind="manifest_header", path=source_path, index=1)
    trailer = _parse_line(lines[-1], kind="manifest_trailer", path=source_path, index=len(lines))
    if len(lines) == 1:
        raise ValueError(f"Manifest JSONL file is missing record and trailer lines: {source_path}")

    records: list[ManifestRecord] = []
    issues: list[InventoryIssue] = []
    for index, line in enumerate(lines[1:-1], start=2):
        payload = _parse_json_line(line, path=source_path, index=index)
        kind = payload.get("kind")
        if kind == "record":
            records.append(_record_from_payload(payload, path=source_path, index=index))
        elif kind == "issue":
            issues.append(_issue_from_payload(payload, path=source_path, index=index))
        else:
            raise ValueError(
                f"Unexpected JSONL kind {kind!r} in {source_path} at line {index}."
            )

    observed_at = _parse_datetime(header.get("observed_at"), path=source_path)
    manifest = InventoryManifest(
        scope=InventoryScope(header["scope"]),
        environment=header["environment"],
        base_url=header["base_url"],
        observed_at=observed_at,
        records=records,
        issues=issues,
        metadata=header.get("metadata") or {},
        schema_version=header["schema_version"],
    )

    expected_counts = {
        "record_count": len(records),
        "issue_count": len(issues),
    }
    for key, expected in expected_counts.items():
        if header.get(key) != expected or trailer.get(key) != expected:
            raise ValueError(
                f"Manifest JSONL count mismatch for {key} in {source_path}."
            )

    if trailer.get("content_sha256") != manifest.content_sha256:
        raise ValueError(
            f"Manifest JSONL content hash mismatch in {source_path}."
        )
    if trailer.get("manifest_sha256") != manifest.manifest_sha256:
        raise ValueError(
            f"Manifest JSONL manifest hash mismatch in {source_path}."
        )

    return manifest


def _parse_line(
    line: str,
    *,
    kind: str,
    path: Path,
    index: int,
) -> dict[str, object]:
    payload = _parse_json_line(line, path=path, index=index)
    if payload.get("kind") != kind:
        raise ValueError(
            f"Expected {kind!r} in {path} at line {index}, got {payload.get('kind')!r}."
        )
    return payload


def _parse_json_line(line: str, *, path: Path, index: int) -> dict[str, object]:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path} at line {index}.") from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"Manifest JSONL line {index} in {path} must decode to an object."
        )
    return payload


def _record_from_payload(
    payload: dict[str, object],
    *,
    path: Path,
    index: int,
) -> ManifestRecord:
    try:
        return ManifestRecord(
            scope=payload["scope"],
            entity_type=payload["entity_type"],
            identity=payload["identity"],
            source_url=payload.get("source_url"),
            data=payload["data"],
            schema_version=payload["schema_version"],
        )
    except KeyError as exc:
        raise ValueError(
            f"Manifest JSONL record in {path} at line {index} is missing {exc.args[0]!r}."
        ) from exc


def _issue_from_payload(
    payload: dict[str, object],
    *,
    path: Path,
    index: int,
) -> InventoryIssue:
    try:
        return InventoryIssue(
            scope=payload["scope"],
            severity=payload["severity"],
            code=payload["code"],
            message=payload["message"],
            entity_type=payload.get("entity_type"),
            identity=payload.get("identity"),
            details=payload.get("details") or {},
            schema_version=payload["schema_version"],
        )
    except KeyError as exc:
        raise ValueError(
            f"Manifest JSONL issue in {path} at line {index} is missing {exc.args[0]!r}."
        ) from exc


def _parse_datetime(value: object, *, path: Path) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"Manifest JSONL observed_at must be a string in {path}.")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Manifest JSONL observed_at is invalid in {path}.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"Manifest JSONL observed_at must be timezone-aware in {path}.")
    return parsed
