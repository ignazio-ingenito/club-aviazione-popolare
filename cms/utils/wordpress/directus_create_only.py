"""Create-only Directus client for approved migration writes.

This module is intentionally separate from the legacy mutable Directus helper.
It allows only GET, HEAD, and POST, and it rejects POST requests that are not
targeted at configured create endpoints.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx


CREATE_ONLY_METHODS = frozenset({"GET", "HEAD", "POST"})
DEFAULT_USER_AGENT = "cap-wordpress-migration/1.0"


class DirectusCreateOnlyError(RuntimeError):
    """Base error for the create-only Directus client."""


class DirectusCreateOnlyMethodError(ValueError):
    """Raised before transport use when a non-create HTTP method is requested."""


class DirectusCreateOnlyEndpointError(DirectusCreateOnlyError):
    """Raised when a POST targets an endpoint that is not explicitly allowed."""


def _require_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty.")
    return normalized


def _require_absolute_http_url(value: str, field_name: str) -> str:
    normalized = _require_text(value, field_name).rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be an absolute HTTP(S) URL.")
    return normalized


@dataclass(frozen=True, slots=True)
class DirectusCreateOnlyConfig:
    base_url: str = "https://cap-cms.skunklabs.uk"
    allowed_item_collections: tuple[str, ...] = ()
    allow_files: bool = True
    allow_folders: bool = True
    auth_token: str | None = None
    user_agent: str = DEFAULT_USER_AGENT

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_url", _require_absolute_http_url(self.base_url, "base_url"))
        collections = tuple(_require_text(collection, "allowed_item_collections") for collection in self.allowed_item_collections)
        object.__setattr__(self, "allowed_item_collections", collections)
        object.__setattr__(self, "user_agent", _require_text(self.user_agent, "user_agent"))
        if self.auth_token is not None:
            token = self.auth_token.strip()
            if not token:
                raise ValueError("auth_token cannot be empty when provided.")
            object.__setattr__(self, "auth_token", token)


class DirectusCreateOnlyClient:
    def __init__(
        self,
        *,
        config: DirectusCreateOnlyConfig,
        http: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self._owns_client = http is None
        self.http = http or httpx.Client(timeout=60, follow_redirects=True)

    def close(self) -> None:
        if self._owns_client:
            self.http.close()

    def __enter__(self) -> "DirectusCreateOnlyClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        data: Mapping[str, Any] | None = None,
        files: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        normalized_method = method.strip().upper()
        if normalized_method not in CREATE_ONLY_METHODS:
            raise DirectusCreateOnlyMethodError(
                f"HTTP method {normalized_method or '<empty>'!r} is forbidden; "
                "create-only transport allows GET, HEAD, and POST only."
            )

        url = self._endpoint_url(endpoint)
        if normalized_method == "POST":
            self._validate_post_endpoint(url)

        return self.http.request(
            normalized_method,
            url,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=self._merge_headers(headers),
        )

    def get(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("GET", endpoint, params=params, headers=headers)

    def head(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("HEAD", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        *,
        json: Any | None = None,
        data: Mapping[str, Any] | None = None,
        files: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return self.request(
            "POST",
            endpoint,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )

    def create_item(self, collection: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        response = self.post(f"/items/{_require_text(collection, 'collection')}", json=dict(payload))
        response.raise_for_status()
        return response.json().get("data", {})

    def create_folder(self, name: str, parent: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": _require_text(name, "name")}
        if parent is not None:
            payload["parent"] = _require_text(parent, "parent")
        response = self.post("/folders", json=payload)
        response.raise_for_status()
        return response.json().get("data", {})

    def upload_file(
        self,
        *,
        folder_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> dict[str, Any]:
        response = self.post(
            "/files",
            files={"file": (filename, content, content_type)},
            data={"folder": _require_text(folder_id, "folder_id")},
        )
        response.raise_for_status()
        return response.json().get("data", {})

    def _endpoint_url(self, endpoint: str) -> str:
        return urljoin(self.config.base_url + "/", _require_text(endpoint, "endpoint").lstrip("/"))

    def _merge_headers(self, headers: Mapping[str, str] | None) -> dict[str, str] | None:
        merged = dict(headers or {})
        merged.setdefault("User-Agent", self.config.user_agent)
        if self.config.auth_token is not None:
            merged["Authorization"] = f"Bearer {self.config.auth_token}"
        return merged

    def _validate_post_endpoint(self, url: str) -> None:
        path = urlparse(url).path.rstrip("/")
        if path == "/files":
            if not self.config.allow_files:
                raise DirectusCreateOnlyEndpointError("/files POST is disabled by config.")
            return
        if path == "/folders":
            if not self.config.allow_folders:
                raise DirectusCreateOnlyEndpointError("/folders POST is disabled by config.")
            return
        if path.startswith("/items/"):
            collection = path.removeprefix("/items/").strip("/")
            if collection in self.config.allowed_item_collections:
                return
            raise DirectusCreateOnlyEndpointError(
                f"POST to collection {collection!r} is not in the allowed create list."
            )
        raise DirectusCreateOnlyEndpointError(
            f"POST to endpoint {path or '/'} is not allowed by the create-only client."
        )
