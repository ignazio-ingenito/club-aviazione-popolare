"""Deterministic JSON Lines rendering for inventory manifests."""

from __future__ import annotations

from collections.abc import Iterator

from .canonical import canonical_json, sha256_bytes
from .models import InventoryManifest


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
