"""Read-only Directus policy graph collector scaffold.

The collector is intentionally narrow: it performs GET-only inspection calls
and returns the conservative raw shape accepted by
``normalize_directus_policy_graph_payload``. Production use remains gated by
the migration runbook; tests inject an ``httpx.Client`` with ``MockTransport``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, urlparse

import httpx


DEFAULT_USER_AGENT = "cap-wordpress-migration/1.0"


class DirectusPolicyCollectorError(ValueError):
    """Raised when live policy graph collection cannot be proven safe."""


def collect_directus_policy_graph_raw(
    *,
    directus_url: str,
    role_id: str,
    auth_token: str,
    http: httpx.Client | None = None,
) -> dict[str, Any]:
    """Collect a raw Directus policy graph using GET-only requests."""

    base_url = _normalize_directus_url(directus_url)
    selected_role_id = _require_text(role_id, "role_id")
    token = _require_text(auth_token, "auth_token")
    headers = {"Authorization": f"Bearer {token}", "User-Agent": DEFAULT_USER_AGENT}

    owns_client = http is None
    client = http or httpx.Client(timeout=30, follow_redirects=False)
    try:
        server_info = _get_data(client, base_url, "/server/info", headers=headers, label="server info")
        role = _get_data(client, base_url, f"/roles/{quote(selected_role_id, safe='')}", headers=headers, label="role")
        policies = _get_data(
            client,
            base_url,
            "/policies",
            headers=headers,
            params={
                "filter[roles][role][_eq]": selected_role_id,
                "fields": "id,name,roles.role.*",
            },
            label="policies",
        )
        policies = _require_non_empty_list(policies, "policies response")
        policy_ids = [_require_item_id(policy, f"policies[{index}]") for index, policy in enumerate(policies)]
        permissions = _get_data(
            client,
            base_url,
            "/permissions",
            headers=headers,
            params={"filter[policy][_in]": ",".join(policy_ids)},
            label="permissions",
        )
        permissions = _require_non_empty_list(permissions, "permissions response")
    finally:
        if owns_client:
            client.close()

    normalized_role = _raw_role(role, selected_role_id)
    return {
        "target_url": base_url,
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "directus_version": _directus_version(server_info),
        "identity": {
            "label": normalized_role.get("name") or selected_role_id,
            "role": selected_role_id,
        },
        "roles": [normalized_role],
        "policies": [_raw_policy(policy, selected_role_id, index) for index, policy in enumerate(policies)],
        "permissions": [_raw_permission(permission, index) for index, permission in enumerate(permissions)],
    }


def _normalize_directus_url(value: str) -> str:
    value = _require_text(value, "directus_url").rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DirectusPolicyCollectorError("directus_url must be an absolute http or https URL")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DirectusPolicyCollectorError(f"{label} is required")
    return value.strip()


def _get_data(
    client: httpx.Client,
    base_url: str,
    path: str,
    *,
    headers: dict[str, str],
    label: str,
    params: dict[str, str] | None = None,
) -> Any:
    response = client.get(f"{base_url}{path}", headers=headers, params=params)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise DirectusPolicyCollectorError(f"{label} GET failed with status {response.status_code}") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise DirectusPolicyCollectorError(f"{label} response is not JSON") from exc

    if not isinstance(payload, dict) or "data" not in payload:
        raise DirectusPolicyCollectorError(f"{label} response must contain data")
    if payload["data"] in (None, []):
        raise DirectusPolicyCollectorError(f"{label} response is empty")
    return payload["data"]


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DirectusPolicyCollectorError(f"{label} must be an object")
    return value


def _require_non_empty_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise DirectusPolicyCollectorError(f"{label} must be a non-empty list")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        result.append(_require_mapping(item, f"{label}[{index}]"))
    return result


def _require_item_id(item: dict[str, Any], label: str) -> str:
    return _require_text(item.get("id"), f"{label}.id")


def _optional_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _directus_version(server_info: Any) -> str:
    data = _require_mapping(server_info, "server info")
    directus = data.get("directus")
    if isinstance(directus, dict):
        version = _optional_text(directus.get("version"))
        if version:
            return version
    return _optional_text(data.get("version"))


def _raw_role(role: Any, selected_role_id: str) -> dict[str, Any]:
    role = _require_mapping(role, "role response")
    role_id = _optional_text(role.get("id")) or selected_role_id
    if role_id != selected_role_id:
        raise DirectusPolicyCollectorError("role response id does not match requested role_id")
    normalized = {"id": role_id}
    role_name = _optional_text(role.get("name"))
    if role_name:
        normalized["name"] = role_name
    return normalized


def _raw_policy(policy: dict[str, Any], selected_role_id: str, index: int) -> dict[str, Any]:
    policy_id = _require_item_id(policy, f"policies[{index}]")
    roles = _policy_role_ids(policy.get("roles"))
    if selected_role_id not in roles:
        raise DirectusPolicyCollectorError(f"policies[{index}] is not attached to requested role")

    normalized: dict[str, Any] = {
        "id": policy_id,
        "roles": roles,
    }
    policy_name = _optional_text(policy.get("name"))
    if policy_name:
        normalized["name"] = policy_name
    return normalized


def _policy_role_ids(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise DirectusPolicyCollectorError("policy roles must be a non-empty list")

    role_ids: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            role_ids.append(item.strip())
        elif isinstance(item, dict):
            role = item.get("role")
            if isinstance(role, str) and role.strip():
                role_ids.append(role.strip())
            elif isinstance(role, dict) and isinstance(role.get("id"), str) and role["id"].strip():
                role_ids.append(role["id"].strip())
            else:
                raise DirectusPolicyCollectorError("policy role linkage is malformed")
        else:
            raise DirectusPolicyCollectorError("policy role linkage is malformed")
    return role_ids


def _raw_permission(permission: dict[str, Any], index: int) -> dict[str, Any]:
    policy_id = _permission_policy_id(permission.get("policy"))
    normalized: dict[str, Any] = {
        "policy": policy_id,
        "collection": _require_text(permission.get("collection"), f"permissions[{index}].collection"),
        "action": _require_text(permission.get("action"), f"permissions[{index}].action"),
        "permissions": _mapping_or_empty(permission.get("permissions"), f"permissions[{index}].permissions"),
        "validation": _mapping_or_empty(permission.get("validation"), f"permissions[{index}].validation"),
        "presets": _mapping_or_none(permission.get("presets"), f"permissions[{index}].presets"),
        "fields": _fields(permission.get("fields"), f"permissions[{index}].fields"),
    }
    permission_id = _optional_text(permission.get("id"))
    if permission_id:
        normalized["id"] = permission_id
    return normalized


def _permission_policy_id(value: Any) -> str:
    if isinstance(value, str):
        return _require_text(value, "permission.policy")
    if isinstance(value, dict):
        return _require_text(value.get("id"), "permission.policy.id")
    raise DirectusPolicyCollectorError("permission.policy is required")


def _mapping_or_empty(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DirectusPolicyCollectorError(f"{label} must be an object or null")
    return value


def _mapping_or_none(value: Any, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DirectusPolicyCollectorError(f"{label} must be an object or null")
    return value


def _fields(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise DirectusPolicyCollectorError(f"{label} must be a non-empty list of strings")
    return [item.strip() for item in value]
