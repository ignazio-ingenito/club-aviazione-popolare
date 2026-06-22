"""Pure Directus policy graph evidence evaluator for migration gates.

This module intentionally performs no network access and accepts only already
sanitized evidence artifacts. It evaluates whether the effective Directus policy
graph is narrow enough for the current draft-only WordPress migration stage.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any


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


def _has_items(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, bytes)):
        return bool(value)
    if isinstance(value, Iterable):
        return any(True for _ in value)
    return bool(value)


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate sanitized Directus policy graph evidence without network access.",
    )
    parser.add_argument("--input", required=True, help="Sanitized Directus policy graph evidence JSON path.")
    parser.add_argument("--output", required=True, help="Evaluation JSON output path.")
    parser.add_argument("--force", action="store_true", help="Allow overwriting the output file.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    try:
        if output_path.exists() and not args.force:
            raise FileExistsError(f"Refusing to overwrite existing output: {output_path}")
        payload = _read_json_object(input_path)
        evaluation = evaluate_policy_graph_evidence(payload)
        output_path.write_text(json.dumps(evaluation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 1

    print(json.dumps({"status": evaluation["status"], "output": str(output_path)}, sort_keys=True))
    if "malformed_payload" in evaluation["reasons"]:
        return 1
    return 0 if evaluation["status"] == "approved" else 2


if __name__ == "__main__":
    raise SystemExit(main())
