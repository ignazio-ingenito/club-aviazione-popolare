"""Fail-closed token recovery helper for the gallery-media migration identity.

The helper is intentionally limited to the existing
``cap-gallery-media-migration@skunklabs.uk`` service user. Normal execution is
GET-only. Token regeneration requires an explicit environment gate and performs
only ``PATCH /users/<id>`` after discovery proves exactly one matching user.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import secrets
from typing import Any
from urllib.parse import urlparse

import httpx


DEFAULT_DIRECTUS_URL = "https://cap-cms.skunklabs.uk"
DEFAULT_USER_AGENT = "cap-wordpress-migration/1.0"
GALLERY_MEDIA_EMAIL = "cap-gallery-media-migration@skunklabs.uk"
GALLERY_MEDIA_IDENTITY = "directus-createonly-gallery-media-migration"
APPLY_GATE = "APPLY_DIRECTUS_GALLERY_MEDIA_TOKEN_REGEN"
ADMIN_TOKEN_ENV = "DIRECTUS_ADMIN_TOKEN"
PROBE_TOKEN_ENV = "DIRECTUS_GALLERY_MEDIA_TOKEN"
EXPECTED_PERMISSIONS = frozenset(
    {
        "feeds.read",
        "directus_folders.read",
        "directus_folders.create",
        "directus_files.read",
        "directus_files.create",
    }
)


class GalleryMediaTokenRecoveryError(ValueError):
    """Raised when token recovery cannot be proven safe."""


def discover_gallery_media_identity(
    *,
    directus_url: str,
    admin_token: str,
    http: httpx.Client | None = None,
) -> dict[str, Any]:
    base_url = _normalize_url(directus_url)
    headers = _headers(admin_token)
    owns_client = http is None
    client = http or httpx.Client(timeout=30, follow_redirects=False)
    try:
        server_info = _get_data(client, base_url, "/server/info", headers=headers, label="server info")
        users = _get_data(
            client,
            base_url,
            "/users",
            headers=headers,
            params={
                "filter[email][_eq]": GALLERY_MEDIA_EMAIL,
                "fields": "id,email,status,role",
            },
            label="gallery-media user",
        )
        users = _require_list(users, "gallery-media user")
        if len(users) != 1:
            raise GalleryMediaTokenRecoveryError(
                f"Expected exactly one gallery-media service user, found {len(users)}."
            )
        user = _require_mapping(users[0], "gallery-media user[0]")
        user_id = _require_text(user.get("id"), "gallery-media user id")

        policies = _get_data(
            client,
            base_url,
            "/policies",
            headers=headers,
            params={
                "filter[name][_eq]": GALLERY_MEDIA_IDENTITY,
                "fields": "id,name,roles.role.*",
            },
            label="gallery-media policy",
        )
        policies = _require_list(policies, "gallery-media policy")
        if len(policies) != 1:
            raise GalleryMediaTokenRecoveryError(
                f"Expected exactly one gallery-media policy, found {len(policies)}."
            )
        policy = _require_mapping(policies[0], "gallery-media policy[0]")
        policy_id = _require_text(policy.get("id"), "gallery-media policy id")
        permissions = _get_data(
            client,
            base_url,
            "/permissions",
            headers=headers,
            params={
                "filter[policy][_eq]": policy_id,
                "fields": "collection,action",
            },
            label="gallery-media permissions",
        )
        permissions = _require_list(permissions, "gallery-media permissions")
    finally:
        if owns_client:
            client.close()

    observed_permissions = _permission_keys(permissions)
    unexpected = sorted(observed_permissions - EXPECTED_PERMISSIONS)
    missing = sorted(EXPECTED_PERMISSIONS - observed_permissions)
    status = "ready_for_token_recovery" if not unexpected and not missing else "blocked"
    return {
        "status": status,
        "identity_name": GALLERY_MEDIA_IDENTITY,
        "service_email": GALLERY_MEDIA_EMAIL,
        "target_url": base_url,
        "observed_at": _utc_now(),
        "directus_version": _directus_version(server_info),
        "user": {
            "exists": True,
            "id_redacted": _redacted_id(user_id),
            "status": _optional_text(user.get("status")),
        },
        "policy": {
            "exists": True,
            "id_redacted": _redacted_id(policy_id),
        },
        "permissions": {
            "expected": sorted(EXPECTED_PERMISSIONS),
            "observed": sorted(observed_permissions),
            "missing": missing,
            "unexpected": unexpected,
        },
        "live_methods_used": ["GET"],
        "token_in_report": False,
    }


def regenerate_gallery_media_token(
    *,
    directus_url: str,
    admin_token: str,
    http: httpx.Client | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    if os.environ.get(APPLY_GATE) != "true":
        raise GalleryMediaTokenRecoveryError(f"{APPLY_GATE}=true is required for token regeneration.")

    base_url = _normalize_url(directus_url)
    headers = _headers(admin_token)
    owns_client = http is None
    client = http or httpx.Client(timeout=30, follow_redirects=False)
    try:
        discovery = discover_gallery_media_identity(
            directus_url=base_url,
            admin_token=admin_token,
            http=client,
        )
        if discovery["status"] != "ready_for_token_recovery":
            raise GalleryMediaTokenRecoveryError("Gallery-media identity is not ready for token recovery.")

        users = _get_data(
            client,
            base_url,
            "/users",
            headers=headers,
            params={"filter[email][_eq]": GALLERY_MEDIA_EMAIL, "fields": "id,email"},
            label="gallery-media user",
        )
        user = _require_mapping(_require_single(users, "gallery-media user"), "gallery-media user[0]")
        user_id = _require_text(user.get("id"), "gallery-media user id")
        new_token = token or secrets.token_urlsafe(48)
        if not new_token.strip():
            raise GalleryMediaTokenRecoveryError("Generated token is empty.")

        response = client.patch(
            f"{base_url}/users/{user_id}",
            headers=headers,
            json={"token": new_token},
        )
        if response.status_code not in {200, 204}:
            raise GalleryMediaTokenRecoveryError(
                f"Token regeneration PATCH failed with status {response.status_code}."
            )
    finally:
        if owns_client:
            client.close()

    return {
        "status": "token_regenerated",
        "identity_name": GALLERY_MEDIA_IDENTITY,
        "service_email": GALLERY_MEDIA_EMAIL,
        "target_url": base_url,
        "observed_at": _utc_now(),
        "patched_endpoint": "/users/<redacted>",
        "methods_used": ["GET", "PATCH"],
        "content_mutations": "none",
        "permission_mutations": "none",
        "token_in_report": False,
        "plaintext_token": new_token,
    }


def probe_gallery_media_token(
    *,
    directus_url: str,
    gallery_media_token: str,
    http: httpx.Client | None = None,
) -> dict[str, Any]:
    base_url = _normalize_url(directus_url)
    headers = _headers(gallery_media_token)
    probes = {
        "server_info": ("/server/info", None),
        "feeds_gallery_read": ("/items/feeds", {"limit": "1", "filter[gallery][_eq]": "true"}),
        "folders_read": ("/folders", {"limit": "1"}),
        "files_read": ("/files", {"limit": "1"}),
        "permissions_read_forbidden": ("/permissions", {"limit": "1"}),
        "users_read_forbidden": ("/users", {"limit": "1"}),
    }
    owns_client = http is None
    client = http or httpx.Client(timeout=30, follow_redirects=False)
    try:
        results = {}
        for label, (path, params) in probes.items():
            response = client.get(f"{base_url}{path}", headers=headers, params=params)
            results[label] = {
                "status": response.status_code,
                "allowed": 200 <= response.status_code < 300,
            }
    finally:
        if owns_client:
            client.close()

    expected_allowed = {"server_info", "feeds_gallery_read", "folders_read", "files_read"}
    expected_forbidden = {"permissions_read_forbidden", "users_read_forbidden"}
    status = "approved"
    if any(not results[label]["allowed"] for label in expected_allowed):
        status = "rejected"
    if any(results[label]["allowed"] for label in expected_forbidden):
        status = "rejected"
    return {
        "status": status,
        "identity_name": GALLERY_MEDIA_IDENTITY,
        "service_email": GALLERY_MEDIA_EMAIL,
        "target_url": base_url,
        "observed_at": _utc_now(),
        "probes": results,
        "live_methods_used": ["GET"],
        "token_in_report": False,
    }


def write_reports(output_dir: Path, reports: dict[str, dict[str, Any]]) -> None:
    _ensure_outside_repo(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, report in reports.items():
        sanitized = dict(report)
        sanitized.pop("plaintext_token", None)
        path = output_dir / name
        if path.exists():
            raise GalleryMediaTokenRecoveryError(f"Refusing to overwrite existing report: {path}")
        path.write_text(json.dumps(sanitized, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None, *, http: httpx.Client | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directus-url", default=DEFAULT_DIRECTUS_URL)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--apply-token-regen", action="store_true")
    parser.add_argument("--probe-token", action="store_true")
    args = parser.parse_args(argv)

    try:
        output_dir = Path(args.output_dir)
        _ensure_outside_repo(output_dir)
        admin_token = _require_text(os.environ.get(ADMIN_TOKEN_ENV), ADMIN_TOKEN_ENV)
        reports = {
            "gallery-media-token-recovery.discovery.json": discover_gallery_media_identity(
                directus_url=args.directus_url,
                admin_token=admin_token,
                http=http,
            )
        }
        if args.apply_token_regen:
            apply_report = regenerate_gallery_media_token(
                directus_url=args.directus_url,
                admin_token=admin_token,
                http=http,
            )
            reports["gallery-media-token-recovery.apply.json"] = apply_report
            print(f"PLAINTEXT_GALLERY_MEDIA_TOKEN={apply_report['plaintext_token']}")
        if args.probe_token:
            probe_token = _require_text(os.environ.get(PROBE_TOKEN_ENV), PROBE_TOKEN_ENV)
            reports["gallery-media-token-recovery.probes.json"] = probe_gallery_media_token(
                directus_url=args.directus_url,
                gallery_media_token=probe_token,
                http=http,
            )
        write_reports(output_dir, reports)
    except GalleryMediaTokenRecoveryError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_require_text(token, 'token')}", "User-Agent": DEFAULT_USER_AGENT}


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
    if response.status_code != 200:
        raise GalleryMediaTokenRecoveryError(f"{label} GET failed with status {response.status_code}.")
    try:
        payload = response.json()
    except ValueError as exc:
        raise GalleryMediaTokenRecoveryError(f"{label} response is not JSON.") from exc
    if not isinstance(payload, dict) or "data" not in payload:
        raise GalleryMediaTokenRecoveryError(f"{label} response must contain data.")
    return payload["data"]


def _normalize_url(value: str) -> str:
    normalized = _require_text(value, "directus_url").rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise GalleryMediaTokenRecoveryError("directus_url must be an absolute HTTP(S) URL.")
    return normalized


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GalleryMediaTokenRecoveryError(f"{label} is required.")
    return value.strip()


def _optional_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GalleryMediaTokenRecoveryError(f"{label} must be an object.")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GalleryMediaTokenRecoveryError(f"{label} must be a list.")
    return value


def _require_single(value: Any, label: str) -> Any:
    values = _require_list(value, label)
    if len(values) != 1:
        raise GalleryMediaTokenRecoveryError(f"Expected exactly one {label}, found {len(values)}.")
    return values[0]


def _permission_keys(permissions: list[Any]) -> set[str]:
    keys = set()
    for index, raw in enumerate(permissions):
        permission = _require_mapping(raw, f"permissions[{index}]")
        collection = _require_text(permission.get("collection"), f"permissions[{index}].collection")
        action = _require_text(permission.get("action"), f"permissions[{index}].action")
        keys.add(f"{collection}.{action}")
    return keys


def _directus_version(server_info: Any) -> str:
    info = _require_mapping(server_info, "server info")
    directus = info.get("directus")
    if isinstance(directus, dict):
        return _optional_text(directus.get("version"))
    return _optional_text(info.get("version"))


def _redacted_id(value: str) -> str:
    if len(value) <= 8:
        return "<redacted>"
    return f"{value[:4]}...{value[-4:]}"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _ensure_outside_repo(path: Path) -> None:
    resolved = path.resolve()
    repo_root = Path(__file__).resolve().parents[3]
    if resolved == repo_root or repo_root in resolved.parents:
        raise GalleryMediaTokenRecoveryError("Output directory must be outside the repository.")


if __name__ == "__main__":
    raise SystemExit(main())
