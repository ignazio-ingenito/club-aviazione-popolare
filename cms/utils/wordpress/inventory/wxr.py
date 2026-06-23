"""Local WordPress WXR export inventory helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

from .models import (
    InventoryIssue,
    InventoryManifest,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
)


WORDPRESS_WXR_NAMESPACE = "http://wordpress.org/export/1.2/"
WXR_NAMESPACES = {"wp": WORDPRESS_WXR_NAMESPACE}


class WordPressWXRInventoryError(RuntimeError):
    """Raised when a local WordPress export cannot be inventoried."""


@dataclass(frozen=True, slots=True)
class WordPressWXRMediaSnapshot:
    base_url: str
    source_filename: str
    records: tuple[ManifestRecord, ...]
    issues: tuple[InventoryIssue, ...]

    def to_manifest(
        self,
        *,
        environment: str,
        observed_at: datetime,
    ) -> InventoryManifest:
        return InventoryManifest(
            scope=InventoryScope.SOURCE,
            environment=environment,
            base_url=self.base_url,
            observed_at=observed_at,
            records=self.records,
            issues=self.issues,
            metadata={
                "source_format": "wordpress_wxr",
                "inventory_type": "wordpress_wxr_media",
                "source_filename": self.source_filename,
                "attachment_count": len(self.records),
                "issue_count": len(self.issues),
            },
        )


class WordPressWXRMediaInventoryClient:
    """Inventory attachment records from a local WordPress admin WXR export."""

    def __init__(self, *, export_path: str | Path) -> None:
        self.export_path = Path(export_path)

    def inventory(self) -> WordPressWXRMediaSnapshot:
        if not self.export_path.is_file():
            raise WordPressWXRInventoryError(
                f"WordPress WXR export does not exist: {self.export_path}"
            )

        try:
            root = ET.parse(self.export_path).getroot()
        except ET.ParseError as exc:
            raise WordPressWXRInventoryError(
                f"WordPress WXR export is not valid XML: {self.export_path}"
            ) from exc

        channel = root.find("channel")
        if channel is None:
            raise WordPressWXRInventoryError(
                f"WordPress WXR export has no channel element: {self.export_path}"
            )

        base_url = _channel_base_url(channel)
        records: list[ManifestRecord] = []
        issues: list[InventoryIssue] = []

        for index, item in enumerate(channel.findall("item")):
            if _wp_text(item, "post_type") != "attachment":
                continue

            raw_id = _wp_text(item, "post_id")
            if not raw_id.isdigit() or int(raw_id) < 1:
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.SOURCE,
                        severity=IssueSeverity.ERROR,
                        code="invalid_wxr_attachment_id",
                        message="WordPress WXR attachment has no positive integer post_id.",
                        details={"index": index, "raw_post_id": raw_id},
                    )
                )
                continue

            attachment_id = int(raw_id)
            identity = f"wordpress:media:{attachment_id}"
            data = _attachment_payload(item, attachment_id=attachment_id)
            source_url = _first_valid_url(
                data.get("attachment_url"),
                data.get("link"),
            )
            if source_url is None:
                issues.append(
                    InventoryIssue(
                        scope=InventoryScope.SOURCE,
                        severity=IssueSeverity.WARNING,
                        code="missing_wxr_attachment_url",
                        message="WordPress WXR attachment has no valid attachment URL.",
                        entity_type="wordpress_media",
                        identity=identity,
                        details={"index": index, "post_id": attachment_id},
                    )
                )

            records.append(
                ManifestRecord(
                    scope=InventoryScope.SOURCE,
                    entity_type="wordpress_media",
                    identity=identity,
                    source_url=source_url,
                    data=data,
                )
            )

        return WordPressWXRMediaSnapshot(
            base_url=base_url,
            source_filename=self.export_path.name,
            records=tuple(records),
            issues=tuple(issues),
        )


def _channel_base_url(channel: ET.Element) -> str:
    for field in ("link", "wp:base_site_url", "wp:base_blog_url"):
        value = _text(channel, field)
        if _is_absolute_http_url(value):
            return value.rstrip("/")
    raise WordPressWXRInventoryError("WordPress WXR export has no absolute site URL.")


def _attachment_payload(item: ET.Element, *, attachment_id: int) -> dict[str, Any]:
    parent = _wp_text(item, "post_parent")
    return {
        "id": attachment_id,
        "title": _text(item, "title"),
        "link": _text(item, "link"),
        "attachment_url": _wp_text(item, "attachment_url"),
        "post_date": _wp_text(item, "post_date"),
        "post_date_gmt": _wp_text(item, "post_date_gmt"),
        "post_modified": _wp_text(item, "post_modified"),
        "post_modified_gmt": _wp_text(item, "post_modified_gmt"),
        "post_parent": int(parent) if parent.isdigit() else parent,
        "status": _wp_text(item, "status"),
    }


def _wp_text(item: ET.Element, field: str) -> str:
    return _text(item, f"wp:{field}")


def _text(item: ET.Element, field: str) -> str:
    element = item.find(field, WXR_NAMESPACES)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _first_valid_url(*values: object) -> str | None:
    for value in values:
        if value is None:
            continue
        candidate = str(value).strip()
        if _is_absolute_http_url(candidate):
            return candidate
    return None


def _is_absolute_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
