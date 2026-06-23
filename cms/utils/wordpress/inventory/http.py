"""GET/HEAD-only HTTP transport used by migration inventory clients."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx


READ_ONLY_METHODS = frozenset({"GET", "HEAD"})


class ReadOnlyMethodError(ValueError):
    """Raised before transport use when a non-read HTTP method is requested."""


class ReadOnlyHttpClient:
    """Small HTTP wrapper whose public request path permits only GET and HEAD.

    The default client keeps TLS verification enabled, follows redirects, and does
    not cache responses. Tests can inject an ``httpx.Client`` with ``MockTransport``.
    Injected clients remain owned by the caller and are not closed by this wrapper.
    """

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
        user_agent: str = "cap-wordpress-inventory/1",
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero.")

        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        normalized_method = method.strip().upper()
        if normalized_method not in READ_ONLY_METHODS:
            raise ReadOnlyMethodError(
                f"HTTP method {normalized_method or '<empty>'!r} is forbidden; "
                "inventory transports allow GET and HEAD only."
            )

        return self._client.request(
            normalized_method,
            url,
            params=params,
            headers=headers,
        )

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("GET", url, params=params, headers=headers)

    def head(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return self.request("HEAD", url, params=params, headers=headers)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "ReadOnlyHttpClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
