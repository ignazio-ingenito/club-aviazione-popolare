"""Fresh, GET-only WordPress REST inventory client."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from .models import InventoryIssue, InventoryManifest, InventoryScope, IssueSeverity, ManifestRecord
from .pagination import InventoryPage, PageMetadata, merge_complete_pages
from .transport import ReadOnlyHttpClient
from .wordpress_records import BuiltWordPressRecord, build_category_record, build_media_record, build_post_record, build_type_record

WORDPRESS_API_PATH = "wp-json/wp/v2"
DEFAULT_PER_PAGE = 100
RecordBuilder = Callable[[Mapping[str, Any]], BuiltWordPressRecord]


class WordPressProtocolError(RuntimeError):
    """Raised when WordPress responses cannot prove a complete inventory."""


@dataclass(frozen=True, slots=True)
class WordPressCollectionInventory:
    endpoint: str
    records: tuple[ManifestRecord, ...]
    issues: tuple[InventoryIssue, ...]
    total_items: int
    total_pages: int
    per_page: int | None


def _validate_site_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("site_url must be an absolute HTTP(S) URL.")
    if parsed.query or parsed.fragment:
        raise ValueError("site_url cannot contain a query string or fragment.")
    return normalized


class WordPressReadOnlyClient:
    """Fresh-by-default inventory client for the public WordPress REST API."""

    def __init__(self, site_url: str, *, per_page: int = DEFAULT_PER_PAGE, timeout: float = 30.0, transport: httpx.BaseTransport | None = None) -> None:
        if isinstance(per_page, bool) or not isinstance(per_page, int):
            raise ValueError("per_page must be an integer.")
        if per_page < 1 or per_page > 100:
            raise ValueError("per_page must be between 1 and 100.")
        self.site_url = _validate_site_url(site_url)
        self.api_base_url = f"{self.site_url}/{WORDPRESS_API_PATH}/"
        self.per_page = per_page
        self._http = ReadOnlyHttpClient(self.api_base_url, timeout=timeout, verify=True, follow_redirects=True, transport=transport)

    def _required_header_int(self, response: httpx.Response, name: str) -> int:
        raw_value = response.headers.get(name)
        if raw_value is None:
            raise WordPressProtocolError(f"WordPress response is missing {name}.")
        try:
            value = int(raw_value)
        except ValueError as exc:
            raise WordPressProtocolError(f"WordPress response header {name} is not an integer.") from exc
        if value < 0:
            raise WordPressProtocolError(f"WordPress response header {name} cannot be negative.")
        return value

    def _fetch_page(self, endpoint: str, *, page: int, params: Mapping[str, Any]) -> InventoryPage[Mapping[str, Any]]:
        query = dict(params)
        query.update({"page": page, "per_page": self.per_page})
        response, payload = self._http.get_json(endpoint, params=query)
        if not isinstance(payload, list):
            raise WordPressProtocolError(f"WordPress endpoint {endpoint} returned {type(payload).__name__}; expected a JSON array.")
        metadata = PageMetadata(
            page=page,
            per_page=self.per_page,
            total_items=self._required_header_int(response, "X-WP-Total"),
            total_pages=self._required_header_int(response, "X-WP-TotalPages"),
        )
        return InventoryPage(metadata, payload)

    def _fetch_paginated(self, endpoint: str, *, params: Mapping[str, Any], entity_type: str, builder: RecordBuilder) -> WordPressCollectionInventory:
        pages = [self._fetch_page(endpoint, page=1, params=params)]
        for page_number in range(2, pages[0].metadata.total_pages + 1):
            pages.append(self._fetch_page(endpoint, page=page_number, params=params))
        raw_items = merge_complete_pages(pages)
        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = []
        for index, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, Mapping):
                issues.append(InventoryIssue(
                    scope=InventoryScope.SOURCE,
                    code="wordpress_invalid_record",
                    message="WordPress collection item is not a JSON object.",
                    severity=IssueSeverity.ERROR,
                    details={"endpoint": endpoint, "index": index, "value_type": type(raw_item).__name__},
                ))
                continue
            try:
                built = builder(raw_item)
            except (TypeError, ValueError) as exc:
                details: dict[str, Any] = {"endpoint": endpoint, "index": index, "reason": str(exc)}
                raw_id = raw_item.get("id")
                if isinstance(raw_id, int) and not isinstance(raw_id, bool):
                    details["source_id"] = raw_id
                issues.append(InventoryIssue(
                    scope=InventoryScope.SOURCE,
                    code="wordpress_record_build_failed",
                    message=f"WordPress {entity_type} record could not be normalized.",
                    severity=IssueSeverity.ERROR,
                    details=details,
                ))
                continue
            records.append(built.record)
            issues.extend(built.issues)
        first = pages[0].metadata
        return WordPressCollectionInventory(endpoint, tuple(records), tuple(issues), first.total_items, first.total_pages, self.per_page)

    def fetch_types(self) -> WordPressCollectionInventory:
        _, payload = self._http.get_json("types", params={"context": "view"})
        if not isinstance(payload, Mapping):
            raise WordPressProtocolError(f"WordPress endpoint types returned {type(payload).__name__}; expected a JSON object.")
        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = []
        for index, (key, raw_item) in enumerate(sorted(payload.items())):
            if not isinstance(key, str) or not isinstance(raw_item, Mapping):
                issues.append(InventoryIssue(
                    scope=InventoryScope.SOURCE,
                    code="wordpress_invalid_type",
                    message="WordPress type entry is not a keyed JSON object.",
                    severity=IssueSeverity.ERROR,
                    details={"index": index, "key_type": type(key).__name__, "value_type": type(raw_item).__name__},
                ))
                continue
            try:
                built = build_type_record(key, raw_item)
            except (TypeError, ValueError) as exc:
                issues.append(InventoryIssue(
                    scope=InventoryScope.SOURCE,
                    code="wordpress_type_build_failed",
                    message="WordPress type record could not be normalized.",
                    severity=IssueSeverity.ERROR,
                    details={"endpoint_key": key, "reason": str(exc)},
                ))
                continue
            records.append(built.record)
            issues.extend(built.issues)
        return WordPressCollectionInventory("types", tuple(records), tuple(issues), len(payload), 1 if payload else 0, None)

    def fetch_categories(self) -> WordPressCollectionInventory:
        return self._fetch_paginated(
            "categories",
            params={"hide_empty": "false", "orderby": "id", "order": "asc"},
            entity_type="category",
            builder=build_category_record,
        )

    def fetch_posts(self, *, status: str = "publish") -> WordPressCollectionInventory:
        normalized_status = status.strip()
        if not normalized_status:
            raise ValueError("status cannot be empty.")
        return self._fetch_paginated(
            "posts",
            params={"status": normalized_status, "orderby": "id", "order": "asc", "_embed": "true"},
            entity_type="post",
            builder=build_post_record,
        )

    def fetch_media(self) -> WordPressCollectionInventory:
        return self._fetch_paginated(
            "media",
            params={"orderby": "id", "order": "asc"},
            entity_type="media",
            builder=build_media_record,
        )

    def collect_manifest(self, *, environment: str, observed_at: datetime | None = None, include_media: bool = True) -> InventoryManifest:
        observation_time = observed_at or datetime.now(timezone.utc)
        collections = [self.fetch_types(), self.fetch_categories(), self.fetch_posts()]
        if include_media:
            collections.append(self.fetch_media())
        return InventoryManifest(
            scope=InventoryScope.SOURCE,
            environment=environment,
            base_url=self.site_url,
            observed_at=observation_time,
            records=(record for collection in collections for record in collection.records),
            issues=(issue for collection in collections for issue in collection.issues),
            metadata={
                "client": "wordpress-rest-readonly-v1",
                "api_base_url": self.api_base_url,
                "fresh_by_default": True,
                "allowed_http_methods": ["GET", "HEAD"],
                "collections": {
                    collection.endpoint: {
                        "api_total_items": collection.total_items,
                        "normalized_records": len(collection.records),
                        "issues": len(collection.issues),
                        "total_pages": collection.total_pages,
                        "per_page": collection.per_page,
                    }
                    for collection in collections
                },
            },
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "WordPressReadOnlyClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
