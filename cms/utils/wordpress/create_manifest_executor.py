"""Draft-only Directus create-manifest executor scaffold.

This executor consumes an already approved create manifest and produces local
reports by default. Real Directus writes are opt-in only and remain blocked
unless an explicit execute flag and token are provided by a future operator.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping

from directus_create_only import DirectusCreateOnlyClient, DirectusCreateOnlyConfig
from inventory.canonical import canonical_sha256, sha256_bytes
from pre_create_gates import (
    PreCreateGateError,
    validate_fresh_target_absence_report,
    validate_permission_evidence_report,
)


APPROVED_APPROVAL_SHA256 = "566ca0d3026ca9035853f623fc1d83d6b8fd31dc54bced9bbdc077c82ea266ee"
APPROVED_MANIFEST_SHA256 = "902e118a73acad4aacd504f6076ef867c7693f2d16144a45cdd78014269c6e4d"
EXPECTED_COUNTS = {
    "create_feed_draft": 28,
    "create_gallery_draft": 7,
    "total_operations": 35,
}
ALLOWED_OPERATIONS = frozenset({"create_feed_draft", "create_gallery_draft"})
FORBIDDEN_METHODS = frozenset({"PATCH", "PUT", "DELETE"})
ALLOWED_POST_ENDPOINTS = frozenset({"/items/feeds"})


class CreateManifestExecutorError(ValueError):
    """Raised when the approved manifest cannot be planned safely."""


@dataclass(frozen=True, slots=True)
class RequestPlanItem:
    operation_id: str
    operation: str
    source_identity: str
    method: str
    endpoint: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation": self.operation,
            "source_identity": self.source_identity,
            "method": self.method,
            "endpoint": self.endpoint,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class ExecutorReports:
    validation_report: dict[str, Any]
    request_plan: dict[str, Any]
    dry_run_report: dict[str, Any]
    stop_condition_report: dict[str, Any]


def load_and_validate_manifest(
    manifest_path: Path | str,
    *,
    approval_path: Path | str,
    expected_manifest_sha256: str = APPROVED_MANIFEST_SHA256,
    expected_approval_sha256: str = APPROVED_APPROVAL_SHA256,
) -> Mapping[str, Any]:
    manifest_path = Path(manifest_path)
    approval_path = Path(approval_path)
    manifest_sha256 = _file_sha256(manifest_path)
    approval_sha256 = _file_sha256(approval_path)
    if manifest_sha256 != expected_manifest_sha256:
        raise CreateManifestExecutorError(
            f"Manifest sha256 mismatch: expected {expected_manifest_sha256}, got {manifest_sha256}."
        )
    if approval_sha256 != expected_approval_sha256:
        raise CreateManifestExecutorError(
            f"Approval sha256 mismatch: expected {expected_approval_sha256}, got {approval_sha256}."
        )

    manifest = _read_json_object(manifest_path)
    approval = _read_json_object(approval_path)
    if manifest.get("approval", {}).get("sha256") != expected_approval_sha256:
        raise CreateManifestExecutorError("Manifest approval hash does not reference the approved approval artifact.")
    _validate_approval_artifact(approval)

    _validate_counts(manifest)
    _validate_operations(manifest)
    return manifest


def build_request_plan(manifest: Mapping[str, Any]) -> tuple[RequestPlanItem, ...]:
    operations = _operation_list(manifest)
    plan: list[RequestPlanItem] = []
    for operation in operations:
        method = "POST"
        endpoint = "/items/feeds"
        if method in FORBIDDEN_METHODS:
            raise CreateManifestExecutorError(f"Forbidden method in request plan: {method}.")
        if endpoint not in ALLOWED_POST_ENDPOINTS:
            raise CreateManifestExecutorError(f"Endpoint is not allowlisted for create execution: {endpoint}.")
        plan.append(
            RequestPlanItem(
                operation_id=_require_text(operation.get("operation_id"), "operation_id"),
                operation=_require_text(operation.get("operation"), "operation"),
                source_identity=_require_text(operation.get("source_identity"), "source_identity"),
                method=method,
                endpoint=endpoint,
                payload=_draft_feed_payload(operation),
            )
        )
    return tuple(plan)


def prepare_reports(
    *,
    manifest_path: Path | str,
    approval_path: Path | str,
    execute: bool = False,
    observed_at: datetime | None = None,
    expected_manifest_sha256: str = APPROVED_MANIFEST_SHA256,
    expected_approval_sha256: str = APPROVED_APPROVAL_SHA256,
) -> ExecutorReports:
    observed = observed_at or datetime.now(timezone.utc)
    manifest = load_and_validate_manifest(
        manifest_path,
        approval_path=approval_path,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_approval_sha256=expected_approval_sha256,
    )
    plan = build_request_plan(manifest)
    counts = Counter(item.operation for item in plan)
    planned_methods = sorted({item.method for item in plan})
    planned_endpoints = sorted({item.endpoint for item in plan})
    forbidden_planned_methods = sorted(set(planned_methods) & FORBIDDEN_METHODS)

    validation_report = {
        "kind": "validation_report",
        "observed_at": observed.isoformat(),
        "approval_sha256": expected_approval_sha256,
        "manifest_sha256": expected_manifest_sha256,
        "counts": {
            "create_feed_draft": counts.get("create_feed_draft", 0),
            "create_gallery_draft": counts.get("create_gallery_draft", 0),
            "total_operations": len(plan),
        },
        "target_status": "draft",
        "allowed_operations": sorted(ALLOWED_OPERATIONS),
        "forbidden_methods": sorted(FORBIDDEN_METHODS),
        "valid": True,
    }
    request_plan = {
        "kind": "request_plan",
        "observed_at": observed.isoformat(),
        "execute_requested": execute,
        "planned_methods": planned_methods,
        "planned_endpoints": planned_endpoints,
        "operation_count": len(plan),
        "operations": [item.to_dict() for item in plan],
    }
    dry_run_report = {
        "kind": "dry_run_report",
        "observed_at": observed.isoformat(),
        "dry_run": not execute,
        "non_read_requests_sent": 0 if not execute else None,
        "post_requests_sent": 0 if not execute else None,
        "execute_requires_explicit_flag": True,
    }
    stop_condition_report = {
        "kind": "stop_condition_report",
        "observed_at": observed.isoformat(),
        "blocked": bool(forbidden_planned_methods),
        "stop_conditions": [
            "Directus token missing or not proven create-only",
            "Any planned PATCH, PUT, or DELETE",
            "Any non-draft target status",
            "Any unsupported operation",
            "Any missing or mismatched source record",
            "Any non-allowlisted endpoint",
            "Any need to upload media or mutate existing Directus artifacts",
        ],
        "forbidden_planned_methods": forbidden_planned_methods,
    }
    return ExecutorReports(
        validation_report=validation_report,
        request_plan=request_plan,
        dry_run_report=dry_run_report,
        stop_condition_report=stop_condition_report,
    )


def run_executor(
    *,
    manifest_path: Path | str,
    approval_path: Path | str,
    output_dir: Path | str,
    execute: bool = False,
    directus_url: str = "https://cap-cms.skunklabs.uk",
    auth_token: str | None = None,
    client: DirectusCreateOnlyClient | None = None,
    permission_evidence_path: Path | str | None = None,
    fresh_target_absence_path: Path | str | None = None,
    expected_manifest_sha256: str = APPROVED_MANIFEST_SHA256,
    expected_approval_sha256: str = APPROVED_APPROVAL_SHA256,
) -> dict[str, Any]:
    reports = prepare_reports(
        manifest_path=manifest_path,
        approval_path=approval_path,
        execute=execute,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_approval_sha256=expected_approval_sha256,
    )
    executed = 0
    if execute:
        _validate_execute_gates(
            manifest_path=manifest_path,
            approval_path=approval_path,
            directus_url=directus_url,
            auth_token=auth_token,
            permission_evidence_path=permission_evidence_path,
            fresh_target_absence_path=fresh_target_absence_path,
            expected_manifest_sha256=expected_manifest_sha256,
            expected_approval_sha256=expected_approval_sha256,
        )
        execution_client = client or DirectusCreateOnlyClient(
            config=DirectusCreateOnlyConfig(
                base_url=directus_url,
                allowed_item_collections=("feeds",),
                allow_files=False,
                allow_folders=False,
                auth_token=auth_token,
            )
        )
        if execution_client is not client:
            execution_client.close()
        paths = write_reports(reports, output_dir=output_dir)
        raise CreateManifestExecutorError(
            "Execution boundary passed, but real writer is not implemented in this slice."
        )

    paths = write_reports(reports, output_dir=output_dir)
    return {
        "execute": execute,
        "executed_operations": executed,
        "reports": {name: str(path) for name, path in paths.items()},
        "request_plan_sha256": canonical_sha256(reports.request_plan),
    }


def write_reports(reports: ExecutorReports, *, output_dir: Path | str) -> dict[str, Path]:
    destination = Path(output_dir)
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(destination, 0o700)
    except PermissionError:
        pass
    payloads = {
        "validation_report": reports.validation_report,
        "request_plan": reports.request_plan,
        "dry_run_report": reports.dry_run_report,
        "stop_condition_report": reports.stop_condition_report,
    }
    paths: dict[str, Path] = {}
    for name, payload in payloads.items():
        path = destination / f"{name}.json"
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing report: {path}")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except PermissionError:
            pass
        paths[name] = path
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and plan the approved CAP draft-only Directus create manifest.",
    )
    parser.add_argument("--manifest", required=True, help="Approved create-manifest-draft-only.json path.")
    parser.add_argument("--approval", required=True, help="Approved migration-approval.json path.")
    parser.add_argument("--output-dir", required=True, help="Run directory outside Git for generated reports.")
    parser.add_argument("--directus-url", default="https://cap-cms.skunklabs.uk")
    parser.add_argument("--permission-evidence", help="permission-evidence-create-only.json path for execute mode.")
    parser.add_argument("--fresh-target-absence", help="fresh-target-absence-before-create.json path for execute mode.")
    parser.add_argument("--execute", action="store_true", help="Actually emit POST requests. Omit for dry-run.")
    args = parser.parse_args(argv)
    token = os.environ.get("DIRECTUS_TOKEN") if args.execute else None
    result = run_executor(
        manifest_path=args.manifest,
        approval_path=args.approval,
        output_dir=args.output_dir,
        execute=args.execute,
        directus_url=args.directus_url,
        auth_token=token,
        permission_evidence_path=args.permission_evidence,
        fresh_target_absence_path=args.fresh_target_absence,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _validate_execute_gates(
    *,
    manifest_path: Path | str,
    approval_path: Path | str,
    directus_url: str,
    auth_token: str | None,
    permission_evidence_path: Path | str | None,
    fresh_target_absence_path: Path | str | None,
    expected_manifest_sha256: str,
    expected_approval_sha256: str,
) -> None:
    if permission_evidence_path is None:
        raise CreateManifestExecutorError("--permission-evidence is required when --execute is used.")
    if fresh_target_absence_path is None:
        raise CreateManifestExecutorError("--fresh-target-absence is required when --execute is used.")
    if auth_token is None or not auth_token.strip():
        raise CreateManifestExecutorError("DIRECTUS_TOKEN is required when --execute is used.")

    manifest = load_and_validate_manifest(
        manifest_path,
        approval_path=approval_path,
        expected_manifest_sha256=expected_manifest_sha256,
        expected_approval_sha256=expected_approval_sha256,
    )
    permission_evidence = _read_json_object(Path(permission_evidence_path))
    fresh_target_absence = _read_json_object(Path(fresh_target_absence_path))

    try:
        validate_permission_evidence_report(
            permission_evidence,
            expected_target_url=directus_url,
        )
        validate_fresh_target_absence_report(
            fresh_target_absence,
            manifest,
            expected_target_url=directus_url,
            expected_manifest_sha256=expected_manifest_sha256,
            expected_approval_sha256=expected_approval_sha256,
            expected_operation_count=EXPECTED_COUNTS["total_operations"],
        )
    except PreCreateGateError as exc:
        raise CreateManifestExecutorError(str(exc)) from exc


def _validate_counts(manifest: Mapping[str, Any]) -> None:
    counts = manifest.get("counts")
    if not isinstance(counts, Mapping):
        raise CreateManifestExecutorError("Manifest counts are missing.")
    for key, expected in EXPECTED_COUNTS.items():
        if counts.get(key) != expected:
            raise CreateManifestExecutorError(
                f"Manifest count mismatch for {key}: expected {expected}, got {counts.get(key)}."
            )


def _validate_approval_artifact(approval: Mapping[str, Any]) -> None:
    if approval.get("kind") != "cap_wordpress_migration_approval":
        raise CreateManifestExecutorError("Approval artifact kind is not recognized.")
    approved = approval.get("approved")
    counts = approval.get("counts")
    if not isinstance(approved, Mapping) or not isinstance(counts, Mapping):
        raise CreateManifestExecutorError("Approval artifact is missing approved candidates or counts.")
    article_candidates = approved.get("article_create_candidates")
    gallery_candidates = approved.get("gallery_create_candidates")
    if not isinstance(article_candidates, list) or not isinstance(gallery_candidates, list):
        raise CreateManifestExecutorError("Approval artifact candidate lists are malformed.")
    if len(article_candidates) != EXPECTED_COUNTS["create_feed_draft"]:
        raise CreateManifestExecutorError("Approval artifact article candidate count mismatch.")
    if len(gallery_candidates) != EXPECTED_COUNTS["create_gallery_draft"]:
        raise CreateManifestExecutorError("Approval artifact gallery candidate count mismatch.")
    if counts.get("approved_article_create_candidates") != EXPECTED_COUNTS["create_feed_draft"]:
        raise CreateManifestExecutorError("Approval artifact approved article count mismatch.")
    if counts.get("approved_gallery_create_candidates") != EXPECTED_COUNTS["create_gallery_draft"]:
        raise CreateManifestExecutorError("Approval artifact approved gallery count mismatch.")


def _validate_operations(manifest: Mapping[str, Any]) -> None:
    operations = _operation_list(manifest)
    if len(operations) != EXPECTED_COUNTS["total_operations"]:
        raise CreateManifestExecutorError("Manifest operation list length does not match approved count.")
    for operation in operations:
        operation_type = _require_text(operation.get("operation"), "operation")
        if operation_type not in ALLOWED_OPERATIONS:
            raise CreateManifestExecutorError(f"Unsupported operation: {operation_type}.")
        if operation.get("target_status") != "draft":
            raise CreateManifestExecutorError("Every operation must target draft status.")
        if operation.get("write_policy") != "create_only":
            raise CreateManifestExecutorError("Every operation must use create_only write policy.")
        forbidden = {str(method).upper() for method in operation.get("forbidden_methods", [])}
        if not FORBIDDEN_METHODS.issubset(forbidden):
            raise CreateManifestExecutorError("Operation forbidden_methods must include PATCH, PUT, and DELETE.")
        if any(str(value).lower() in {"update", "delete", "patch", "put"} for value in operation.values() if isinstance(value, str)):
            raise CreateManifestExecutorError("Operation contains update/delete intent.")
        source_record = operation.get("source_record")
        if not isinstance(source_record, Mapping):
            raise CreateManifestExecutorError("Operation is missing source_record.")
        if source_record.get("identity") != operation.get("source_identity"):
            raise CreateManifestExecutorError("Operation source_identity does not match source_record identity.")
        if source_record.get("sha256") != operation.get("source_sha256"):
            raise CreateManifestExecutorError("Operation source_sha256 does not match source_record sha256.")
        if source_record.get("scope") != "source":
            raise CreateManifestExecutorError("Operation source_record must have source scope.")
        if operation_type == "create_feed_draft" and source_record.get("entity_type") != "wordpress_post":
            raise CreateManifestExecutorError("create_feed_draft requires a wordpress_post source record.")
        if operation_type == "create_gallery_draft" and source_record.get("entity_type") != "wordpress_gallery_album":
            raise CreateManifestExecutorError("create_gallery_draft requires a wordpress_gallery_album source record.")


def _draft_feed_payload(operation: Mapping[str, Any]) -> dict[str, Any]:
    source_record = operation["source_record"]
    data = source_record["data"]
    payload = {
        "status": "draft",
        "slug": data.get("slug"),
        "title": _rendered(data.get("title")) or data.get("slug"),
        "content": _rendered(data.get("content")),
        "description": _rendered(data.get("excerpt")),
        "date": data.get("date"),
        "original_uri": operation.get("original_uri") or source_record.get("source_url"),
        "gallery": operation.get("operation") == "create_gallery_draft",
    }
    return {key: value for key, value in payload.items() if value not in (None, "")}


def _rendered(value: Any) -> str | None:
    if isinstance(value, Mapping):
        rendered = value.get("rendered")
        if isinstance(rendered, str):
            return rendered
    if isinstance(value, str):
        return value
    return None


def _operation_list(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        raise CreateManifestExecutorError("Manifest operations must be a list.")
    if not all(isinstance(operation, Mapping) for operation in operations):
        raise CreateManifestExecutorError("Every manifest operation must be an object.")
    return operations


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise CreateManifestExecutorError(f"JSON artifact must contain an object: {path}")
    return payload


def _file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CreateManifestExecutorError(f"{field_name} must be a non-empty string.")
    return value.strip()


if __name__ == "__main__":
    raise SystemExit(main())
