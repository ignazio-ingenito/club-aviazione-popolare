"""GET/HEAD-only HTTP transport for migration inventory clients."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

import httpx

READ_ONLY_METHODS = frozenset({"GET", "HEAD"})


class ReadOnlyMethodError(RuntimeError):
    """Raised before network I/O when a non-read HTTP method is requested."""


class ReadOnlyEndpointError(ValueError):
    """Raised when an endpoint escapes the configured inventory API base URL."""


class InventoryHttpError(RuntimeError):
    """Sanitized HTTP/JSON error that never includes response bodies."""

    def __init__(self, message: str, *, method: str, url: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.method = method
        self.url = url
        self.status_code = status_code


def _validate_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/") + "/"
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an absolute HTTP(S) URL.")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url cannot contain a query string or fragment.")
    return normalized


def _validate_relative_endpoint(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ReadOnlyEndpointError("endpoint cannot be empty.")
    parsed = urlparse(normalized)
    if parsed.scheme or parsed.netloc:
        raise ReadOnlyEndpointError("endpoint must be relative to the configured base URL.")
    if parsed.query or parsed.fragment:
        raise ReadOnlyEndpointError("endpoint cannot contain a query string or fragment; use params instead.")
    if ".." in [part for part in parsed.path.split("/") if part]:
        raise ReadOnlyEndpointError("endpoint cannot contain parent path traversal.")
    return normalized.lstrip("/")


def _origin(value: str | httpx.URL) -> tuple[str, str, int]:
    parsed = urlparse(str(value))
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    return scheme, hostname, parsed.port or (443 if scheme == "https" else 80)


class ReadOnlyHttpClient:
    """Small httpx wrapper that allows GET/HEAD requests only."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        follow_redirects: bool = True,
        verify: bool = True,
        headers: Mapping[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = _validate_base_url(base_url)
        self._origin = _origin(self.base_url)
        default_headers = {"Accept": "application/json", "User-Agent": "cap-wordpress-inventory/1"}
        if headers:
            default_headers.update(dict(headers))
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify=verify,
            headers=default_headers,
            transport=transport,
        )

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        normalized_method = method.strip().upper()
        if normalized_method not in READ_ONLY_METHODS:
            raise ReadOnlyMethodError(f"HTTP method {normalized_method or '<empty>'} is forbidden for inventory.")
        relative_endpoint = _validate_relative_endpoint(endpoint)
        try:
            response = self._client.request(normalized_method, relative_endpoint, params=params, headers=headers)
            if _origin(response.url) != self._origin:
                raise InventoryHttpError(
                    "Read-only request redirected outside the configured origin.",
                    method=normalized_method,
                    url=str(response.url),
                    status_code=response.status_code,
                )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            raise InventoryHttpError(
                f"{normalized_method} request failed with HTTP {exc.response.status_code}.",
                method=normalized_method,
                url=str(exc.request.url),
                status_code=exc.response.status_code,
            ) from exc
        except httpx.HTTPError as exc:
            try:
                request_url = str(exc.request.url)
            except RuntimeError:
                request_url = self.base_url
            raise InventoryHttpError(
                f"{normalized_method} request failed before a valid response was received.",
                method=normalized_method,
                url=request_url,
            ) from exc

    def get(self, endpoint: str, *, params: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> httpx.Response:
        return self.request("GET", endpoint, params=params, headers=headers)

    def head(self, endpoint: str, *, params: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> httpx.Response:
        return self.request("HEAD", endpoint, params=params, headers=headers)

    def get_json(self, endpoint: str, *, params: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> tuple[httpx.Response, Any]:
        response = self.get(endpoint, params=params, headers=headers)
        try:
            return response, response.json()
        except ValueError as exc:
            raise InventoryHttpError(
                "GET request returned invalid JSON.",
                method="GET",
                url=str(response.request.url),
                status_code=response.status_code,
            ) from exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ReadOnlyHttpClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
