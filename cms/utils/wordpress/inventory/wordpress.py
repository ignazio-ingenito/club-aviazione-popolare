"""Fresh, read-only WordPress REST inventory client."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from .http import ReadOnlyHttpClient
from .models import (
    InventoryIssue,
    InventoryManifest,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
)
from .pagination import InventoryPage, PageMetadata, PaginationError, merge_complete_pages


WORDPRESS_API_PATH = "wp-json/wp/v2/"
WORDPRESS_MAX_PER_PAGE = 100


class WordPressInventoryError(RuntimeError):
    """Fail-closed WordPress inventory error with a serializable fatal issue."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        endpoint: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.endpoint = endpoint
        self.details = dict(details or {})

    def to_issue(self) -> InventoryIssue:
        return InventoryIssue(
            scope=InventoryScope.SOURCE,
            severity=IssueSeverity.FATAL,
            code=self.code,
            message=str(self),
            details={"endpoint": self.endpoint, **self.details},
        )


class WordPressHttpError(WordPressInventoryError):
    """Raised for transport failures and non-success HTTP responses."""


class WordPressProtocolError(WordPressInventoryError):
    """Raised when WordPress returns incomplete or inconsistent REST metadata."""


@dataclass(frozen=True, slots=True)
class WordPressInventoryConfig:
    base_url: str = "https://www.clubaviazionepopolare.org"
    per_page: int = WORDPRESS_MAX_PER_PAGE

    def __post_init__(self) -> None:
        normalized = self.base_url.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be an absolute HTTP(S) URL.")
        if not 1 <= self.per_page <= WORDPRESS_MAX_PER_PAGE:
            raise ValueError(
                f"per_page must be between 1 and {WORDPRESS_MAX_PER_PAGE}."
            )
        object.__setattr__(self, "base_url", normalized)

    @property
    def api_base_url(self) -> str:
        return urljoin(f"{self.base_url}/", WORDPRESS_API_PATH)


@dataclass(frozen=True, slots=True)
class WordPressCollectionResult:
    endpoint: str
    records: tuple[ManifestRecord, ...]
    issues: tuple[InventoryIssue, ...]
    total_items: int
    total_pages: int
    raw_item_count: int

    def metadata(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "raw_item_count": self.raw_item_count,
            "record_count": len(self.records),
            "issue_count": len(self.issues),
        }


@dataclass(frozen=True, slots=True)
class WordPressInventorySnapshot:
    base_url: str
    results: tuple[WordPressCollectionResult, ...]

    @property
    def records(self) -> tuple[ManifestRecord, ...]:
        return tuple(record for result in self.results for record in result.records)

    @property
    def issues(self) -> tuple[InventoryIssue, ...]:
        return tuple(issue for result in self.results for issue in result.issues)

    def to_manifest(
        self,
        *,
        environment: str,
        observed_at: datetime,
        metadata: Mapping[str, Any] | None = None,
    ) -> InventoryManifest:
        endpoint_metadata = {
            result.endpoint: result.metadata() for result in self.results
        }
        return InventoryManifest(
            scope=InventoryScope.SOURCE,
            environment=environment,
            base_url=self.base_url,
            observed_at=observed_at,
            records=self.records,
            issues=self.issues,
            metadata={
                "wordpress_api": WORDPRESS_API_PATH.rstrip("/"),
                "endpoints": endpoint_metadata,
                **dict(metadata or {}),
            },
        )


class WordPressInventoryClient:
    """Inventory public WordPress REST resources without implicit cache or writes."""

    def __init__(
        self,
        *,
        config: WordPressInventoryConfig | None = None,
        http: ReadOnlyHttpClient | None = None,
    ) -> None:
        self.config = config or WordPressInventoryConfig()
        self._owns_http = http is None
        self.http = http or ReadOnlyHttpClient()

    def close(self) -> None:
        if self._owns_http:
            self.http.close()

    def __enter__(self) -> "WordPressInventoryClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def get_types(self) -> WordPressCollectionResult:
        endpoint = "types"
        _, payload = self._get_json(endpoint)
        if not isinstance(payload, dict):
            raise WordPressProtocolError(
                "invalid_json_shape",
                "WordPress types endpoint must return an object keyed by type slug.",
                endpoint=endpoint,
                details={"received_type": type(payload).__name__},
            )

        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = []
        for raw_slug, raw_value in sorted(payload.items(), key=lambda item: str(item[0])):
            slug = str(raw_slug).strip()
            if not slug or not isinstance(raw_value, Mapping):
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.SOURCE,
                        severity=IssueSeverity.ERROR,
                        code="malformed_wordpress_type",
                        message="WordPress type entry is missing a slug or object payload.",
                        details={
                            "endpoint": endpoint,
                            "raw_slug": str(raw_slug),
                            "received_type": type(raw_value).__name__,
                        },
                    )
                )
                continue

            records.append(
                ManifestRecord(
                    scope=InventoryScope.SOURCE,
                    entity_type="wordpress_type",
                    identity=f"wordpress:type:{slug}",
                    data=dict(raw_value),
                )
            )

        total_items = len(payload)
        return WordPressCollectionResult(
            endpoint=endpoint,
            records=tuple(records),
            issues=tuple(issues),
            total_items=total_items,
            total_pages=1 if total_items else 0,
            raw_item_count=total_items,
        )

    def get_categories(self) -> WordPressCollectionResult:
        return self._get_paginated(
            endpoint="categories",
            entity_type="wordpress_category",
            identity_prefix="wordpress:category",
            source_url_fields=("link",),
            params={"hide_empty": "false", "orderby": "id", "order": "asc"},
        )

    def get_posts(self, *, status: str = "publish") -> WordPressCollectionResult:
        normalized_status = status.strip()
        if not normalized_status:
            raise ValueError("status cannot be empty.")
        return self._get_paginated(
            endpoint="posts",
            entity_type="wordpress_post",
            identity_prefix="wordpress:post",
            source_url_fields=("link",),
            params={
                "status": normalized_status,
                "orderby": "id",
                "order": "asc",
                "_embed": "1",
            },
        )

    def get_media(self, *, status: str = "inherit") -> WordPressCollectionResult:
        normalized_status = status.strip()
        if not normalized_status:
            raise ValueError("status cannot be empty.")
        return self._get_paginated(
            endpoint="media",
            entity_type="wordpress_media",
            identity_prefix="wordpress:media",
            source_url_fields=("link", "source_url"),
            params={
                "status": normalized_status,
                "orderby": "id",
                "order": "asc",
            },
        )

    def inventory_core(self) -> WordPressInventorySnapshot:
        """Fetch a fresh core snapshot. No result is cached between calls."""

        return WordPressInventorySnapshot(
            base_url=self.config.base_url,
            results=(
                self.get_types(),
                self.get_categories(),
                self.get_posts(),
                self.get_media(),
            ),
        )

    def _endpoint_url(self, endpoint: str) -> str:
        normalized = endpoint.strip("/")
        if not normalized or "/" in normalized or ":" in normalized:
            raise ValueError(f"Invalid WordPress REST endpoint {endpoint!r}.")
        return urljoin(self.config.api_base_url, normalized)

    def _get_json(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> tuple[httpx.Response, Any]:
        url = self._endpoint_url(endpoint)
        try:
            response = self.http.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise WordPressHttpError(
                "wordpress_http_status",
                f"WordPress returned HTTP {exc.response.status_code} for {endpoint}.",
                endpoint=endpoint,
                details={
                    "status_code": exc.response.status_code,
                    "method": exc.request.method,
                    "url": str(exc.request.url),
                },
            ) from exc
        except httpx.HTTPError as exc:
            request = getattr(exc, "request", None)
            raise WordPressHttpError(
                "wordpress_transport_error",
                f"WordPress request failed for {endpoint}: {type(exc).__name__}.",
                endpoint=endpoint,
                details={
                    "method": getattr(request, "method", "GET"),
                    "url": str(getattr(request, "url", url)),
                },
            ) from exc

        try:
            payload = response.json()
        except (ValueError, UnicodeError) as exc:
            raise WordPressProtocolError(
                "invalid_json",
                f"WordPress returned invalid JSON for {endpoint}.",
                endpoint=endpoint,
                details={
                    "status_code": response.status_code,
                    "url": str(response.request.url),
                },
            ) from exc
        return response, payload

    def _pagination_metadata(
        self,
        endpoint: str,
        response: httpx.Response,
        *,
        page: int,
    ) -> PageMetadata:
        total_header = response.headers.get("X-WP-Total")
        pages_header = response.headers.get("X-WP-TotalPages")
        if total_header is None or pages_header is None:
            raise WordPressProtocolError(
                "missing_pagination_headers",
                "WordPress response is missing X-WP-Total or X-WP-TotalPages.",
                endpoint=endpoint,
                details={
                    "page": page,
                    "has_total": total_header is not None,
                    "has_total_pages": pages_header is not None,
                },
            )

        try:
            total_items = int(total_header)
            total_pages = int(pages_header)
        except ValueError as exc:
            raise WordPressProtocolError(
                "invalid_pagination_headers",
                "WordPress pagination headers must be integers.",
                endpoint=endpoint,
                details={
                    "page": page,
                    "x_wp_total": total_header,
                    "x_wp_totalpages": pages_header,
                },
            ) from exc

        try:
            return PageMetadata(
                page=page,
                per_page=self.config.per_page,
                total_items=total_items,
                total_pages=total_pages,
            )
        except PaginationError as exc:
            raise WordPressProtocolError(
                "inconsistent_pagination",
                f"WordPress pagination is inconsistent for {endpoint}: {exc}",
                endpoint=endpoint,
                details={
                    "page": page,
                    "per_page": self.config.per_page,
                    "total_items": total_items,
                    "total_pages": total_pages,
                },
            ) from exc

    def _get_paginated(
        self,
        *,
        endpoint: str,
        entity_type: str,
        identity_prefix: str,
        source_url_fields: tuple[str, ...],
        params: Mapping[str, Any],
    ) -> WordPressCollectionResult:
        first_params = {
            "context": "view",
            "per_page": self.config.per_page,
            "page": 1,
            **dict(params),
        }
        response, payload = self._get_json(endpoint, params=first_params)
        if not isinstance(payload, list):
            raise WordPressProtocolError(
                "invalid_json_shape",
                f"WordPress {endpoint} endpoint must return an array.",
                endpoint=endpoint,
                details={"page": 1, "received_type": type(payload).__name__},
            )

        first_metadata = self._pagination_metadata(endpoint, response, page=1)
        try:
            pages: list[InventoryPage[Any]] = [
                InventoryPage(first_metadata, payload)
            ]
        except PaginationError as exc:
            raise WordPressProtocolError(
                "inconsistent_page_size",
                f"WordPress page size is inconsistent for {endpoint}: {exc}",
                endpoint=endpoint,
                details={"page": 1, "item_count": len(payload)},
            ) from exc

        for page_number in range(2, first_metadata.total_pages + 1):
            page_params = {**first_params, "page": page_number}
            page_response, page_payload = self._get_json(
                endpoint, params=page_params
            )
            if not isinstance(page_payload, list):
                raise WordPressProtocolError(
                    "invalid_json_shape",
                    f"WordPress {endpoint} page {page_number} must return an array.",
                    endpoint=endpoint,
                    details={
                        "page": page_number,
                        "received_type": type(page_payload).__name__,
                    },
                )
            page_metadata = self._pagination_metadata(
                endpoint, page_response, page=page_number
            )
            try:
                pages.append(InventoryPage(page_metadata, page_payload))
            except PaginationError as exc:
                raise WordPressProtocolError(
                    "inconsistent_page_size",
                    f"WordPress page size is inconsistent for {endpoint}: {exc}",
                    endpoint=endpoint,
                    details={
                        "page": page_number,
                        "item_count": len(page_payload),
                    },
                ) from exc

        try:
            raw_items = merge_complete_pages(pages)
        except PaginationError as exc:
            raise WordPressProtocolError(
                "incomplete_pagination",
                f"WordPress pagination is incomplete for {endpoint}: {exc}",
                endpoint=endpoint,
                details={"fetched_pages": len(pages)},
            ) from exc

        records, issues = self._records_from_items(
            endpoint=endpoint,
            raw_items=raw_items,
            entity_type=entity_type,
            identity_prefix=identity_prefix,
            source_url_fields=source_url_fields,
        )
        return WordPressCollectionResult(
            endpoint=endpoint,
            records=records,
            issues=issues,
            total_items=first_metadata.total_items,
            total_pages=first_metadata.total_pages,
            raw_item_count=len(raw_items),
        )

    def _records_from_items(
        self,
        *,
        endpoint: str,
        raw_items: Iterable[Any],
        entity_type: str,
        identity_prefix: str,
        source_url_fields: tuple[str, ...],
    ) -> tuple[tuple[ManifestRecord, ...], tuple[InventoryIssue, ...]]:
        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = []

        for index, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, Mapping):
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.SOURCE,
                        severity=IssueSeverity.ERROR,
                        code="malformed_wordpress_item",
                        message="WordPress collection item is not an object.",
                        details={
                            "endpoint": endpoint,
                            "index": index,
                            "received_type": type(raw_item).__name__,
                        },
                    )
                )
                continue

            raw_id = raw_item.get("id")
            if isinstance(raw_id, bool) or not isinstance(raw_id, int) or raw_id < 1:
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.SOURCE,
                        severity=IssueSeverity.ERROR,
                        code="invalid_wordpress_id",
                        message="WordPress collection item has no positive integer ID.",
                        details={
                            "endpoint": endpoint,
                            "index": index,
                            "raw_id": raw_id,
                        },
                    )
                )
                continue

            identity = f"{identity_prefix}:{raw_id}"
            source_url = self._first_valid_source_url(
                raw_item,
                fields=source_url_fields,
                endpoint=endpoint,
                entity_type=entity_type,
                identity=identity,
                issues=issues,
            )
            records.append(
                ManifestRecord(
                    scope=InventoryScope.SOURCE,
                    entity_type=entity_type,
                    identity=identity,
                    source_url=source_url,
                    data=dict(raw_item),
                )
            )

        return tuple(records), tuple(issues)

    def _first_valid_source_url(
        self,
        item: Mapping[str, Any],
        *,
        fields: tuple[str, ...],
        endpoint: str,
        entity_type: str,
        identity: str,
        issues: list[InventoryIssue],
    ) -> str | None:
        invalid_values: list[dict[str, str]] = []
        for field in fields:
            raw_value = item.get(field)
            if raw_value is None or raw_value == "":
                continue
            value = str(raw_value).strip()
            parsed = urlparse(value)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                return value
            invalid_values.append({"field": field, "value": value})

        if invalid_values:
            issues.append(
                InventoryIssue(
                    scope=InventoryScope.SOURCE,
                    severity=IssueSeverity.WARNING,
                    code="invalid_source_url",
                    message="WordPress item contains no valid absolute source URL.",
                    entity_type=entity_type,
                    identity=identity,
                    details={"endpoint": endpoint, "values": invalid_values},
                )
            )
        return None
