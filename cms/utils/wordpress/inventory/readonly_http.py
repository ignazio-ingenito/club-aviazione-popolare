"""Small HTTP wrapper that can transmit only read methods."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from .errors import ReadOnlyMethodError, ResponseContractError

_ALLOWED_METHODS = frozenset({"GET", "HEAD"})


class ReadOnlyHttpClient:
    """Own an httpx client while enforcing method and URL boundaries."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        parsed = httpx.URL(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.host:
            raise ValueError("base_url must be an absolute HTTP(S) URL.")
        if parsed.username or parsed.password:
            raise ValueError("Credentials must not be embedded in base_url.")
        normalized = str(parsed.copy_with(query=None, fragment=None)).rstrip("/") + "/"
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "cap-wordpress-inventory/1",
            **dict(headers or {}),
        }
        self._client = httpx.Client(
            base_url=normalized,
            timeout=timeout,
            follow_redirects=True,
            transport=transport,
            headers=request_headers,
        )

    @property
    def base_url(self) -> str:
        return str(self._client.base_url).rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        normalized_method = method.upper().strip()
        if normalized_method not in _ALLOWED_METHODS:
            raise ReadOnlyMethodError(
                f"HTTP method {normalized_method or '<empty>'} is not allowed."
            )

        parsed_path = httpx.URL(path)
        if parsed_path.is_absolute_url or path.startswith(("/", "//")):
            raise ValueError("Inventory request paths must be relative to base_url.")

        response = self._client.request(
            normalized_method,
            path,
            params=dict(params or {}),
        )
        response.raise_for_status()
        return response

    def get(
        self, path: str, *, params: Mapping[str, Any] | None = None
    ) -> httpx.Response:
        return self.request("GET", path, params=params)

    def head(
        self, path: str, *, params: Mapping[str, Any] | None = None
    ) -> httpx.Response:
        return self.request("HEAD", path, params=params)

    def get_json(
        self, path: str, *, params: Mapping[str, Any] | None = None
    ) -> tuple[httpx.Response, Any]:
        response = self.get(path, params=params)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ResponseContractError(
                f"Response from {response.url} is not valid JSON."
            ) from exc
        return response, payload

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ReadOnlyHttpClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
