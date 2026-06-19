"""Normalize WordPress REST objects into immutable source manifest records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .models import (
    InventoryIssue,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
)


@dataclass(frozen=True, slots=True)
class BuiltWordPressRecord:
    record: ManifestRecord
    issues: tuple[InventoryIssue, ...] = ()


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer.")
    return value


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, int) else None


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _rendered(item: Mapping[str, Any], field_name: str) -> str:
    container = item.get(field_name)
    if not isinstance(container, Mapping):
        return ""
    rendered = container.get("rendered")
    return rendered if isinstance(rendered, str) else ""


def _absolute_http_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value.strip()


def _integer_list(value: Any) -> tuple[list[int], bool]:
    if not isinstance(value, list):
        return [], value is not None
    result: list[int] = []
    invalid = False
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            invalid = True
            continue
        result.append(item)
    return result, invalid


def _html_attribute(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        normalized = " ".join(str(item) for item in value if str(item))
    else:
        normalized = str(value)
    normalized = normalized.strip()
    return normalized or None


def extract_html_references(html: str) -> dict[str, list[dict[str, str]]]:
    """Extract links and image references without changing source HTML."""

    if not html:
        return {"images": [], "links": []}

    soup = BeautifulSoup(html, "html.parser")
    images: list[dict[str, str]] = []
    links: list[dict[str, str]] = []

    for tag in soup.find_all("img"):
        record = {
            key: value
            for key in ("src", "srcset", "data-src", "data-lazy-src", "alt", "title")
            if (value := _html_attribute(tag.attrs.get(key))) is not None
        }
        images.append(record)

    for tag in soup.find_all("a"):
        record = {
            key: value
            for key in ("href", "title", "rel")
            if (value := _html_attribute(tag.attrs.get(key))) is not None
        }
        links.append(record)

    return {"images": images, "links": links}


def _selected_featured_media(item: Mapping[str, Any]) -> dict[str, Any] | None:
    embedded = item.get("_embedded")
    if not isinstance(embedded, Mapping):
        return None

    candidates = embedded.get("wp:featuredmedia")
    if not isinstance(candidates, list) or not candidates:
        return None

    media = candidates[0]
    if not isinstance(media, Mapping):
        return None

    return {
        "id": _optional_int(media.get("id")),
        "date": _text(media.get("date")),
        "slug": _text(media.get("slug")),
        "link": _text(media.get("link")),
        "source_url": _text(media.get("source_url")),
        "alt_text": _text(media.get("alt_text")) or "",
        "media_type": _text(media.get("media_type")),
        "mime_type": _text(media.get("mime_type")),
        "title": _rendered(media, "title"),
        "caption": _rendered(media, "caption"),
        "media_details": (
            dict(media["media_details"])
            if isinstance(media.get("media_details"), Mapping)
            else {}
        ),
    }


def _record_issue(
    *,
    code: str,
    message: str,
    entity_type: str,
    identity: str,
    severity: IssueSeverity = IssueSeverity.ERROR,
    details: Mapping[str, Any] | None = None,
) -> InventoryIssue:
    return InventoryIssue(
        scope=InventoryScope.SOURCE,
        severity=severity,
        code=code,
        message=message,
        entity_type=entity_type,
        identity=identity,
        details=details or {},
    )


def build_type_record(key: str, item: Mapping[str, Any]) -> BuiltWordPressRecord:
    slug = _text(item.get("slug")) or key
    identity = f"wordpress:type:{slug}"
    issues: list[InventoryIssue] = []
    if not _text(item.get("slug")):
        issues.append(
            _record_issue(
                code="wordpress_type_missing_slug",
                message="WordPress type has no explicit slug; endpoint key was used.",
                entity_type="wordpress_type",
                identity=identity,
                severity=IssueSeverity.WARNING,
                details={"endpoint_key": key},
            )
        )

    taxonomies = item.get("taxonomies")
    if not isinstance(taxonomies, list):
        taxonomies = []

    record = ManifestRecord(
        scope=InventoryScope.SOURCE,
        entity_type="wordpress_type",
        identity=identity,
        data={
            "name": _text(item.get("name")) or "",
            "description": _text(item.get("description")) or "",
            "hierarchical": bool(item.get("hierarchical")),
            "rest_base": _text(item.get("rest_base")),
            "rest_namespace": _text(item.get("rest_namespace")),
            "slug": slug,
            "taxonomies": [value for value in taxonomies if isinstance(value, str)],
            "viewable": bool(item.get("viewable")),
        },
    )
    return BuiltWordPressRecord(record=record, issues=tuple(issues))


def build_category_record(item: Mapping[str, Any]) -> BuiltWordPressRecord:
    category_id = _positive_int(item.get("id"), "category.id")
    identity = f"wordpress:category:{category_id}"
    source_url = _absolute_http_url(item.get("link"))
    issues: list[InventoryIssue] = []
    if source_url is None:
        issues.append(
            _record_issue(
                code="wordpress_category_invalid_link",
                message="WordPress category has no valid absolute link.",
                entity_type="wordpress_category",
                identity=identity,
                details={"field": "link"},
            )
        )

    record = ManifestRecord(
        scope=InventoryScope.SOURCE,
        entity_type="wordpress_category",
        identity=identity,
        source_url=source_url,
        data={
            "id": category_id,
            "count": _optional_int(item.get("count")),
            "description": _text(item.get("description")) or "",
            "link": _text(item.get("link")),
            "name": _text(item.get("name")) or "",
            "slug": _text(item.get("slug")) or "",
            "taxonomy": _text(item.get("taxonomy")),
            "parent": _optional_int(item.get("parent")),
        },
    )
    return BuiltWordPressRecord(record=record, issues=tuple(issues))


def build_post_record(item: Mapping[str, Any]) -> BuiltWordPressRecord:
    post_id = _positive_int(item.get("id"), "post.id")
    identity = f"wordpress:post:{post_id}"
    source_url = _absolute_http_url(item.get("link"))
    issues: list[InventoryIssue] = []
    if source_url is None:
        issues.append(
            _record_issue(
                code="wordpress_post_invalid_link",
                message="WordPress post has no valid absolute canonical link.",
                entity_type="wordpress_post",
                identity=identity,
                details={"field": "link"},
            )
        )

    slug = _text(item.get("slug")) or ""
    if not slug:
        issues.append(
            _record_issue(
                code="wordpress_post_missing_slug",
                message="WordPress post has an empty slug.",
                entity_type="wordpress_post",
                identity=identity,
                severity=IssueSeverity.WARNING,
            )
        )

    title = _rendered(item, "title")
    if not title:
        issues.append(
            _record_issue(
                code="wordpress_post_empty_title",
                message="WordPress post has an empty rendered title.",
                entity_type="wordpress_post",
                identity=identity,
                severity=IssueSeverity.WARNING,
            )
        )

    categories, invalid_categories = _integer_list(item.get("categories"))
    tags, invalid_tags = _integer_list(item.get("tags"))
    if invalid_categories:
        issues.append(
            _record_issue(
                code="wordpress_post_invalid_categories",
                message="WordPress post categories contained non-integer values.",
                entity_type="wordpress_post",
                identity=identity,
            )
        )
    if invalid_tags:
        issues.append(
            _record_issue(
                code="wordpress_post_invalid_tags",
                message="WordPress post tags contained non-integer values.",
                entity_type="wordpress_post",
                identity=identity,
            )
        )

    content = _rendered(item, "content")
    record = ManifestRecord(
        scope=InventoryScope.SOURCE,
        entity_type="wordpress_post",
        identity=identity,
        source_url=source_url,
        data={
            "id": post_id,
            "type": _text(item.get("type")) or "post",
            "slug": slug,
            "link": _text(item.get("link")),
            "date": _text(item.get("date")),
            "date_gmt": _text(item.get("date_gmt")),
            "modified": _text(item.get("modified")),
            "modified_gmt": _text(item.get("modified_gmt")),
            "status": _text(item.get("status")),
            "author": _optional_int(item.get("author")),
            "featured_media": _optional_int(item.get("featured_media")),
            "categories": categories,
            "tags": tags,
            "guid": _rendered(item, "guid"),
            "title": title,
            "excerpt": _rendered(item, "excerpt"),
            "content": content,
            "html_references": extract_html_references(content),
            "embedded_featured_media": _selected_featured_media(item),
        },
    )
    return BuiltWordPressRecord(record=record, issues=tuple(issues))


def build_media_record(item: Mapping[str, Any]) -> BuiltWordPressRecord:
    media_id = _positive_int(item.get("id"), "media.id")
    identity = f"wordpress:media:{media_id}"
    source_url = _absolute_http_url(item.get("link"))
    file_url = _absolute_http_url(item.get("source_url"))
    issues: list[InventoryIssue] = []

    if source_url is None:
        issues.append(
            _record_issue(
                code="wordpress_media_invalid_link",
                message="WordPress media item has no valid absolute attachment link.",
                entity_type="wordpress_media",
                identity=identity,
                details={"field": "link"},
            )
        )
    if file_url is None:
        issues.append(
            _record_issue(
                code="wordpress_media_invalid_source_url",
                message="WordPress media item has no valid absolute source file URL.",
                entity_type="wordpress_media",
                identity=identity,
                details={"field": "source_url"},
            )
        )

    record = ManifestRecord(
        scope=InventoryScope.SOURCE,
        entity_type="wordpress_media",
        identity=identity,
        source_url=source_url,
        data={
            "id": media_id,
            "type": _text(item.get("type")) or "attachment",
            "slug": _text(item.get("slug")) or "",
            "status": _text(item.get("status")),
            "date": _text(item.get("date")),
            "date_gmt": _text(item.get("date_gmt")),
            "modified": _text(item.get("modified")),
            "modified_gmt": _text(item.get("modified_gmt")),
            "post": _optional_int(item.get("post")),
            "link": _text(item.get("link")),
            "title": _rendered(item, "title"),
            "caption": _rendered(item, "caption"),
            "description": _rendered(item, "description"),
            "alt_text": _text(item.get("alt_text")) or "",
            "media_type": _text(item.get("media_type")),
            "mime_type": _text(item.get("mime_type")),
            "source_url": _text(item.get("source_url")),
            "media_details": (
                dict(item["media_details"])
                if isinstance(item.get("media_details"), Mapping)
                else {}
            ),
        },
    )
    return BuiltWordPressRecord(record=record, issues=tuple(issues))
