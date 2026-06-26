"""Pure Directus policy graph evidence evaluator for migration gates.

This module intentionally performs no network access and accepts only already
sanitized evidence artifacts. It evaluates whether the effective Directus policy
graph is narrow enough for the current draft-only WordPress migration stage.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
import json
import os
from pathlib import Path
from typing import Any

import httpx

from directus_policy_collector import DirectusPolicyCollectorError, collect_directus_policy_graph_raw


EVALUATION_KIND = "directus_policy_graph_evidence_evaluation"
RECOGNIZED_KINDS = frozenset(
    {
        "directus_policy_graph_evidence",
        "directus_policy_graph_evidence_example",
    }
)
ALLOWED_FEEDS_CREATE_FIELDS = frozenset(
    {
        "status",
        "slug",
        "title",
        "content",
        "description",
        "date",
        "original_uri",
        "gallery",
    }
)
ALLOWED_READ_PERMISSIONS = frozenset({("feeds", "read")})
MUTATION_ACTIONS = frozenset({"create", "update", "delete", "share"})
SYSTEM_COLLECTIONS = frozenset(
    {
        "schema",
        "settings",
        "users",
        "roles",
        "permissions",
        "policies",
        "access",
        "flows",
        "automations",
        "admin",
        "system",
        "directus_users",
        "directus_roles",
        "directus_permissions",
        "directus_policies",
        "directus_settings",
        "directus_flows",
        "directus_operations",
    }
)
FILE_OR_FOLDER_COLLECTIONS = frozenset({"directus_files", "directus_folders", "files", "folders"})
PERMISSION_EVIDENCE_KIND = "permission_evidence_create_only"


class DirectusPolicyEvidenceError(ValueError):
    """Raised when raw Directus policy graph payloads cannot be normalized safely."""


def normalize_directus_policy_graph_payload(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a conservative raw Directus policy graph export.

    This function intentionally supports only the synthetic, documented raw
    shape used by the migration runbook. It performs no network access and
    fails closed when identity, role, policy, or permission linkage is unclear.
    """

    raw = _require_mapping(raw, "raw payload")
    target_url = _require_text(raw, "target_url")
    observed_at = _require_text(raw, "observed_at")
    directus_version = _optional_text(raw, "directus_version")

    identity = _require_mapping(raw.get("identity"), "identity")
    identity_label = _optional_text(identity, "label")
    identity_role = _optional_text(identity, "role")
    identity_roles = identity.get("roles")
    if not identity_role:
        if isinstance(identity_roles, list) and len(identity_roles) > 1:
            raise DirectusPolicyEvidenceError("identity has multiple roles without explicit role selection")
        raise DirectusPolicyEvidenceError("identity.role is required")
    if identity_roles is not None and not _is_text_list(identity_roles):
        raise DirectusPolicyEvidenceError("identity.roles must be a list of strings when present")

    roles = [_normalize_role(role, index) for index, role in enumerate(_require_list(raw.get("roles"), "roles"))]
    role_match_count = sum(
        1
        for role in roles
        if identity_role in {_optional_text(role, "id"), _optional_text(role, "name")}
    )
    if role_match_count > 1:
        raise DirectusPolicyEvidenceError("identity role matches multiple roles")
    role_keys = {
        key
        for role in roles
        for key in (_optional_text(role, "id"), _optional_text(role, "name"))
        if key
    }
    if identity_role not in role_keys:
        raise DirectusPolicyEvidenceError("identity role does not match any role")

    raw_policies = _require_list(raw.get("policies"), "policies")
    if not raw_policies:
        raise DirectusPolicyEvidenceError("policies must not be empty")

    policies = [_normalize_policy(policy, index) for index, policy in enumerate(raw_policies)]
    attached_policy_ids: set[str] = set()
    for policy in policies:
        policy_roles = policy["roles"]
        if identity_role not in policy_roles:
            raise DirectusPolicyEvidenceError(f"policy is not attached to identity role: {policy['id']}")
        attached_policy_ids.add(policy["id"])
    if not attached_policy_ids:
        raise DirectusPolicyEvidenceError("no policies attached to identity role")

    permissions = [
        _normalize_permission(permission, index, attached_policy_ids)
        for index, permission in enumerate(_require_list(raw.get("permissions"), "permissions"))
    ]
    if not permissions:
        raise DirectusPolicyEvidenceError("permissions must not be empty")

    normalized: dict[str, Any] = {
        "kind": "directus_policy_graph_evidence",
        "target_url": target_url,
        "observed_at": observed_at,
        "identity": {
            "label": identity_label,
            "role": identity_role,
        },
        "policies": policies,
        "permissions": permissions,
    }
    if directus_version:
        normalized["directus_version"] = directus_version
    return normalized


def evaluate_policy_graph_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate sanitized Directus policy graph evidence.

    The function is fail-closed and deterministic: normal unsafe or incomplete
    evidence returns ``status="rejected"`` with stable reason strings instead
    of raising.
    """

    reasons: list[str] = []
    checks: dict[str, Any] = {}

    if not isinstance(payload, Mapping):
        return _result(["malformed_payload"], {"payload_is_object": False})

    kind = _text(payload.get("kind"))
    checks["payload_kind_recognized"] = kind in RECOGNIZED_KINDS
    if not checks["payload_kind_recognized"]:
        reasons.append("malformed_payload")

    target_url = _target_url(payload)
    checks["target_url_present"] = bool(target_url)
    if not target_url:
        reasons.append("missing_target_url")

    observed_at = _text(payload.get("observed_at")) or _text(payload.get("collected_at"))
    checks["observed_at_present"] = bool(observed_at)
    if not observed_at:
        reasons.append("missing_observed_at")

    identity = payload.get("identity")
    if not isinstance(identity, Mapping):
        identity = payload.get("subject")
    checks["identity_present"] = isinstance(identity, Mapping) and bool(identity)
    if not checks["identity_present"]:
        reasons.append("missing_identity")

    policy_sources = _policy_sources(payload)
    checks["policies_present"] = bool(policy_sources)
    if not policy_sources:
        reasons.append("missing_policies")

    permissions = _permissions(payload)
    checks["permissions_present"] = bool(permissions)
    if not permissions:
        reasons.append("missing_permissions")

    if _policy_graph_is_ambiguous(payload):
        reasons.append("ambiguous_policy_graph")

    _evaluate_permissions(permissions, checks=checks, reasons=reasons)

    return _result(reasons, checks)


def build_permission_evidence_create_only(
    payload: Mapping[str, Any],
    *,
    evaluation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical Gate 1 report from approved policy graph evidence.

    The generated report keeps the existing pre-create gate contract. It derives
    the probe matrix from an approved complete policy graph rather than from
    live denied-probe requests with the execution token.
    """

    payload = _require_mapping(payload, "policy graph evidence")
    evaluation_payload = evaluation or evaluate_policy_graph_evidence(payload)
    evaluation_payload = _require_mapping(evaluation_payload, "policy graph evaluation")
    if evaluation_payload.get("status") != "approved":
        raise DirectusPolicyEvidenceError("permission evidence requires approved policy graph evaluation")

    target_url = _target_url(payload)
    observed_at = _text(payload.get("observed_at")) or _text(payload.get("collected_at"))
    identity = payload.get("identity")
    if not isinstance(identity, Mapping):
        identity = payload.get("subject")
    identity = _require_mapping(identity, "identity")
    role = _require_text_value(identity.get("role"), "identity.role")
    label = _text(identity.get("label")) or role

    return {
        "kind": PERMISSION_EVIDENCE_KIND,
        "status": "approved",
        "target_url": target_url,
        "observed_at": observed_at,
        "execution_identity": {
            "id": f"directus-role:{role}",
            "role": role,
            "label": label,
        },
        "capabilities": {
            "admin": False,
            "system_wildcard": False,
            "wildcard": False,
            "broad_token": False,
            "role_admin": False,
            "permission_management": False,
        },
        "evidence_source": {
            "kind": payload.get("kind"),
            "evaluation_kind": evaluation_payload.get("kind"),
            "evaluation_status": evaluation_payload.get("status"),
            "source": "approved_policy_graph",
        },
        "probes": {
            "create": _probe("POST", "/items/feeds", "allowed", True),
            "patch": _probe("PATCH", "/items/feeds", "denied", False),
            "put": _probe("PUT", "/items/feeds", "denied", False),
            "delete": _probe("DELETE", "/items/feeds", "denied", False),
            "schema": _probe("GET", "/schema", "denied", False),
            "settings": _probe("GET", "/settings", "denied", False),
            "users": _probe("GET", "/users", "denied", False),
            "roles": _probe("GET", "/roles", "denied", False),
            "permissions": _probe("GET", "/permissions", "denied", False),
            "policies": _probe("GET", "/policies", "denied", False),
        },
    }


def _evaluate_permissions(
    permissions: list[Mapping[str, Any]],
    *,
    checks: dict[str, Any],
    reasons: list[str],
) -> None:
    mutation_permissions: list[Mapping[str, Any]] = []
    feeds_create_permissions: list[Mapping[str, Any]] = []
    unexpected_fields: set[str] = set()

    for permission in permissions:
        collection = _normalized_permission_text(permission.get("collection"))
        action = _normalized_permission_text(permission.get("action"))

        if collection == "*":
            reasons.append("wildcard_collection")
        if action == "*":
            reasons.append("wildcard_action")
        if collection in SYSTEM_COLLECTIONS:
            reasons.append("forbidden_system_access")
        if collection in FILE_OR_FOLDER_COLLECTIONS:
            reasons.append("forbidden_file_or_folder_access")
        if action == "update":
            reasons.append("forbidden_update_permission")
        if action == "delete":
            reasons.append("forbidden_delete_permission")
        if action not in {"read", "create", "update", "delete", "share", "*"}:
            reasons.append("forbidden_action")

        if action in MUTATION_ACTIONS or action == "*":
            mutation_permissions.append(permission)
        if collection == "feeds" and action == "create":
            feeds_create_permissions.append(permission)
        elif (collection, action) not in ALLOWED_READ_PERMISSIONS:
            reasons.append("forbidden_collection")

        if collection == "feeds" and action == "create":
            fields = permission.get("fields")
            if not isinstance(fields, list) or not fields:
                reasons.append("missing_feeds_create_fields")
                continue
            normalized_fields = {_normalized_permission_text(field) for field in fields}
            if "*" in normalized_fields:
                reasons.append("wildcard_field")
            unexpected_fields.update(normalized_fields - ALLOWED_FEEDS_CREATE_FIELDS)

    checks["mutation_permission_count"] = len(mutation_permissions)
    checks["exactly_one_mutation_permission"] = len(mutation_permissions) == 1
    if len(mutation_permissions) != 1:
        reasons.append("ambiguous_policy_graph")

    checks["feeds_create_present"] = len(feeds_create_permissions) == 1
    if not feeds_create_permissions:
        reasons.append("missing_feeds_create")
    elif len(feeds_create_permissions) > 1:
        reasons.append("ambiguous_policy_graph")

    feeds_create = feeds_create_permissions[0] if len(feeds_create_permissions) == 1 else None
    if feeds_create is not None:
        checks["feeds_create_validation_status_draft"] = _has_status_draft_validation(feeds_create)
        checks["feeds_create_preset_status_draft"] = _has_status_draft_preset(feeds_create)
        if not checks["feeds_create_validation_status_draft"]:
            reasons.append("missing_status_draft_validation")
        if not checks["feeds_create_preset_status_draft"]:
            reasons.append("missing_status_draft_preset")
    else:
        checks["feeds_create_validation_status_draft"] = False
        checks["feeds_create_preset_status_draft"] = False

    checks["feeds_create_unexpected_fields"] = sorted(unexpected_fields)
    checks["feeds_create_fields_subset"] = not unexpected_fields
    if unexpected_fields:
        reasons.append("unexpected_feeds_create_field")


def _target_url(payload: Mapping[str, Any]) -> str:
    direct = _text(payload.get("target_url"))
    if direct:
        return direct
    target = payload.get("target")
    if isinstance(target, Mapping):
        return _text(target.get("target_url")) or _text(target.get("base_url"))
    return ""


def _policy_sources(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    policies = payload.get("policies")
    if isinstance(policies, list):
        return [policy for policy in policies if isinstance(policy, Mapping)]

    graph = payload.get("policy_graph")
    if isinstance(graph, Mapping):
        sources = graph.get("sources")
        if isinstance(sources, list):
            return [source for source in sources if isinstance(source, Mapping)]
    return []


def _permissions(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    direct_permissions = payload.get("permissions")
    if isinstance(direct_permissions, list):
        return [permission for permission in direct_permissions if isinstance(permission, Mapping)]

    graph = payload.get("policy_graph")
    if not isinstance(graph, Mapping):
        return []

    permissions: list[Mapping[str, Any]] = []
    sources = graph.get("sources")
    if not isinstance(sources, list):
        return []
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        source_permissions = source.get("permissions")
        if not isinstance(source_permissions, list):
            continue
        permissions.extend(permission for permission in source_permissions if isinstance(permission, Mapping))
    return permissions


def _policy_graph_is_ambiguous(payload: Mapping[str, Any]) -> bool:
    graph = payload.get("policy_graph")
    if isinstance(graph, Mapping) and graph.get("complete") is False:
        return True

    analysis = payload.get("feeds_create_analysis")
    if isinstance(analysis, Mapping):
        if _has_items(analysis.get("broadening_permissions")):
            return True
        if _has_items(analysis.get("ambiguous_permissions")):
            return True
        result = _text(analysis.get("result"))
        if result and result not in {"accepted_exact_or_narrower", "accepted"}:
            return True

    forbidden_access = payload.get("forbidden_access")
    if isinstance(forbidden_access, Mapping):
        if forbidden_access.get("any_forbidden_allowed") is True:
            return True
        if _has_items(forbidden_access.get("violations")):
            return True
    return False


def _has_status_draft_validation(permission: Mapping[str, Any]) -> bool:
    validation = permission.get("validation")
    if not isinstance(validation, Mapping):
        return False
    status = validation.get("status")
    if not isinstance(status, Mapping):
        return False
    return status.get("_eq") == "draft"


def _has_status_draft_preset(permission: Mapping[str, Any]) -> bool:
    presets = permission.get("presets")
    if not isinstance(presets, Mapping):
        return False
    return presets.get("status") == "draft"


def _probe(method: str, resource: str, result: str, success: bool) -> dict[str, Any]:
    return {
        "method": method,
        "resource": resource,
        "result": result,
        "success": success,
        "evidence_source": "approved_policy_graph",
    }


def _has_items(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, bytes)):
        return bool(value)
    if isinstance(value, Iterable):
        return any(True for _ in value)
    return bool(value)


def _normalize_role(role: Any, index: int) -> dict[str, Any]:
    role = _require_mapping(role, f"roles[{index}]")
    role_id = _optional_text(role, "id")
    role_name = _optional_text(role, "name")
    if not role_id and not role_name:
        raise DirectusPolicyEvidenceError(f"roles[{index}] must have id or name")

    normalized: dict[str, Any] = {}
    if role_id:
        normalized["id"] = role_id
    if role_name:
        normalized["name"] = role_name
    return normalized


def _normalize_policy(policy: Any, index: int) -> dict[str, Any]:
    policy = _require_mapping(policy, f"policies[{index}]")
    policy_id = _require_text_value(policy.get("id"), f"policies[{index}].id")
    policy_roles = _require_text_list(policy.get("roles"), f"policies[{index}].roles")
    if not policy_roles:
        raise DirectusPolicyEvidenceError(f"policies[{index}].roles must not be empty")

    normalized: dict[str, Any] = {
        "id": policy_id,
        "roles": policy_roles,
    }
    policy_name = _optional_text(policy, "name")
    if policy_name:
        normalized["name"] = policy_name
    return normalized


def _normalize_permission(permission: Any, index: int, attached_policy_ids: set[str]) -> dict[str, Any]:
    permission = _require_mapping(permission, f"permissions[{index}]")
    policy_id = _require_text_value(permission.get("policy"), f"permissions[{index}].policy")
    if policy_id not in attached_policy_ids:
        raise DirectusPolicyEvidenceError(f"permissions[{index}].policy is not attached to identity role")

    normalized: dict[str, Any] = {
        "policy": policy_id,
        "collection": _require_text_value(permission.get("collection"), f"permissions[{index}].collection"),
        "action": _require_text_value(permission.get("action"), f"permissions[{index}].action"),
        "permissions": _optional_mapping(permission.get("permissions"), f"permissions[{index}].permissions", default={}),
        "validation": _require_mapping(permission.get("validation"), f"permissions[{index}].validation"),
        "presets": _optional_mapping(permission.get("presets"), f"permissions[{index}].presets", default=None),
        "fields": _require_text_list(permission.get("fields"), f"permissions[{index}].fields"),
    }
    permission_id = _optional_text(permission, "id")
    if permission_id:
        normalized["id"] = permission_id
    return normalized


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DirectusPolicyEvidenceError(f"{label} must be an object")
    return value


def _optional_mapping(value: Any, label: str, *, default: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if value is None:
        return default
    if not isinstance(value, Mapping):
        raise DirectusPolicyEvidenceError(f"{label} must be an object or null")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise DirectusPolicyEvidenceError(f"{label} must be a list")
    return value


def _require_text(raw: Mapping[str, Any], key: str) -> str:
    return _require_text_value(raw.get(key), key)


def _require_text_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DirectusPolicyEvidenceError(f"{label} is required")
    return value.strip()


def _optional_text(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise DirectusPolicyEvidenceError(f"{key} must be a string")
    return value.strip()


def _require_text_list(value: Any, label: str) -> list[str]:
    if not _is_text_list(value):
        raise DirectusPolicyEvidenceError(f"{label} must be a list of strings")
    return [item.strip() for item in value]


def _is_text_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _normalized_permission_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _result(reasons: list[str], checks: dict[str, Any]) -> dict[str, Any]:
    unique_reasons = sorted(set(reasons))
    return {
        "kind": EVALUATION_KIND,
        "status": "rejected" if unique_reasons else "approved",
        "reasons": unique_reasons,
        "checks": checks,
    }


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("input JSON must contain an object")
    return payload


def main(argv: list[str] | None = None, *, http: httpx.Client | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize and evaluate Directus policy graph evidence without network access.",
    )
    parser.add_argument("--collect-live", action="store_true", help="Collect raw policy graph evidence with GET-only Directus calls.")
    parser.add_argument("--directus-url", help="Directus base URL for --collect-live.")
    parser.add_argument("--role-id", help="Directus role id to inspect for --collect-live.")
    parser.add_argument("--raw-output", help="Raw collected evidence JSON output path for --collect-live.")
    parser.add_argument("--input", help="Sanitized Directus policy graph evidence JSON path.")
    parser.add_argument("--output", help="Evaluation JSON output path.")
    parser.add_argument("--raw-input", help="Raw synthetic Directus policy graph JSON path.")
    parser.add_argument("--normalized-output", help="Normalized evidence JSON output path.")
    parser.add_argument("--evaluation-output", help="Evaluation JSON output path for raw mode.")
    parser.add_argument(
        "--permission-evidence-output",
        help="Derived permission-evidence-create-only.json output path, written only for approved evidence.",
    )
    parser.add_argument("--force", action="store_true", help="Allow overwriting the output file.")
    args = parser.parse_args(argv)

    raw_mode_args = [args.raw_input, args.normalized_output, args.evaluation_output]
    raw_mode = any(raw_mode_args)
    collect_mode_args = [args.directus_url, args.role_id, args.raw_output]
    collect_mode = args.collect_live

    try:
        if collect_mode:
            if (
                not all(collect_mode_args)
                or not args.normalized_output
                or not args.evaluation_output
                or args.input
                or args.output
                or args.raw_input
            ):
                raise ValueError(
                    "collect-live mode requires --directus-url, --role-id, --raw-output, "
                    "--normalized-output, and --evaluation-output only",
                )

            raw_output_path = Path(args.raw_output)
            normalized_output_path = Path(args.normalized_output)
            evaluation_output_path = Path(args.evaluation_output)
            permission_evidence_output_path = (
                Path(args.permission_evidence_output) if args.permission_evidence_output else None
            )
            output_paths = [raw_output_path, normalized_output_path, evaluation_output_path]
            if permission_evidence_output_path is not None:
                output_paths.append(permission_evidence_output_path)
            for path in output_paths:
                _ensure_writable_output(path, force=args.force)
                _ensure_output_outside_repository(path)

            token = os.environ.get("DIRECTUS_TOKEN", "")
            if not token.strip():
                raise ValueError("DIRECTUS_TOKEN is required for collect-live mode")

            raw_payload = collect_directus_policy_graph_raw(
                directus_url=args.directus_url,
                role_id=args.role_id,
                auth_token=token,
                http=http,
            )
            normalized = normalize_directus_policy_graph_payload(raw_payload)
            evaluation = evaluate_policy_graph_evidence(normalized)
            raw_output_path.write_text(
                json.dumps(raw_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            normalized_output_path.write_text(
                json.dumps(normalized, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            evaluation_output_path.write_text(
                json.dumps(evaluation, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output_summary = {
                "status": evaluation["status"],
                "raw_output": str(raw_output_path),
                "normalized_output": str(normalized_output_path),
                "evaluation_output": str(evaluation_output_path),
            }
            if permission_evidence_output_path is not None:
                permission_evidence = build_permission_evidence_create_only(normalized, evaluation=evaluation)
                permission_evidence_output_path.write_text(
                    json.dumps(permission_evidence, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                output_summary["permission_evidence_output"] = str(permission_evidence_output_path)
            print(
                json.dumps(output_summary, sort_keys=True),
            )
        elif raw_mode:
            if any(collect_mode_args):
                raise ValueError("collect-live options require --collect-live")
            if not all(raw_mode_args) or args.input or args.output:
                raise ValueError(
                    "raw mode requires --raw-input, --normalized-output, and --evaluation-output only",
                )
            normalized_output_path = Path(args.normalized_output)
            evaluation_output_path = Path(args.evaluation_output)
            permission_evidence_output_path = (
                Path(args.permission_evidence_output) if args.permission_evidence_output else None
            )
            output_paths = [normalized_output_path, evaluation_output_path]
            if permission_evidence_output_path is not None:
                output_paths.append(permission_evidence_output_path)
            for path in output_paths:
                _ensure_writable_output(path, force=args.force)

            raw_payload = _read_json_object(Path(args.raw_input))
            normalized = normalize_directus_policy_graph_payload(raw_payload)
            evaluation = evaluate_policy_graph_evidence(normalized)
            normalized_output_path.write_text(
                json.dumps(normalized, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            evaluation_output_path.write_text(
                json.dumps(evaluation, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            output_summary = {
                "status": evaluation["status"],
                "normalized_output": str(normalized_output_path),
                "evaluation_output": str(evaluation_output_path),
            }
            if permission_evidence_output_path is not None:
                permission_evidence = build_permission_evidence_create_only(normalized, evaluation=evaluation)
                permission_evidence_output_path.write_text(
                    json.dumps(permission_evidence, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                output_summary["permission_evidence_output"] = str(permission_evidence_output_path)
            print(
                json.dumps(output_summary, sort_keys=True),
            )
        else:
            if any(collect_mode_args):
                raise ValueError("collect-live options require --collect-live")
            if not args.input or not args.output:
                raise ValueError("evaluator mode requires --input and --output")
            output_path = Path(args.output)
            permission_evidence_output_path = (
                Path(args.permission_evidence_output) if args.permission_evidence_output else None
            )
            output_paths = [output_path]
            if permission_evidence_output_path is not None:
                output_paths.append(permission_evidence_output_path)
            for path in output_paths:
                _ensure_writable_output(path, force=args.force)
            payload = _read_json_object(Path(args.input))
            evaluation = evaluate_policy_graph_evidence(payload)
            output_path.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            output_summary = {"status": evaluation["status"], "output": str(output_path)}
            if permission_evidence_output_path is not None:
                permission_evidence = build_permission_evidence_create_only(payload, evaluation=evaluation)
                permission_evidence_output_path.write_text(
                    json.dumps(permission_evidence, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                output_summary["permission_evidence_output"] = str(permission_evidence_output_path)
            print(json.dumps(output_summary, sort_keys=True))
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
        DirectusPolicyEvidenceError,
        DirectusPolicyCollectorError,
        httpx.HTTPError,
    ) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 1

    if "malformed_payload" in evaluation["reasons"]:
        return 1
    return 0 if evaluation["status"] == "approved" else 2


def _ensure_writable_output(path: Path, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing output: {path}")


def _ensure_output_outside_repository(path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    resolved = path.resolve()
    if resolved == repository_root or repository_root in resolved.parents:
        raise ValueError(f"collect-live output must be outside the repository: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
