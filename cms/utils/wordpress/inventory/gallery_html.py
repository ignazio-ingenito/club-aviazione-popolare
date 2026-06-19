"""Ordered public-HTML fallback for WordPress gallery albums."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from .errors import InventoryContractError, ResponseContractError
from .gallery_models import GalleryAlbum, GalleryArchiveEntry, GalleryImage
from .manifest import InventoryManifest
from .readonly_http import ReadOnlyHttpClient
from .records import InventoryIssue

_IMAGE_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
_GENERIC_TITLES = {"", "gallery", "image", "view album", "album"}


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def _absolute_url(site_url: str, value: str) -> str:
    return urljoin(site_url.rstrip("/") + "/", value.strip())


def _gallery_slug(url: str) -> str | None:
    path = unquote(urlparse(url).path)
    match = re.search(r"/dt-gallery/([^/]+)/?$", path, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _is_upload_image(url: str) -> bool:
    path = unquote(urlparse(url).path)
    return "/wp-content/uploads/" in path and Path(path).suffix.lower() in _IMAGE_EXTENSIONS


def _tag_url(tag: Tag, site_url: str) -> str | None:
    for attribute in ("data-lazy-src", "data-src", "src"):
        value = tag.attrs.get(attribute)
        if isinstance(value, str) and value.strip():
            return _absolute_url(site_url, value)
    return None


def _nearest_content_container(tag: Tag) -> Tag:
    for parent in tag.parents:
        if not isinstance(parent, Tag):
            continue
        classes = " ".join(parent.get("class", []))
        if parent.name == "article" or re.search(
            r"gallery|entry|post|album", classes, flags=re.IGNORECASE
        ):
            return parent
    return tag.parent if isinstance(tag.parent, Tag) else tag


def _heading_text(container: Tag) -> str:
    heading = container.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    return _clean_text(heading.get_text(" ", strip=True)) if isinstance(heading, Tag) else ""


def _published_at(container: Tag) -> str | None:
    time_tag = container.find("time")
    if isinstance(time_tag, Tag):
        value = time_tag.attrs.get("datetime")
        if isinstance(value, str) and value.strip():
            return value.strip()
    meta = container.find("meta", attrs={"property": "article:published_time"})
    if isinstance(meta, Tag):
        value = meta.attrs.get("content")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _cover_url(container: Tag, site_url: str) -> str | None:
    for anchor in container.find_all("a", href=True):
        href = anchor.attrs.get("href")
        if isinstance(href, str):
            absolute = _absolute_url(site_url, href)
            if _is_upload_image(absolute):
                return absolute
    for image in container.find_all("img"):
        candidate = _tag_url(image, site_url)
        if candidate and _is_upload_image(candidate):
            return candidate
    return None


def parse_gallery_archive(html: str, site_url: str) -> tuple[GalleryArchiveEntry, ...]:
    """Parse unique album cards in document order from the public archive."""

    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("main, #main, .site-main, .content-area") or soup
    entries: dict[str, dict[str, Any]] = {}

    for anchor in root.find_all("a", href=True):
        href = anchor.attrs.get("href")
        if not isinstance(href, str) or not href.strip():
            continue
        absolute = _absolute_url(site_url, href)
        slug = _gallery_slug(absolute)
        if not slug:
            continue

        container = _nearest_content_container(anchor)
        anchor_title = _clean_text(anchor.get_text(" ", strip=True))
        title = anchor_title
        if title.lower() in _GENERIC_TITLES:
            title = _heading_text(container)
        if not title:
            title = slug.replace("-", " ")

        existing = entries.get(absolute)
        if existing is None:
            entries[absolute] = {
                "slug": slug,
                "url": absolute,
                "title": title,
                "position": len(entries),
                "cover_url": _cover_url(container, site_url),
                "published_at": _published_at(container),
            }
            continue

        if existing["title"].lower() in _GENERIC_TITLES and title:
            existing["title"] = title
        if existing["cover_url"] is None:
            existing["cover_url"] = _cover_url(container, site_url)
        if existing["published_at"] is None:
            existing["published_at"] = _published_at(container)

    if not entries:
        raise ResponseContractError("No /dt-gallery/ album links were found in the archive.")

    return tuple(GalleryArchiveEntry(**entry) for entry in entries.values())


def _candidate_containers(soup: BeautifulSoup) -> tuple[Tag, ...]:
    selectors = (
        ".entry-content",
        ".photo-scroller",
        ".dt-gallery",
        ".gallery",
        "[class*='gallery']",
        "article",
        "main",
        "#main",
        ".site-main",
    )
    result: list[Tag] = []
    seen: set[int] = set()
    for selector in selectors:
        for candidate in soup.select(selector):
            if not isinstance(candidate, Tag) or id(candidate) in seen:
                continue
            seen.add(id(candidate))
            result.append(candidate)
    return tuple(result)


def _upload_urls(container: Tag, site_url: str) -> tuple[str, ...]:
    urls: list[str] = []
    for anchor in container.find_all("a", href=True):
        href = anchor.attrs.get("href")
        if isinstance(href, str):
            candidate = _absolute_url(site_url, href)
            if _is_upload_image(candidate):
                urls.append(candidate)
    for image in container.find_all("img"):
        candidate = _tag_url(image, site_url)
        if candidate and _is_upload_image(candidate):
            urls.append(candidate)
    return tuple(dict.fromkeys(urls))


def _album_container(soup: BeautifulSoup, site_url: str) -> Tag:
    candidates = _candidate_containers(soup)
    if not candidates:
        return soup
    ranked = sorted(
        candidates,
        key=lambda candidate: (
            -len(_upload_urls(candidate, site_url)),
            len(candidate.find_all(True)),
        ),
    )
    return ranked[0]


def _image_title(anchor: Tag, image: Tag | None) -> str | None:
    if image is not None:
        for attribute in ("title", "alt"):
            value = image.attrs.get(attribute)
            if isinstance(value, str) and _clean_text(value):
                return _clean_text(value)
    for attribute in ("data-title", "title"):
        value = anchor.attrs.get(attribute)
        if isinstance(value, str) and _clean_text(value):
            return _clean_text(value)
    sibling = anchor.find_next_sibling(["h3", "h4", "h5", "h6"])
    if isinstance(sibling, Tag):
        text = _clean_text(sibling.get_text(" ", strip=True))
        return text or None
    return None


def _image_caption(anchor: Tag) -> str | None:
    figure = anchor.find_parent("figure")
    if isinstance(figure, Tag):
        caption = figure.find("figcaption")
        if isinstance(caption, Tag):
            text = _clean_text(caption.get_text(" ", strip=True))
            return text or None
    return None


def _ordered_anchor_images(container: Tag, site_url: str) -> list[GalleryImage]:
    images: list[GalleryImage] = []
    seen: set[str] = set()
    for anchor in container.find_all("a", href=True):
        href = anchor.attrs.get("href")
        if not isinstance(href, str):
            continue
        original = _absolute_url(site_url, href)
        if not _is_upload_image(original) or original in seen:
            continue
        seen.add(original)
        image = anchor.find("img")
        thumbnail = _tag_url(image, site_url) if isinstance(image, Tag) else None
        alt = None
        if isinstance(image, Tag):
            value = image.attrs.get("alt")
            alt = _clean_text(value) if isinstance(value, str) else None
        images.append(
            GalleryImage(
                position=len(images),
                original_url=original,
                thumbnail_url=thumbnail,
                title=_image_title(anchor, image if isinstance(image, Tag) else None),
                alt_text=alt or None,
                caption=_image_caption(anchor),
            )
        )
    return images


def _ordered_standalone_images(container: Tag, site_url: str) -> list[GalleryImage]:
    images: list[GalleryImage] = []
    seen: set[str] = set()
    for image in container.find_all("img"):
        source = _tag_url(image, site_url)
        if not source or not _is_upload_image(source) or source in seen:
            continue
        seen.add(source)
        alt_value = image.attrs.get("alt")
        title_value = image.attrs.get("title")
        images.append(
            GalleryImage(
                position=len(images),
                original_url=source,
                thumbnail_url=source,
                title=(
                    _clean_text(title_value)
                    if isinstance(title_value, str) and _clean_text(title_value)
                    else None
                ),
                alt_text=(
                    _clean_text(alt_value)
                    if isinstance(alt_value, str) and _clean_text(alt_value)
                    else None
                ),
            )
        )
    return images


def parse_gallery_album(html: str, album_url: str) -> GalleryAlbum:
    """Parse one album while preserving the image order found in HTML."""

    slug = _gallery_slug(album_url)
    if not slug:
        raise ResponseContractError("Album URL is not a /dt-gallery/ URL.")
    parsed_url = urlparse(album_url)
    site_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    soup = BeautifulSoup(html, "html.parser")
    container = _album_container(soup, site_url)

    title_tag = soup.select_one("main h1, article h1, h1")
    title = (
        _clean_text(title_tag.get_text(" ", strip=True))
        if isinstance(title_tag, Tag)
        else slug.replace("-", " ")
    )
    images = _ordered_anchor_images(container, site_url)
    if not images:
        images = _ordered_standalone_images(container, site_url)
    if not images:
        raise ResponseContractError(f"Gallery album {slug} contains no upload images.")

    return GalleryAlbum(
        slug=slug,
        url=album_url,
        title=title,
        images=tuple(images),
        source_mode="html",
        cover_url=images[0].original_url,
        published_at=_published_at(container),
    )


def _relative_site_path(site_url: str, absolute_url: str) -> str:
    site = urlparse(site_url)
    target = urlparse(absolute_url)
    if (site.scheme, site.netloc) != (target.scheme, target.netloc):
        raise ResponseContractError("Gallery URL points outside the configured WordPress site.")
    path = target.path.lstrip("/")
    if not path or ".." in path.split("/"):
        raise ResponseContractError("Gallery URL does not contain a safe relative path.")
    return path


class GalleryHtmlInventoryClient:
    """Read the public gallery archive and albums using GET requests only."""

    def __init__(
        self,
        site_url: str,
        *,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        parsed = httpx.URL(site_url)
        if parsed.scheme not in {"http", "https"} or not parsed.host:
            raise ValueError("site_url must be an absolute HTTP(S) URL.")
        self.site_url = str(parsed.copy_with(query=None, fragment=None)).rstrip("/")
        self.http = ReadOnlyHttpClient(
            base_url=self.site_url + "/",
            timeout=timeout,
            transport=transport,
            headers={"Accept": "text/html,application/xhtml+xml"},
        )

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> "GalleryHtmlInventoryClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def fetch_archive(self, path: str = "gallery/") -> tuple[GalleryArchiveEntry, ...]:
        response = self.http.get(path)
        return parse_gallery_archive(response.text, self.site_url)

    def fetch_album(self, entry: GalleryArchiveEntry) -> GalleryAlbum:
        path = _relative_site_path(self.site_url, entry.url)
        response = self.http.get(path)
        album = parse_gallery_album(response.text, entry.url)
        return GalleryAlbum(
            slug=album.slug,
            url=album.url,
            title=album.title or entry.title,
            images=album.images,
            source_mode=album.source_mode,
            cover_url=album.cover_url or entry.cover_url,
            published_at=album.published_at or entry.published_at,
        )

    def build_manifest(
        self,
        *,
        environment: str,
        observed_at: datetime | None = None,
        archive_path: str = "gallery/",
    ) -> InventoryManifest:
        at = observed_at or datetime.now(timezone.utc)
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware.")

        entries = self.fetch_archive(archive_path)
        records = []
        issues: list[InventoryIssue] = []
        for entry in entries:
            try:
                records.append(self.fetch_album(entry).to_record(observed_at=at))
            except (InventoryContractError, httpx.HTTPError) as exc:
                issues.append(
                    InventoryIssue(
                        object_ref=f"wordpress:gallery_album:{entry.slug}",
                        code="gallery_album_error",
                        message=str(exc),
                        retryable=isinstance(exc, httpx.HTTPError),
                    )
                )

        return InventoryManifest(
            manifest_type="wordpress_gallery_html",
            environment=environment,
            base_url=self.site_url,
            observed_at=at,
            records=tuple(records),
            issues=tuple(issues),
            metadata={
                "discovery_mode": "html",
                "archive_path": archive_path,
                "archive_entries": len(entries),
                "album_records": len(records),
            },
        )
