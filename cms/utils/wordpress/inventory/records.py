"""Immutable record and issue models for inventory artifacts."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonicalize, sha256_hex
from .errors import InventoryContractError

SCHEMA_VERSION = 1


def _require_text(name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InventoryContractError(f"{name} must not be empty.")
    return normalized


def _freeze_value(value: Any) -> Any:
    normalized = canonicalize(value)
    if isinstance(normalized, MappingABC):
        return MappingProxyType(
            {key: _freeze_value(item) for key, item in normalized.items()}
        )
    if isinstance(normalized, Sequence) and not isinstance(normalized, str):
        return tuple(_freeze_value(item) for item in normalized)
    return normalized


def freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen = _freeze_value(value)
    if not isinstance(frozen, MappingABC):
        raise InventoryContractError("Expected an inventory mapping.")
    return frozen


@dataclass(frozen=True, slots=True)
class InventoryIssue:
    """A non-silent source or target inventory problem."""

    object_ref: str
    code: str
    message: str
    retryable: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "object_ref", _require_text("object_ref", self.object_ref))
        object.__setattr__(self, "code", _require_text("code", self.code))
        object.__setattr__(self, "message", _require_text("message", self.message))
        object.__setattr__(self, "details", freeze_mapping(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_ref": self.object_ref,
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class ManifestRecord:
    """One canonical source or target object observed during inventory."""

    system: str
    object_type: str
    object_id: str
    observed_at: datetime
    payload: Mapping[str, Any]
    canonical_url: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "system", _require_text("system", self.system))
        object.__setattr__(
            self, "object_type", _require_text("object_type", self.object_type)
        )
        object.__setattr__(self, "object_id", _require_text("object_id", self.object_id))
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise InventoryContractError("observed_at must be timezone-aware.")
        if self.canonical_url is not None:
            object.__setattr__(
                self,
                "canonical_url",
                _require_text("canonical_url", self.canonical_url),
            )
        object.__setattr__(self, "payload", freeze_mapping(self.payload))
        self.content_hash()

    @property
    def identity(self) -> str:
        return f"{self.system}:{self.object_type}:{self.object_id}"

    def content_dict(self) -> dict[str, Any]:
        """Return content used for drift comparison, excluding observation time."""

        return {
            "schema_version": SCHEMA_VERSION,
            "identity": self.identity,
            "canonical_url": self.canonical_url,
            "payload": dict(self.payload),
        }

    def content_hash(self) -> str:
        return sha256_hex(self.content_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.content_dict(),
            "observed_at": self.observed_at,
            "content_hash": self.content_hash(),
        }
