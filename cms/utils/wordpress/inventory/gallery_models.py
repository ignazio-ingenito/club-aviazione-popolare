"""Immutable models for WordPress gallery discovery and inventory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .errors import InventoryContractError
from .records import ManifestRecord, _require_text


@dataclass(frozen=True, slots=True)
class GalleryRestCandidate:
    type_key: str
    rest_base: str
    rest_namespace: str
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_key", _require_text("type_key", self.type_key))
        object.__setattr__(self, "rest_base", _require_text("rest_base", self.rest_base))
        object.__setattr__(
            self,
            "rest_namespace",
            _require_text("rest_namespace", self.rest_namespace),
        )
        object.__setattr__(self, "evidence", tuple(self.evidence))


@dataclass(frozen=True, slots=True)
class GalleryDiscoveryPlan:
    mode: str
    reason: str
    rest_candidate: GalleryRestCandidate | None = None

    def __post_init__(self) -> None:
        if self.mode not in {"rest", "html"}:
            raise InventoryContractError("Gallery discovery mode must be rest or html.")
        object.__setattr__(self, "reason", _require_text("reason", self.reason))
        if self.mode == "rest" and self.rest_candidate is None:
            raise InventoryContractError("REST mode requires a REST candidate.")


@dataclass(frozen=True, slots=True)
class GalleryArchiveEntry:
    slug: str
    url: str
    title: str
    position: int
    cover_url: str | None = None
    published_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "slug", _require_text("slug", self.slug))
        object.__setattr__(self, "url", _require_text("url", self.url))
        object.__setattr__(self, "title", _require_text("title", self.title))
        if self.position < 0:
            raise InventoryContractError("Gallery archive position must not be negative.")


@dataclass(frozen=True, slots=True)
class GalleryImage:
    position: int
    original_url: str
    thumbnail_url: str | None = None
    title: str | None = None
    alt_text: str | None = None
    caption: str | None = None

    def __post_init__(self) -> None:
        if self.position < 0:
            raise InventoryContractError("Gallery image position must not be negative.")
        object.__setattr__(
            self,
            "original_url",
            _require_text("original_url", self.original_url),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "position": self.position,
            "original_url": self.original_url,
            "thumbnail_url": self.thumbnail_url,
            "title": self.title,
            "alt_text": self.alt_text,
            "caption": self.caption,
        }


@dataclass(frozen=True, slots=True)
class GalleryAlbum:
    slug: str
    url: str
    title: str
    images: tuple[GalleryImage, ...]
    source_mode: str
    cover_url: str | None = None
    published_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "slug", _require_text("slug", self.slug))
        object.__setattr__(self, "url", _require_text("url", self.url))
        object.__setattr__(self, "title", _require_text("title", self.title))
        object.__setattr__(self, "source_mode", _require_text("source_mode", self.source_mode))
        object.__setattr__(self, "images", tuple(self.images))
        if not self.images:
            raise InventoryContractError("A gallery album must contain at least one image.")
        positions = tuple(image.position for image in self.images)
        if positions != tuple(range(len(self.images))):
            raise InventoryContractError(
                "Gallery image positions must be contiguous and preserve source order."
            )

    def to_record(self, *, observed_at: datetime) -> ManifestRecord:
        return ManifestRecord(
            system="wordpress",
            object_type="gallery_album",
            object_id=self.slug,
            canonical_url=self.url,
            observed_at=observed_at,
            payload={
                "title": self.title,
                "cover_url": self.cover_url,
                "published_at": self.published_at,
                "source_mode": self.source_mode,
                "images": [image.to_dict() for image in self.images],
            },
        )
