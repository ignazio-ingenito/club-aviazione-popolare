"""Fail-closed pre-create gate validation for approved migration execution."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any


PERMISSION_GATE_KIND = "permission_evidence_create_only"
FRESH_TARGET_ABSENCE_GATE_KIND = "fresh_target_absence_before_create"

PERMISSION_REQUIRED_PROBES: Mapping[str, tuple[str, str, str]] = {
    "create": ("POST", "/items/feeds", "allowed"),
    "patch": ("PATCH", "/items/feeds", "denied"),
    "put": ("PUT", "/items/feeds", "denied"),
    "delete": ("DELETE", "/items/feeds", "denied"),
    "schema": ("GET", "/schema", "denied"),
    "settings": ("GET", "/settings", "denied"),
    "users": ("GET", "/users", "denied"),
    "roles": ("GET", "/roles", "denied"),
    "permissions": ("GET", "/permissions", "denied"),
}
PERMISSION_OPTIONAL_FORBIDDEN_PROBES: Mapping[str, tuple[str, str, str]] = {
    "policies": ("GET", "/policies", "denied"),
}
FORBIDDEN_CAPABILITY_FLAGS = frozenset(
    {
        "admin",
        "system_wildcard",
        "wildcard",
        "broad_token",
        "broad_token_admin_indicator",
        "role_admin",
        "permission_management",
    }
)


class PreCreateGateError(ValueError):
    """Raised when a pre-create gate report is missing, malformed, or unsafe."""


def validate_permission_evidence_report(
    report: Mapping[str, Any],
    *,
    expected_target_url: str,
) -> None:
    """Validate the create-only permission report required by execute mode."""

    payload = _require_mapping(report, "permission evidence report")
    _require_exact(payload.get("kind"), PERMISSION_GATE_KIND, "permission evidence kind")
    _require_exact(payload.get("status"), "approved", "permission evidence status")
    _require_exact(payload.get("target_url"), expected_target_url, "permission evidence target_url")
    _require_non_empty_text(payload.get("observed_at"), "permission evidence observed_at")
    _validate_execution_identity(payload.get("execution_identity"))
    _reject_successful_forbidden_capabilities(payload)

    probes = _require_mapping(payload.get("probes"), "permission evidence probes")
    for name, (method, resource, result) in PERMISSION_REQUIRED_PROBES.items():
        _validate_probe(
            probes.get(name),
            name=name,
            expected_method=method,
            expected_resource=resource,
            expected_result=result,
        )

    for name, (method, resource, result) in PERMISSION_OPTIONAL_FORBIDDEN_PROBES.items():
        if name in probes:
            _validate_probe(
                probes.get(name),
                name=name,
                expected_method=method,
                expected_resource=resource,
                expected_result=result,
            )

    for name, raw_probe in probes.items():
        if name in PERMISSION_REQUIRED_PROBES or name in PERMISSION_OPTIONAL_FORBIDDEN_PROBES:
            continue
        probe = _require_mapping(raw_probe, f"permission evidence probe {name}")
        if _normalized_result(probe) == "allowed":
            raise PreCreateGateError(f"Unexpected successful permission probe: {name}.")
        if _normalized_result(probe) in {"skipped", "ambiguous", "inconclusive", "unknown"}:
            raise PreCreateGateError(f"Unexpected inconclusive permission probe: {name}.")


def validate_fresh_target_absence_report(
    report: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    expected_target_url: str,
    expected_manifest_sha256: str,
    expected_approval_sha256: str,
    expected_operation_count: int,
) -> None:
    """Validate the fresh target absence report required by execute mode."""

    payload = _require_mapping(report, "fresh target absence report")
    _require_exact(payload.get("kind"), FRESH_TARGET_ABSENCE_GATE_KIND, "fresh target absence kind")
    _require_exact(payload.get("status"), "approved", "fresh target absence status")
    _require_exact(payload.get("target_url"), expected_target_url, "fresh target absence target_url")
    _require_non_empty_text(payload.get("observed_at"), "fresh target absence observed_at")
    _require_non_empty_text(payload.get("target_baseline_sha256"), "fresh target absence target_baseline_sha256")
    _require_exact(
        payload.get("manifest_sha256"),
        expected_manifest_sha256,
        "fresh target absence manifest_sha256",
    )
    _require_exact(
        payload.get("approval_sha256"),
        expected_approval_sha256,
        "fresh target absence approval_sha256",
    )
    _require_exact(
        payload.get("checked_operation_count"),
        expected_operation_count,
        "fresh target absence checked_operation_count",
    )
    if payload.get("stale_baseline") is True:
        raise PreCreateGateError("Fresh target absence report has stale_baseline=true.")

    manifest_original_uris = _manifest_original_uri_set(manifest)
    checked_original_uris = _text_set(payload.get("checked_original_uris"), "checked_original_uris")
    if checked_original_uris != manifest_original_uris:
        raise PreCreateGateError("Checked original_uri set does not exactly match the manifest.")

    absence_evidence = _require_mapping(payload.get("absence_evidence"), "absence_evidence")
    evidence_uris = set(absence_evidence)
    if evidence_uris != manifest_original_uris:
        raise PreCreateGateError("Absence evidence keys do not exactly match the manifest original_uri set.")
    for original_uri, raw_evidence in absence_evidence.items():
        evidence = _require_mapping(raw_evidence, f"absence_evidence[{original_uri}]")
        _require_exact(evidence.get("status"), "absent", f"absence_evidence[{original_uri}].status")
        if evidence.get("checked") is not True:
            raise PreCreateGateError(f"Absence evidence for {original_uri} was not explicitly checked.")
        if evidence.get("existing_target_match") is True:
            raise PreCreateGateError(f"Existing target match found for {original_uri}.")
        for match_key in ("matches", "target_matches", "collisions"):
            if _has_items(evidence.get(match_key)):
                raise PreCreateGateError(f"Absence evidence for {original_uri} contains {match_key}.")

    for list_name in (
        "route_collisions",
        "slug_collisions",
        "protected_collisions",
        "drift_protected_collisions",
        "ambiguous_matches",
        "skipped_checks",
    ):
        if _has_items(payload.get(list_name)):
            raise PreCreateGateError(f"Fresh target absence report contains {list_name}.")


def _manifest_original_uri_set(manifest: Mapping[str, Any]) -> set[str]:
    operations = manifest.get("operations")
    if not isinstance(operations, list):
        raise PreCreateGateError("Manifest operations must be a list for target absence validation.")
    original_uris: list[str] = []
    for index, operation in enumerate(operations):
        if not isinstance(operation, Mapping):
            raise PreCreateGateError(f"Manifest operation {index} is not an object.")
        original_uris.append(_require_non_empty_text(operation.get("original_uri"), f"operations[{index}].original_uri"))
    duplicates = sorted(uri for uri, count in Counter(original_uris).items() if count > 1)
    if duplicates:
        raise PreCreateGateError(f"Manifest contains duplicate original_uri values: {duplicates!r}.")
    return set(original_uris)


def _validate_execution_identity(value: Any) -> None:
    identity = _require_mapping(value, "execution_identity")
    identifier = _require_non_empty_text(identity.get("id"), "execution_identity.id")
    if "token" in identity or "password" in identity or "secret" in identity:
        raise PreCreateGateError("Execution identity must not contain credentials.")
    if identifier.lower() in {"admin", "administrator", "root"}:
        raise PreCreateGateError("Execution identity cannot be an admin identity.")
    if identity.get("is_admin") is True or identity.get("admin") is True:
        raise PreCreateGateError("Execution identity reports admin capability.")


def _validate_probe(
    value: Any,
    *,
    name: str,
    expected_method: str,
    expected_resource: str,
    expected_result: str,
) -> None:
    probe = _require_mapping(value, f"permission evidence probe {name}")
    _require_exact(_upper_text(probe.get("method"), f"probe {name}.method"), expected_method, f"probe {name}.method")
    _require_exact(probe.get("resource"), expected_resource, f"probe {name}.resource")
    result = _normalized_result(probe)
    if result in {"skipped", "ambiguous", "inconclusive", "unknown"}:
        raise PreCreateGateError(f"Permission probe {name} is not conclusive.")
    _require_exact(result, expected_result, f"probe {name}.result")
    if expected_result == "denied" and probe.get("success") is True:
        raise PreCreateGateError(f"Forbidden permission probe {name} reports success.")
    if expected_result == "allowed" and probe.get("success") is False:
        raise PreCreateGateError(f"Create permission probe {name} reports failure.")


def _reject_successful_forbidden_capabilities(payload: Mapping[str, Any]) -> None:
    capabilities = payload.get("capabilities", {})
    if capabilities is not None:
        capability_map = _require_mapping(capabilities, "permission evidence capabilities")
        for key, value in capability_map.items():
            normalized_key = key.lower().replace("-", "_")
            if normalized_key in FORBIDDEN_CAPABILITY_FLAGS and value is True:
                raise PreCreateGateError(f"Forbidden capability is present: {key}.")
    for key, value in payload.items():
        normalized_key = key.lower().replace("-", "_") if isinstance(key, str) else ""
        if normalized_key in FORBIDDEN_CAPABILITY_FLAGS and value is True:
            raise PreCreateGateError(f"Forbidden capability is present: {key}.")


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PreCreateGateError(f"{field_name} must be an object.")
    return value


def _require_non_empty_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PreCreateGateError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _upper_text(value: Any, field_name: str) -> str:
    return _require_non_empty_text(value, field_name).upper()


def _require_exact(value: Any, expected: Any, field_name: str) -> None:
    if value != expected:
        raise PreCreateGateError(f"{field_name} mismatch: expected {expected!r}, got {value!r}.")


def _normalized_result(probe: Mapping[str, Any]) -> str:
    result = probe.get("result")
    if result is None:
        result = probe.get("outcome")
    if result is None:
        result = "allowed" if probe.get("allowed") is True else "denied" if probe.get("denied") is True else None
    return str(result).strip().lower() if result is not None else "unknown"


def _text_set(value: Any, field_name: str) -> set[str]:
    if not isinstance(value, list):
        raise PreCreateGateError(f"{field_name} must be a list.")
    result: set[str] = set()
    for index, item in enumerate(value):
        result.add(_require_non_empty_text(item, f"{field_name}[{index}]"))
    if len(result) != len(value):
        raise PreCreateGateError(f"{field_name} contains duplicate values.")
    return result


def _has_items(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return len(value) > 0
    return bool(value)
