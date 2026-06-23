"""Anonymous/read-only Directus inventory client."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from .canonical import canonical_sha256
from .http import ReadOnlyHttpClient
from .models import (
    InventoryIssue,
    InventoryManifest,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
)
from .pagination import InventoryPage, PageMetadata, PaginationError, merge_complete_pages


DIRECTUS_MAX_LIMIT = 100
FEED_FIELDS = (
    "id",
    "author",
    "category",
    "cover",
    "cover_offset_x",
    "cover_offset_y",
    "content",
    "description",
    "date",
    "featured",
    "slug",
    "gallery",
    "sort",
    "status",
    "title",
    "original_uri",
    "user_created",
    "date_created",
    "user_updated",
    "date_updated",
)
CATEGORY_FIELDS = (
    "key",
    "title",
    "description",
    "status",
    "sort",
    "date_created",
    "date_updated",
)
APPLICATION_IDENTITY_FIELDS = ("id", "key", "slug", "collection")
SYSTEM_COLLECTION_PREFIX = "directus_"
VALID_COLLECTION_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class DirectusInventoryError(RuntimeError):
    """Fail-closed Directus inventory error with a serializable fatal issue."""

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
            scope=InventoryScope.TARGET,
            severity=IssueSeverity.FATAL,
            code=self.code,
            message=str(self),
            details={"endpoint": self.endpoint, **self.details},
        )


class DirectusHttpError(DirectusInventoryError):
    """Raised for transport failures when no response can be inventoried."""


class DirectusProtocolError(DirectusInventoryError):
    """Raised when Directus returns incomplete or inconsistent payloads."""


@dataclass(frozen=True, slots=True)
class DirectusInventoryConfig:
    base_url: str = "https://cap-cms.skunklabs.uk"
    limit: int = DIRECTUS_MAX_LIMIT
    auth_token: str | None = None

    def __post_init__(self) -> None:
        normalized = self.base_url.strip().rstrip("/")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be an absolute HTTP(S) URL.")
        if not 1 <= self.limit <= DIRECTUS_MAX_LIMIT:
            raise ValueError(f"limit must be between 1 and {DIRECTUS_MAX_LIMIT}.")
        object.__setattr__(self, "base_url", normalized)
        if self.auth_token is not None:
            token = self.auth_token.strip()
            if not token:
                raise ValueError("auth_token cannot be empty when provided.")
            object.__setattr__(self, "auth_token", token)


@dataclass(frozen=True, slots=True)
class DirectusCollectionResult:
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
class DirectusInventorySnapshot:
    base_url: str
    results: tuple[DirectusCollectionResult, ...]

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
            scope=InventoryScope.TARGET,
            environment=environment,
            base_url=self.base_url,
            observed_at=observed_at,
            records=self.records,
            issues=self.issues,
            metadata={
                "directus_api": "rest",
                "endpoints": endpoint_metadata,
                **dict(metadata or {}),
            },
        )


class DirectusInventoryClient:
    """Inventory Directus resources without cache or write-capable requests."""

    def __init__(
        self,
        *,
        config: DirectusInventoryConfig | None = None,
        http: ReadOnlyHttpClient | None = None,
    ) -> None:
        self.config = config or DirectusInventoryConfig()
        self._owns_http = http is None
        self.http = http or ReadOnlyHttpClient()

    def close(self) -> None:
        if self._owns_http:
            self.http.close()

    def __enter__(self) -> "DirectusInventoryClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def get_server_info(self) -> DirectusCollectionResult:
        return self._get_singleton(
            endpoint="server/info",
            entity_type="directus_server_info",
            identity="directus:server:info",
            payload_key="data",
        )

    def get_permissions_me(self) -> DirectusCollectionResult:
        return self._get_singleton(
            endpoint="permissions/me",
            entity_type="directus_permissions",
            identity="directus:permissions:me",
            payload_key="data",
        )

    def get_collections(self) -> DirectusCollectionResult:
        return self._get_system_array(
            endpoint="collections",
            entity_type="directus_collection",
            identity_field="collection",
            identity_prefix="directus:collection",
        )

    def get_fields(self) -> DirectusCollectionResult:
        return self._get_system_array(
            endpoint="fields",
            entity_type="directus_field",
            identity_builder=_field_identity,
        )

    def get_relations(self) -> DirectusCollectionResult:
        result = self._get_system_array(
            endpoint="relations",
            entity_type="directus_relation",
            identity_builder=_relation_identity,
        )
        return _dedupe_identical_relation_records(result)

    def get_feeds(self) -> DirectusCollectionResult:
        return self._get_items(
            collection="feeds",
            entity_type="directus_feed",
            identity_prefix="directus:feed",
            fields=FEED_FIELDS,
        )

    def get_categories(self) -> DirectusCollectionResult:
        return self._get_items(
            collection="categories",
            entity_type="directus_category",
            identity_prefix="directus:category",
            fields=CATEGORY_FIELDS,
            identity_field="key",
            sort_field="key",
        )

    def get_files(self) -> DirectusCollectionResult:
        return self._get_paginated(
            endpoint="files",
            entity_type="directus_file",
            identity_prefix="directus:file",
            fields=(
                "id",
                "filename_disk",
                "filename_download",
                "title",
                "type",
                "filesize",
                "folder",
                "uploaded_on",
                "modified_on",
            ),
        )

    def get_folders(self) -> DirectusCollectionResult:
        return self._get_paginated(
            endpoint="folders",
            entity_type="directus_folder",
            identity_prefix="directus:folder",
            fields=("id", "name", "parent"),
        )

    def inventory_core(self) -> DirectusInventorySnapshot:
        """Fetch a fresh anonymous/read-only snapshot. Results are not cached."""

        return DirectusInventorySnapshot(
            base_url=self.config.base_url,
            results=(
                self.get_server_info(),
                self.get_permissions_me(),
                self.get_collections(),
                self.get_fields(),
                self.get_relations(),
                self.get_feeds(),
                self.get_categories(),
                self.get_files(),
                self.get_folders(),
            ),
        )

    def inventory_application_collections(
        self,
        *,
        collection_names: tuple[str, ...] | None = None,
    ) -> DirectusInventorySnapshot:
        """Fetch all readable non-system Directus application collections."""

        collections_result = self.get_collections()
        fields_result = self.get_fields()
        fields_by_collection = _fields_by_collection(fields_result.records)
        singleton_collections = _singleton_collection_names(collections_result.records)
        resolved_collections = _application_collection_names(
            collections_result.records,
            requested=collection_names,
        )

        results: list[DirectusCollectionResult] = []
        for collection in resolved_collections:
            fields = fields_by_collection.get(collection)
            if not fields:
                raise DirectusProtocolError(
                    "missing_directus_collection_fields",
                    "Directus collection has no readable field metadata.",
                    endpoint="fields",
                    details={"collection": collection},
                )
            if collection in singleton_collections:
                results.append(
                    self._get_singleton(
                        endpoint=f"items/{collection}",
                        entity_type="directus_app_item",
                        identity=f"directus:item:{collection}:singleton",
                        payload_key="data",
                    )
                )
            else:
                identity_field = _application_identity_field(collection, fields)
                results.append(
                    self._get_paginated(
                        endpoint=f"items/{collection}",
                        entity_type="directus_app_item",
                        identity_prefix=f"directus:item:{collection}",
                        fields=tuple(fields),
                        identity_field=identity_field,
                        sort_field=identity_field,
                    )
                )

        return DirectusInventorySnapshot(
            base_url=self.config.base_url,
            results=tuple(results),
        )

    def _get_items(
        self,
        *,
        collection: str,
        entity_type: str,
        identity_prefix: str,
        fields: tuple[str, ...],
        identity_field: str = "id",
        sort_field: str = "id",
    ) -> DirectusCollectionResult:
        return self._get_paginated(
            endpoint=f"items/{collection}",
            entity_type=entity_type,
            identity_prefix=identity_prefix,
            fields=fields,
            identity_field=identity_field,
            sort_field=sort_field,
        )

    def _get_singleton(
        self,
        *,
        endpoint: str,
        entity_type: str,
        identity: str,
        payload_key: str,
    ) -> DirectusCollectionResult:
        response, payload = self._get_json(endpoint)
        blocked = self._blocked_result(endpoint, response)
        if blocked is not None:
            return blocked

        if not isinstance(payload, Mapping):
            raise DirectusProtocolError(
                "invalid_json_shape",
                f"Directus {endpoint} endpoint must return an object.",
                endpoint=endpoint,
                details={"received_type": type(payload).__name__},
            )
        raw_data = payload.get(payload_key, payload)
        if not isinstance(raw_data, Mapping):
            raise DirectusProtocolError(
                "invalid_json_shape",
                f"Directus {endpoint} payload must contain an object.",
                endpoint=endpoint,
                details={
                    "payload_key": payload_key,
                    "received_type": type(raw_data).__name__,
                },
            )

        return DirectusCollectionResult(
            endpoint=endpoint,
            records=(
                ManifestRecord(
                    scope=InventoryScope.TARGET,
                    entity_type=entity_type,
                    identity=identity,
                    data=dict(raw_data),
                ),
            ),
            issues=(),
            total_items=1,
            total_pages=1,
            raw_item_count=1,
        )

    def _get_system_array(
        self,
        *,
        endpoint: str,
        entity_type: str,
        identity_field: str | None = None,
        identity_prefix: str | None = None,
        identity_builder: Any | None = None,
    ) -> DirectusCollectionResult:
        response, payload = self._get_json(endpoint)
        blocked = self._blocked_result(endpoint, response)
        if blocked is not None:
            return blocked

        items = self._data_array(endpoint, payload)
        records, issues = self._records_from_items(
            endpoint=endpoint,
            raw_items=items,
            entity_type=entity_type,
            identity_prefix=identity_prefix,
            identity_field=identity_field,
            identity_builder=identity_builder,
        )
        return DirectusCollectionResult(
            endpoint=endpoint,
            records=records,
            issues=issues,
            total_items=len(items),
            total_pages=1 if items else 0,
            raw_item_count=len(items),
        )

    def _get_paginated(
        self,
        *,
        endpoint: str,
        entity_type: str,
        identity_prefix: str,
        fields: tuple[str, ...],
        identity_field: str = "id",
        sort_field: str = "id",
    ) -> DirectusCollectionResult:
        first_params = {
            "limit": self.config.limit,
            "offset": 0,
            "sort": sort_field,
            "fields": ",".join(fields),
            "meta": "filter_count,total_count",
        }
        response, payload = self._get_json(endpoint, params=first_params)
        blocked = self._blocked_result(endpoint, response)
        if blocked is not None:
            return blocked

        first_items, total_items = self._paginated_payload(
            endpoint, payload, offset=0
        )
        first_metadata = self._page_metadata(
            endpoint,
            page=1,
            total_items=total_items,
        )
        try:
            pages: list[InventoryPage[Any]] = [
                InventoryPage(first_metadata, first_items)
            ]
        except PaginationError as exc:
            raise DirectusProtocolError(
                "inconsistent_page_size",
                f"Directus page size is inconsistent for {endpoint}: {exc}",
                endpoint=endpoint,
                details={"page": 1, "item_count": len(first_items)},
            ) from exc

        for page_number in range(2, first_metadata.total_pages + 1):
            offset = (page_number - 1) * self.config.limit
            page_params = {**first_params, "offset": offset}
            page_response, page_payload = self._get_json(
                endpoint, params=page_params
            )
            page_blocked = self._blocked_result(endpoint, page_response)
            if page_blocked is not None:
                return _merge_blocked_result(endpoint, pages, page_blocked)
            page_items, page_total_items = self._paginated_payload(
                endpoint, page_payload, offset=offset
            )
            if page_total_items != first_metadata.total_items:
                raise DirectusProtocolError(
                    "incomplete_pagination",
                    f"Directus pagination totals changed for {endpoint}.",
                    endpoint=endpoint,
                    details={
                        "page": page_number,
                        "first_total_items": first_metadata.total_items,
                        "page_total_items": page_total_items,
                    },
                )
            page_metadata = self._page_metadata(
                endpoint,
                page=page_number,
                total_items=page_total_items,
            )
            try:
                pages.append(InventoryPage(page_metadata, page_items))
            except PaginationError as exc:
                raise DirectusProtocolError(
                    "inconsistent_page_size",
                    f"Directus page size is inconsistent for {endpoint}: {exc}",
                    endpoint=endpoint,
                    details={"page": page_number, "item_count": len(page_items)},
                ) from exc

        try:
            raw_items = merge_complete_pages(pages)
        except PaginationError as exc:
            raise DirectusProtocolError(
                "incomplete_pagination",
                f"Directus pagination is incomplete for {endpoint}: {exc}",
                endpoint=endpoint,
                details={"fetched_pages": len(pages)},
            ) from exc

        records, issues = self._records_from_items(
            endpoint=endpoint,
            raw_items=raw_items,
            entity_type=entity_type,
            identity_prefix=identity_prefix,
            identity_field=identity_field,
        )
        return DirectusCollectionResult(
            endpoint=endpoint,
            records=records,
            issues=issues,
            total_items=first_metadata.total_items,
            total_pages=first_metadata.total_pages,
            raw_item_count=len(raw_items),
        )

    def _endpoint_url(self, endpoint: str) -> str:
        normalized = endpoint.strip("/")
        if not normalized or ":" in normalized or normalized.startswith("."):
            raise ValueError(f"Invalid Directus REST endpoint {endpoint!r}.")
        return urljoin(f"{self.config.base_url}/", normalized)

    def _get_json(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> tuple[httpx.Response, Any]:
        url = self._endpoint_url(endpoint)
        try:
            headers = (
                {"Authorization": f"Bearer {self.config.auth_token}"}
                if self.config.auth_token is not None
                else None
            )
            response = self.http.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            request = getattr(exc, "request", None)
            raise DirectusHttpError(
                "directus_transport_error",
                f"Directus request failed for {endpoint}: {type(exc).__name__}.",
                endpoint=endpoint,
                details={
                    "method": getattr(request, "method", "GET"),
                    "url": str(getattr(request, "url", url)),
                },
            ) from exc

        if response.status_code in {401, 403}:
            return response, {}
        if response.status_code >= 400:
            raise DirectusHttpError(
                "directus_http_status",
                f"Directus returned HTTP {response.status_code} for {endpoint}.",
                endpoint=endpoint,
                details={
                    "status_code": response.status_code,
                    "method": response.request.method,
                    "url": str(response.request.url),
                },
            )

        try:
            payload = response.json()
        except (ValueError, UnicodeError) as exc:
            raise DirectusProtocolError(
                "invalid_json",
                f"Directus returned invalid JSON for {endpoint}.",
                endpoint=endpoint,
                details={
                    "status_code": response.status_code,
                    "url": str(response.request.url),
                },
            ) from exc
        return response, payload

    def _blocked_result(
        self, endpoint: str, response: httpx.Response
    ) -> DirectusCollectionResult | None:
        if response.status_code < 400:
            return None
        if response.status_code in {401, 403}:
            return DirectusCollectionResult(
                endpoint=endpoint,
                records=(),
                issues=(
                    InventoryIssue(
                        scope=InventoryScope.TARGET,
                        severity=IssueSeverity.FATAL,
                        code="directus_endpoint_inaccessible",
                        message="Directus endpoint is not readable with the current identity.",
                        details={
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "method": response.request.method,
                            "url": str(response.request.url),
                        },
                    ),
                ),
                total_items=0,
                total_pages=0,
                raw_item_count=0,
            )
        raise DirectusHttpError(
            "directus_http_status",
            f"Directus returned HTTP {response.status_code} for {endpoint}.",
            endpoint=endpoint,
            details={
                "status_code": response.status_code,
                "method": response.request.method,
                "url": str(response.request.url),
            },
        )

    def _data_array(self, endpoint: str, payload: Any) -> tuple[Any, ...]:
        if not isinstance(payload, Mapping):
            raise DirectusProtocolError(
                "invalid_json_shape",
                f"Directus {endpoint} endpoint must return an object.",
                endpoint=endpoint,
                details={"received_type": type(payload).__name__},
            )
        raw_data = payload.get("data")
        if not isinstance(raw_data, list):
            raise DirectusProtocolError(
                "invalid_json_shape",
                f"Directus {endpoint} payload must contain a data array.",
                endpoint=endpoint,
                details={"received_type": type(raw_data).__name__},
            )
        return tuple(raw_data)

    def _paginated_payload(
        self, endpoint: str, payload: Any, *, offset: int
    ) -> tuple[tuple[Any, ...], int]:
        items = self._data_array(endpoint, payload)
        if not isinstance(payload, Mapping):
            raise AssertionError("payload shape checked by _data_array")
        raw_meta = payload.get("meta")
        if not isinstance(raw_meta, Mapping):
            raise DirectusProtocolError(
                "missing_pagination_meta",
                "Directus paginated response is missing meta.",
                endpoint=endpoint,
                details={"offset": offset},
            )
        raw_total = raw_meta.get("filter_count")
        raw_unfiltered_total = raw_meta.get("total_count")
        if isinstance(raw_total, bool) or not isinstance(raw_total, int):
            raise DirectusProtocolError(
                "invalid_pagination_meta",
                "Directus filter_count must be an integer.",
                endpoint=endpoint,
                details={
                    "offset": offset,
                    "filter_count": raw_total,
                },
            )
        if isinstance(raw_unfiltered_total, bool) or not isinstance(
            raw_unfiltered_total, int
        ):
            raise DirectusProtocolError(
                "invalid_pagination_meta",
                "Directus total_count must be an integer.",
                endpoint=endpoint,
                details={
                    "offset": offset,
                    "total_count": raw_unfiltered_total,
                },
            )
        if raw_unfiltered_total != raw_total:
            raise DirectusProtocolError(
                "inconsistent_pagination",
                "Directus total_count and filter_count differ for an unfiltered inventory.",
                endpoint=endpoint,
                details={
                    "offset": offset,
                    "filter_count": raw_total,
                    "total_count": raw_unfiltered_total,
                },
            )
        return items, raw_total

    def _page_metadata(
        self,
        endpoint: str,
        *,
        page: int,
        total_items: int,
    ) -> PageMetadata:
        try:
            return PageMetadata(
                page=page,
                per_page=self.config.limit,
                total_items=total_items,
                total_pages=_total_pages(total_items, self.config.limit),
            )
        except PaginationError as exc:
            raise DirectusProtocolError(
                "inconsistent_pagination",
                f"Directus pagination is inconsistent for {endpoint}: {exc}",
                endpoint=endpoint,
                details={
                    "page": page,
                    "limit": self.config.limit,
                    "total_items": total_items,
                },
            ) from exc

    def _records_from_items(
        self,
        *,
        endpoint: str,
        raw_items: Iterable[Any],
        entity_type: str,
        identity_prefix: str | None,
        identity_field: str | None,
        identity_builder: Any | None = None,
    ) -> tuple[tuple[ManifestRecord, ...], tuple[InventoryIssue, ...]]:
        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = []

        for index, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, Mapping):
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.TARGET,
                        severity=IssueSeverity.ERROR,
                        code="malformed_directus_item",
                        message="Directus item is not an object.",
                        details={
                            "endpoint": endpoint,
                            "index": index,
                            "received_type": type(raw_item).__name__,
                        },
                    )
                )
                continue

            identity = None
            if identity_builder is not None:
                identity = identity_builder(raw_item)
            elif identity_field is not None and identity_prefix is not None:
                raw_identity = raw_item.get(identity_field)
                if raw_identity is not None and raw_identity != "":
                    identity = f"{identity_prefix}:{raw_identity}"

            if identity is None:
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.TARGET,
                        severity=IssueSeverity.ERROR,
                        code="missing_directus_identity",
                        message="Directus item has no stable inventory identity.",
                        details={"endpoint": endpoint, "index": index},
                    )
                )
                continue

            records.append(
                ManifestRecord(
                    scope=InventoryScope.TARGET,
                    entity_type=entity_type,
                    identity=identity,
                    data=dict(raw_item),
                )
            )

        return tuple(records), tuple(issues)


def _total_pages(total_items: int, limit: int) -> int:
    if total_items == 0:
        return 0
    return (total_items + limit - 1) // limit


def _field_identity(item: Mapping[str, Any]) -> str | None:
    collection = item.get("collection")
    field = item.get("field")
    if collection and field:
        return f"directus:field:{collection}.{field}"
    return None


def _relation_identity(item: Mapping[str, Any]) -> str | None:
    collection = item.get("collection")
    field = item.get("field")
    related_collection = item.get("related_collection")
    related_field = item.get("related_field")
    meta = item.get("meta")
    meta_junction_field = None
    meta_one_field = None
    if isinstance(meta, Mapping):
        meta_junction_field = meta.get("junction_field")
        meta_one_field = meta.get("one_field")
    if collection and field:
        suffix = f"{collection}.{field}"
        if related_collection:
            suffix = f"{suffix}->{related_collection}"
            if related_field:
                suffix = f"{suffix}.{related_field}"
            else:
                qualifiers = []
                if meta_junction_field:
                    qualifiers.append(f"junction:{meta_junction_field}")
                if meta_one_field:
                    qualifiers.append(f"one:{meta_one_field}")
                if qualifiers:
                    suffix = f"{suffix}#{','.join(qualifiers)}"
        return f"directus:relation:{suffix}"
    raw_id = item.get("id")
    if raw_id is not None and raw_id != "":
        return f"directus:relation:{raw_id}"
    return None


def _dedupe_identical_relation_records(
    result: DirectusCollectionResult,
) -> DirectusCollectionResult:
    """Collapse exact duplicate Directus system relation rows."""

    seen: dict[str, tuple[ManifestRecord, str]] = {}
    records: list[ManifestRecord] = []
    issues = list(result.issues)

    for record in result.records:
        payload_hash = canonical_sha256(record.data)
        previous = seen.get(record.identity)
        if previous is None:
            seen[record.identity] = (record, payload_hash)
            records.append(record)
            continue

        _, previous_hash = previous
        if previous_hash != payload_hash:
            raise DirectusProtocolError(
                "duplicate_directus_relation_identity",
                "Directus relations endpoint returned different records with the same inventory identity.",
                endpoint=result.endpoint,
                details={"identity": record.identity},
            )

        issues.append(
            InventoryIssue(
                scope=InventoryScope.TARGET,
                severity=IssueSeverity.WARNING,
                code="duplicate_directus_relation_ignored",
                message="Directus relations endpoint returned an exact duplicate relation; inventory kept one copy.",
                details={"endpoint": result.endpoint, "identity": record.identity},
            )
        )

    return DirectusCollectionResult(
        endpoint=result.endpoint,
        records=tuple(records),
        issues=tuple(issues),
        total_items=result.total_items,
        total_pages=result.total_pages,
        raw_item_count=result.raw_item_count,
    )


def _fields_by_collection(
    records: Iterable[ManifestRecord],
) -> dict[str, tuple[str, ...]]:
    fields: dict[str, list[str]] = {}
    for record in records:
        collection = record.data.get("collection")
        field = record.data.get("field")
        if isinstance(collection, str) and isinstance(field, str):
            fields.setdefault(collection, []).append(field)
    return {
        collection: tuple(sorted(set(collection_fields)))
        for collection, collection_fields in fields.items()
    }


def _application_collection_names(
    records: Iterable[ManifestRecord],
    *,
    requested: tuple[str, ...] | None,
) -> tuple[str, ...]:
    available = {
        record.data.get("collection")
        for record in records
        if isinstance(record.data.get("collection"), str)
    }
    if requested:
        names = requested
        reject_system = True
    else:
        names = tuple(
            sorted(
                name
                for name in available
                if not name.startswith(SYSTEM_COLLECTION_PREFIX)
            )
        )
        reject_system = False

    normalized: list[str] = []
    for name in names:
        if not VALID_COLLECTION_NAME.fullmatch(name):
            raise ValueError(f"Invalid Directus collection name {name!r}.")
        if reject_system and name.startswith(SYSTEM_COLLECTION_PREFIX):
            raise ValueError(f"System Directus collection is not application data: {name}.")
        if name not in available:
            raise ValueError(f"Directus collection is not readable or does not exist: {name}.")
        normalized.append(name)
    return tuple(dict.fromkeys(normalized))


def _singleton_collection_names(records: Iterable[ManifestRecord]) -> set[str]:
    singleton_names: set[str] = set()
    for record in records:
        collection = record.data.get("collection")
        meta = record.data.get("meta")
        if (
            isinstance(collection, str)
            and isinstance(meta, Mapping)
            and meta.get("singleton") is True
        ):
            singleton_names.add(collection)
    return singleton_names


def _application_identity_field(collection: str, fields: tuple[str, ...]) -> str:
    field_set = set(fields)
    for candidate in APPLICATION_IDENTITY_FIELDS:
        if candidate in field_set:
            return candidate
    raise DirectusProtocolError(
        "missing_directus_application_identity",
        "Directus application collection has no supported stable identity field.",
        endpoint=f"items/{collection}",
        details={
            "collection": collection,
            "supported_identity_fields": APPLICATION_IDENTITY_FIELDS,
        },
    )


def _merge_blocked_result(
    endpoint: str,
    pages: list[InventoryPage[Any]],
    blocked: DirectusCollectionResult,
) -> DirectusCollectionResult:
    fetched_items = tuple(item for page in pages for item in page.items)
    issue = InventoryIssue(
        scope=InventoryScope.TARGET,
        severity=IssueSeverity.FATAL,
        code="directus_page_inaccessible",
        message="Directus pagination became inaccessible before all pages were fetched.",
        details={
            "endpoint": endpoint,
            "fetched_pages": len(pages),
            "fetched_items": len(fetched_items),
            "blocked_endpoint": blocked.endpoint,
        },
    )
    return DirectusCollectionResult(
        endpoint=endpoint,
        records=(),
        issues=(issue, *blocked.issues),
        total_items=0,
        total_pages=0,
        raw_item_count=len(fetched_items),
    )
