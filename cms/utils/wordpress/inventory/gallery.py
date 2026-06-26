"""Read-only WordPress gallery discovery with REST-first HTML fallback."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from .http import ReadOnlyHttpClient
from .models import (
    InventoryIssue,
    InventoryManifest,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
)
from .wordpress import (
    WordPressCollectionResult,
    WordPressHttpError,
    WordPressInventoryClient,
    WordPressInventoryConfig,
    WordPressInventorySnapshot,
)


GALLERY_ARCHIVE_PATH = "gallery/"
GALLERY_ROUTE_MARKER = "/dt-gallery/"
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif")


@dataclass(frozen=True, slots=True)
class GalleryDiscoveryResult:
    """Result of one gallery discovery pass."""

    result: WordPressCollectionResult
    method: str
    rest_endpoint: str | None

    def to_snapshot(self, *, base_url: str) -> WordPressInventorySnapshot:
        return WordPressInventorySnapshot(base_url=base_url, results=(self.result,))

    def to_manifest(
        self,
        *,
        base_url: str,
        environment: str,
        observed_at: datetime,
        metadata: Mapping[str, Any] | None = None,
    ) -> InventoryManifest:
        return self.to_snapshot(base_url=base_url).to_manifest(
            environment=environment,
            observed_at=observed_at,
            metadata={
                "gallery_discovery_method": self.method,
                "gallery_rest_endpoint": self.rest_endpoint,
                **dict(metadata or {}),
            },
        )


class WordPressGalleryDiscoveryClient:
    """Discover WordPress galleries without cache or write-capable requests."""

    def __init__(
        self,
        *,
        config: WordPressInventoryConfig | None = None,
        http: ReadOnlyHttpClient | None = None,
    ) -> None:
        self.config = config or WordPressInventoryConfig()
        self._owns_http = http is None
        self.http = http or ReadOnlyHttpClient()
        self._wordpress = WordPressInventoryClient(config=self.config, http=self.http)

    def close(self) -> None:
        if self._owns_http:
            self.http.close()

    def __enter__(self) -> "WordPressGalleryDiscoveryClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def discover(self) -> GalleryDiscoveryResult:
        """Use exposed REST gallery types first, then public HTML fallback."""

        types = self._wordpress.get_types()
        endpoint = self._gallery_rest_endpoint(types.records)
        if endpoint is not None:
            return GalleryDiscoveryResult(
                result=self._discover_rest(endpoint),
                method="rest",
                rest_endpoint=endpoint,
            )

        result = self.discover_public_html()
        issues = (
            InventoryIssue(
                scope=InventoryScope.SOURCE,
                severity=IssueSeverity.WARNING,
                code="gallery_rest_type_not_exposed",
                message="No exposed WordPress REST type was identified for dt-gallery.",
                details={"types_count": len(types.records)},
            ),
            *types.issues,
            *result.result.issues,
        )
        merged_result = WordPressCollectionResult(
            endpoint=result.result.endpoint,
            records=result.result.records,
            issues=issues,
            total_items=result.result.total_items,
            total_pages=result.result.total_pages,
            raw_item_count=result.result.raw_item_count,
        )
        return GalleryDiscoveryResult(
            result=merged_result,
            method="public_html",
            rest_endpoint=None,
        )

    def discover_public_html(self) -> GalleryDiscoveryResult:
        archive_url = urljoin(f"{self.config.base_url}/", GALLERY_ARCHIVE_PATH)
        archive_html = self._get_html(archive_url, endpoint="gallery_archive")
        album_links, archive_issues = self._album_links_from_archive(
            archive_html, archive_url=archive_url
        )

        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = list(archive_issues)
        for position, album in enumerate(album_links, start=1):
            try:
                album_html = self._get_html(album["url"], endpoint="gallery_album")
            except WordPressHttpError as exc:
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.SOURCE,
                        severity=IssueSeverity.ERROR,
                        code="gallery_album_fetch_failed",
                        message="Gallery album page could not be fetched.",
                        entity_type="wordpress_gallery_album",
                        identity=f"wordpress:gallery:{album['slug']}",
                        details={"url": album["url"], "error": exc.code},
                    )
                )
                images: list[dict[str, Any]] = []
            else:
                images = self._images_from_album(album_html, album_url=album["url"])
                if not images:
                    issues.append(
                        InventoryIssue(
                            scope=InventoryScope.SOURCE,
                            severity=IssueSeverity.ERROR,
                            code="gallery_album_has_no_images",
                            message="Gallery album page did not expose image entries.",
                            entity_type="wordpress_gallery_album",
                            identity=f"wordpress:gallery:{album['slug']}",
                            details={"url": album["url"]},
                        )
                    )

            records.append(
                ManifestRecord(
                    scope=InventoryScope.SOURCE,
                    entity_type="wordpress_gallery_album",
                    identity=f"wordpress:gallery:{album['slug']}",
                    source_url=album["url"],
                    data={
                        "discovery_method": "public_html",
                        "order": position,
                        "slug": album["slug"],
                        "title": album["title"],
                        "url": album["url"],
                        "cover_url": album["cover_url"],
                        "images": images,
                    },
                )
            )

        result = WordPressCollectionResult(
            endpoint="gallery_archive",
            records=tuple(records),
            issues=tuple(issues),
            total_items=len(album_links),
            total_pages=1 if album_links else 0,
            raw_item_count=len(album_links),
        )
        return GalleryDiscoveryResult(
            result=result,
            method="public_html",
            rest_endpoint=None,
        )

    def _discover_rest(self, endpoint: str) -> WordPressCollectionResult:
        result = self._wordpress._get_paginated(
            endpoint=endpoint,
            entity_type="wordpress_gallery_album",
            identity_prefix="wordpress:gallery",
            source_url_fields=("link",),
            params={"orderby": "id", "order": "asc", "_embed": "1"},
        )
        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = list(result.issues)
        for position, record in enumerate(result.records, start=1):
            raw_data = dict(record.data)
            slug = str(raw_data.get("slug") or raw_data.get("id")).strip()
            images = self._images_from_rendered_content(raw_data, record.source_url)
            if not images and record.source_url:
                try:
                    album_html = self._get_html(record.source_url, endpoint="gallery_album_rest_html_fallback")
                except WordPressHttpError as exc:
                    issues.append(
                        InventoryIssue(
                            scope=InventoryScope.SOURCE,
                            severity=IssueSeverity.ERROR,
                            code="gallery_rest_html_fallback_failed",
                            message="REST gallery did not expose images and public album HTML could not be fetched.",
                            entity_type="wordpress_gallery_album",
                            identity=record.identity,
                            details={"url": record.source_url, "error": exc.code},
                        )
                    )
                else:
                    images = self._images_from_album(album_html, album_url=record.source_url)
                    if images:
                        issues.append(
                            InventoryIssue(
                                scope=InventoryScope.SOURCE,
                                severity=IssueSeverity.WARNING,
                                code="gallery_images_enriched_from_public_html",
                                message="REST gallery record did not expose images; public HTML was used for image order.",
                                entity_type="wordpress_gallery_album",
                                identity=record.identity,
                                details={"url": record.source_url, "image_count": len(images)},
                            )
                        )
            if not images:
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.SOURCE,
                        severity=IssueSeverity.ERROR,
                        code="gallery_album_has_no_images",
                        message="Gallery album did not expose image entries through REST content or public HTML.",
                        entity_type="wordpress_gallery_album",
                        identity=record.identity,
                        details={"url": record.source_url},
                    )
                )
            records.append(
                ManifestRecord(
                    scope=InventoryScope.SOURCE,
                    entity_type="wordpress_gallery_album",
                    identity=record.identity,
                    source_url=record.source_url,
                    data={
                        **raw_data,
                        "discovery_method": "rest",
                        "order": position,
                        "slug": slug,
                        "images": images,
                    },
                )
            )
        return WordPressCollectionResult(
            endpoint=endpoint,
            records=tuple(records),
            issues=tuple(issues),
            total_items=result.total_items,
            total_pages=result.total_pages,
            raw_item_count=result.raw_item_count,
        )

    def _gallery_rest_endpoint(self, records: tuple[ManifestRecord, ...]) -> str | None:
        for record in records:
            raw_data = dict(record.data)
            slug = str(raw_data.get("slug") or "").strip()
            rest_base = str(raw_data.get("rest_base") or "").strip("/")
            name = str(raw_data.get("name") or "").lower()
            description = str(raw_data.get("description") or "").lower()
            rewrite = raw_data.get("rewrite")
            route_base = ""
            if isinstance(rewrite, Mapping):
                route_base = str(rewrite.get("slug") or "").strip("/")
            if (
                slug in {"dt_gallery", "dt-gallery", "gallery"}
                or rest_base in {"dt-gallery", "dt_gallery", "gallery"}
                or route_base == "dt-gallery"
                or "gallery" in name
                or "gallery" in description
            ):
                return rest_base or slug
        return None

    def _get_html(self, url: str, *, endpoint: str) -> str:
        try:
            response = self.http.get(url, headers={"Accept": "text/html"})
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

        return response.text

    def _album_links_from_archive(
        self, html: str, *, archive_url: str
    ) -> tuple[list[dict[str, str | None]], list[InventoryIssue]]:
        soup = BeautifulSoup(html, "html.parser")
        seen: set[str] = set()
        albums: list[dict[str, str | None]] = []
        issues: list[InventoryIssue] = []

        for anchor in soup.find_all("a", href=True):
            href = str(anchor.get("href") or "").strip()
            album_url = urljoin(archive_url, href)
            parsed = urlparse(album_url)
            if GALLERY_ROUTE_MARKER not in parsed.path:
                continue
            slug = _slug_from_gallery_url(album_url)
            if not slug or slug in seen:
                continue
            seen.add(slug)
            image = anchor.find("img")
            albums.append(
                {
                    "slug": slug,
                    "url": album_url,
                    "title": _album_title(anchor, image, slug),
                    "cover_url": _absolute_attr_url(image, archive_url, "src")
                    if image is not None
                    else None,
                }
            )

        if not albums:
            issues.append(
                InventoryIssue(
                    scope=InventoryScope.SOURCE,
                    severity=IssueSeverity.ERROR,
                    code="gallery_archive_has_no_albums",
                    message="Gallery archive did not expose /dt-gallery/ album links.",
                    details={"url": archive_url},
                )
            )

        return albums, issues

    def _images_from_rendered_content(
        self, raw_data: Mapping[str, Any], source_url: str | None
    ) -> list[dict[str, Any]]:
        content = raw_data.get("content")
        if not isinstance(content, Mapping):
            return []
        rendered = content.get("rendered")
        if not isinstance(rendered, str) or not rendered:
            return []
        return self._images_from_album(rendered, album_url=source_url or self.config.base_url)

    def _images_from_album(self, html: str, *, album_url: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("article.type-dt_gallery, article.dt_gallery")
        search_root = container if isinstance(container, Tag) else soup
        images: list[dict[str, Any]] = []

        for image in search_root.find_all("img"):
            if not isinstance(image, Tag):
                continue
            thumbnail_url = _absolute_attr_url(image, album_url, "src")
            source_url = self._source_url_for_image(image, album_url, thumbnail_url)
            if source_url is None:
                continue
            images.append(
                {
                    "order": len(images) + 1,
                    "source_url": source_url,
                    "thumbnail_url": thumbnail_url,
                    "alt": _clean_text(str(image.get("alt") or "")) or None,
                    "title": _clean_text(str(image.get("title") or "")) or None,
                    "caption": _caption_for_image(image),
                    "link_url": _nearest_anchor_url(image, album_url),
                }
            )

        return images

    def _source_url_for_image(
        self, image: Tag, album_url: str, thumbnail_url: str | None
    ) -> str | None:
        anchor_url = _nearest_anchor_url(image, album_url)
        if anchor_url and _looks_like_image_url(anchor_url):
            return anchor_url
        if thumbnail_url and _looks_like_image_url(thumbnail_url):
            return thumbnail_url
        return None


def _absolute_attr_url(tag: Tag | None, base_url: str, attr: str) -> str | None:
    if tag is None:
        return None
    raw_value = str(tag.get(attr) or "").strip()
    if not raw_value:
        return None
    return urljoin(base_url, raw_value).rstrip("/")


def _nearest_anchor_url(tag: Tag, base_url: str) -> str | None:
    anchor = tag.find_parent("a", href=True)
    if not isinstance(anchor, Tag):
        return None
    return _absolute_attr_url(anchor, base_url, "href")


def _looks_like_image_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(IMAGE_EXTENSIONS) or "/wp-content/uploads/" in path


def _slug_from_gallery_url(url: str) -> str | None:
    path_parts = [part for part in urlparse(url).path.split("/") if part]
    try:
        marker_index = path_parts.index("dt-gallery")
    except ValueError:
        return None
    if marker_index + 1 >= len(path_parts):
        return None
    return path_parts[marker_index + 1].strip() or None


def _album_title(anchor: Tag, image: Tag | None, slug: str) -> str:
    text = _clean_text(anchor.get_text(" ", strip=True))
    if text:
        return text
    if image is not None:
        alt = _clean_text(str(image.get("alt") or ""))
        if alt:
            return alt
        title = _clean_text(str(image.get("title") or ""))
        if title:
            return title
    return slug.replace("-", " ")


def _caption_for_image(image: Tag) -> str | None:
    caption_container = image.find_parent("figure")
    if isinstance(caption_container, Tag):
        caption = caption_container.find("figcaption")
        if isinstance(caption, Tag):
            return _clean_text(caption.get_text(" ", strip=True)) or None
    return None


def _clean_text(value: str) -> str:
    return " ".join(value.split())
