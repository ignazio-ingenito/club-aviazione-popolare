"""Fresh read-only WordPress REST inventory client."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .errors import InventoryContractError, ResponseContractError
from .manifest import InventoryManifest
from .pagination import PageResult, PaginationAccumulator, wordpress_page_meta
from .readonly_http import ReadOnlyHttpClient
from .records import InventoryIssue, ManifestRecord

RecordMapper = Callable[[Mapping[str, Any], datetime], ManifestRecord]


def _required_id(item: Mapping[str, Any]) -> str:
    value = item.get("id")
    if value is None or isinstance(value, bool):
        raise ResponseContractError("WordPress item is missing a valid id.")
    text = str(value).strip()
    if not text:
        raise ResponseContractError("WordPress item id is empty.")
    return text


def _required_url(item: Mapping[str, Any], field: str = "link") -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ResponseContractError(f"WordPress item is missing {field}.")
    return value.strip()


def _rendered(item: Mapping[str, Any], field: str) -> str | None:
    value = item.get(field)
    if not isinstance(value, Mapping):
        return None
    rendered = value.get("rendered")
    return rendered if isinstance(rendered, str) else None


def _sorted_integer_ids(value: Any) -> list[int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    ids: set[int] = set()
    for item in value:
        if isinstance(item, bool):
            continue
        try:
            ids.add(int(item))
        except (TypeError, ValueError):
            continue
    return sorted(ids)


def _ordered_unique(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _absolute_url(site_url: str, value: str) -> str:
    return urljoin(site_url.rstrip("/") + "/", value.strip())


def _srcset_urls(value: str) -> list[str]:
    urls: list[str] = []
    for candidate in value.split(","):
        token = candidate.strip().split()
        if token:
            urls.append(token[0])
    return urls


def extract_content_media_urls(html: str | None, site_url: str) -> dict[str, list[str]]:
    """Extract ordered image and file-link URLs without changing article HTML."""

    if not html:
        return {"image_urls": [], "linked_media_urls": []}

    soup = BeautifulSoup(html, "html.parser")
    images: list[str] = []
    links: list[str] = []

    for tag in soup.select("img[src], source[src]"):
        src = tag.attrs.get("src")
        if isinstance(src, str) and src.strip():
            images.append(_absolute_url(site_url, src))

    for tag in soup.select("img[srcset], source[srcset]"):
        srcset = tag.attrs.get("srcset")
        if isinstance(srcset, str):
            images.extend(_absolute_url(site_url, url) for url in _srcset_urls(srcset))

    for tag in soup.select("a[href]"):
        href = tag.attrs.get("href")
        if not isinstance(href, str) or not href.strip():
            continue
        absolute = _absolute_url(site_url, href)
        path = urlparse(absolute).path
        if "/wp-content/uploads/" in path or Path(path).suffix:
            links.append(absolute)

    return {
        "image_urls": _ordered_unique(images),
        "linked_media_urls": _ordered_unique(links),
    }


def _featured_media(post: Mapping[str, Any]) -> dict[str, Any] | None:
    embedded = post.get("_embedded")
    if not isinstance(embedded, Mapping):
        return None
    candidates = embedded.get("wp:featuredmedia")
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        return None
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            return {
                "id": candidate.get("id"),
                "source_url": candidate.get("source_url"),
                "alt_text": candidate.get("alt_text"),
                "mime_type": candidate.get("mime_type"),
                "media_type": candidate.get("media_type"),
            }
    return None


@dataclass(frozen=True, slots=True)
class InventoryBatch:
    name: str
    records: tuple[ManifestRecord, ...]
    issues: tuple[InventoryIssue, ...]
    total_items: int


class WordPressInventoryClient:
    """Inventory WordPress through public GET requests with no implicit cache."""

    def __init__(
        self,
        site_url: str,
        *,
        per_page: int = 100,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if per_page < 1 or per_page > 100:
            raise ValueError("per_page must be between 1 and 100 for WordPress REST.")
        parsed = httpx.URL(site_url)
        if parsed.scheme not in {"http", "https"} or not parsed.host:
            raise ValueError("site_url must be an absolute HTTP(S) URL.")
        if parsed.username or parsed.password:
            raise ValueError("Credentials must not be embedded in site_url.")

        self.site_url = str(parsed.copy_with(query=None, fragment=None)).rstrip("/")
        self.api_url = urljoin(self.site_url + "/", "wp-json/wp/v2/")
        self.per_page = per_page
        self.http = ReadOnlyHttpClient(
            base_url=self.api_url,
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> "WordPressInventoryClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _paginated_items(
        self,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> tuple[Any, ...]:
        base_params = dict(params or {})
        base_params.pop("page", None)
        base_params.pop("per_page", None)

        first_response, first_payload = self.http.get_json(
            endpoint,
            params={**base_params, "page": 1, "per_page": self.per_page},
        )
        if not isinstance(first_payload, list):
            raise ResponseContractError(
                f"WordPress collection {endpoint} did not return a JSON array."
            )

        first_meta = wordpress_page_meta(
            page=1,
            per_page=self.per_page,
            headers=first_response.headers,
        )
        accumulator: PaginationAccumulator[Any] = PaginationAccumulator()
        accumulator.add(PageResult(first_meta, first_payload))

        for page in range(2, first_meta.total_pages + 1):
            response, payload = self.http.get_json(
                endpoint,
                params={**base_params, "page": page, "per_page": self.per_page},
            )
            if not isinstance(payload, list):
                raise ResponseContractError(
                    f"WordPress collection {endpoint} page {page} is not a JSON array."
                )
            meta = wordpress_page_meta(
                page=page,
                per_page=self.per_page,
                headers=response.headers,
            )
            accumulator.add(PageResult(meta, payload))

        return accumulator.items()

    def _map_batch(
        self,
        *,
        name: str,
        object_type: str,
        items: Sequence[Any],
        observed_at: datetime,
        mapper: RecordMapper,
    ) -> InventoryBatch:
        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = []

        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                issues.append(
                    InventoryIssue(
                        object_ref=f"wordpress:{object_type}:index-{index}",
                        code="invalid_record_shape",
                        message="WordPress collection item is not a JSON object.",
                    )
                )
                continue
            try:
                records.append(mapper(item, observed_at))
            except (InventoryContractError, TypeError, ValueError) as exc:
                raw_id = item.get("id")
                object_id = str(raw_id) if raw_id is not None else f"index-{index}"
                issues.append(
                    InventoryIssue(
                        object_ref=f"wordpress:{object_type}:{object_id}",
                        code="invalid_source_record",
                        message=str(exc),
                    )
                )

        return InventoryBatch(
            name=name,
            records=tuple(records),
            issues=tuple(issues),
            total_items=len(items),
        )

    def fetch_post_types(self, *, observed_at: datetime) -> InventoryBatch:
        _, payload = self.http.get_json("types")
        if not isinstance(payload, Mapping):
            raise ResponseContractError("WordPress types endpoint is not a JSON object.")

        items: list[Mapping[str, Any]] = []
        issues: list[InventoryIssue] = []
        for type_key in sorted(str(key) for key in payload.keys()):
            item = payload.get(type_key)
            if not isinstance(item, Mapping):
                issues.append(
                    InventoryIssue(
                        object_ref=f"wordpress:post_type:{type_key}",
                        code="invalid_record_shape",
                        message="WordPress post type is not a JSON object.",
                    )
                )
                continue
            items.append({"_type_key": type_key, **dict(item)})

        batch = self._map_batch(
            name="post_types",
            object_type="post_type",
            items=items,
            observed_at=observed_at,
            mapper=self._post_type_record,
        )
        return InventoryBatch(
            name=batch.name,
            records=batch.records,
            issues=tuple([*issues, *batch.issues]),
            total_items=len(payload),
        )

    def fetch_categories(self, *, observed_at: datetime) -> InventoryBatch:
        items = self._paginated_items(
            "categories",
            params={"context": "view", "orderby": "id", "order": "asc"},
        )
        return self._map_batch(
            name="categories",
            object_type="category",
            items=items,
            observed_at=observed_at,
            mapper=self._category_record,
        )

    def fetch_posts(self, *, observed_at: datetime) -> InventoryBatch:
        items = self._paginated_items(
            "posts",
            params={
                "context": "view",
                "status": "publish",
                "orderby": "id",
                "order": "asc",
                "_embed": "true",
            },
        )
        return self._map_batch(
            name="posts",
            object_type="post",
            items=items,
            observed_at=observed_at,
            mapper=self._post_record,
        )

    def fetch_media(self, *, observed_at: datetime) -> InventoryBatch:
        items = self._paginated_items(
            "media",
            params={"context": "view", "orderby": "id", "order": "asc"},
        )
        return self._map_batch(
            name="media",
            object_type="media",
            items=items,
            observed_at=observed_at,
            mapper=self._media_record,
        )

    def build_manifest(
        self, *, environment: str, observed_at: datetime | None = None
    ) -> InventoryManifest:
        at = observed_at or datetime.now(timezone.utc)
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware.")

        batches = (
            self.fetch_post_types(observed_at=at),
            self.fetch_categories(observed_at=at),
            self.fetch_posts(observed_at=at),
            self.fetch_media(observed_at=at),
        )
        records = tuple(record for batch in batches for record in batch.records)
        issues = tuple(issue for batch in batches for issue in batch.issues)
        counts = {batch.name: batch.total_items for batch in batches}

        return InventoryManifest(
            manifest_type="wordpress_source",
            environment=environment,
            base_url=self.site_url,
            observed_at=at,
            records=records,
            issues=issues,
            metadata={
                "api_url": self.api_url,
                "per_page": self.per_page,
                "collection_counts": counts,
            },
        )

    def _post_type_record(
        self, item: Mapping[str, Any], observed_at: datetime
    ) -> ManifestRecord:
        type_key = item.get("_type_key")
        if not isinstance(type_key, str) or not type_key.strip():
            raise ResponseContractError("WordPress post type key is missing.")
        payload = {
            "name": item.get("name"),
            "slug": item.get("slug"),
            "description": item.get("description"),
            "hierarchical": item.get("hierarchical"),
            "rest_base": item.get("rest_base"),
            "rest_namespace": item.get("rest_namespace"),
            "taxonomies": item.get("taxonomies", []),
            "supports": item.get("supports", {}),
        }
        return ManifestRecord(
            system="wordpress",
            object_type="post_type",
            object_id=type_key,
            observed_at=observed_at,
            payload=payload,
        )

    def _category_record(
        self, item: Mapping[str, Any], observed_at: datetime
    ) -> ManifestRecord:
        object_id = _required_id(item)
        return ManifestRecord(
            system="wordpress",
            object_type="category",
            object_id=object_id,
            canonical_url=_required_url(item),
            observed_at=observed_at,
            payload={
                "name": item.get("name"),
                "slug": item.get("slug"),
                "description": item.get("description"),
                "parent": item.get("parent"),
                "count": item.get("count"),
                "taxonomy": item.get("taxonomy"),
            },
        )

    def _post_record(
        self, item: Mapping[str, Any], observed_at: datetime
    ) -> ManifestRecord:
        object_id = _required_id(item)
        content = _rendered(item, "content")
        media_urls = extract_content_media_urls(content, self.site_url)
        guid = item.get("guid")
        guid_rendered = guid.get("rendered") if isinstance(guid, Mapping) else None

        return ManifestRecord(
            system="wordpress",
            object_type=str(item.get("type") or "post"),
            object_id=object_id,
            canonical_url=_required_url(item),
            observed_at=observed_at,
            payload={
                "date": item.get("date"),
                "date_gmt": item.get("date_gmt"),
                "modified": item.get("modified"),
                "modified_gmt": item.get("modified_gmt"),
                "guid": guid_rendered,
                "slug": item.get("slug"),
                "status": item.get("status"),
                "type": item.get("type"),
                "title": _rendered(item, "title"),
                "excerpt": _rendered(item, "excerpt"),
                "content": content,
                "author": item.get("author"),
                "featured_media_id": item.get("featured_media"),
                "featured_media": _featured_media(item),
                "categories": _sorted_integer_ids(item.get("categories")),
                "tags": _sorted_integer_ids(item.get("tags")),
                **media_urls,
            },
        )

    def _media_record(
        self, item: Mapping[str, Any], observed_at: datetime
    ) -> ManifestRecord:
        object_id = _required_id(item)
        description = item.get("description")
        return ManifestRecord(
            system="wordpress",
            object_type="media",
            object_id=object_id,
            canonical_url=_required_url(item),
            observed_at=observed_at,
            payload={
                "date": item.get("date"),
                "date_gmt": item.get("date_gmt"),
                "modified": item.get("modified"),
                "modified_gmt": item.get("modified_gmt"),
                "slug": item.get("slug"),
                "status": item.get("status"),
                "type": item.get("type"),
                "title": _rendered(item, "title"),
                "author": item.get("author"),
                "caption": _rendered(item, "caption"),
                "description": (
                    description.get("rendered")
                    if isinstance(description, Mapping)
                    else None
                ),
                "alt_text": item.get("alt_text"),
                "media_type": item.get("media_type"),
                "mime_type": item.get("mime_type"),
                "source_url": item.get("source_url"),
                "media_details": item.get("media_details", {}),
                "parent_post_id": item.get("post"),
            },
        )
