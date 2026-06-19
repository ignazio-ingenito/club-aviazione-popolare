"""Deterministic JSON normalization and SHA-256 helpers for inventory artifacts."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented safely as canonical JSON."""


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise CanonicalizationError("Naive datetimes are not allowed in inventory artifacts.")

    normalized = value.astimezone(timezone.utc)
    timespec = "microseconds" if normalized.microsecond else "seconds"
    return normalized.isoformat(timespec=timespec).replace("+00:00", "Z")


def normalize_json(value: Any) -> Any:
    """Return a JSON-compatible value with deterministic date and enum handling.

    Mapping keys must be strings. Lists and tuples preserve order because order can be
    semantically relevant, especially for galleries. Sets are rejected rather than
    sorted implicitly because doing so could hide an upstream ordering bug.
    """

    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("NaN and infinite floats are not allowed.")
        return value

    if isinstance(value, datetime):
        return _canonical_datetime(value)

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        return normalize_json(value.value)

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: normalize_json(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(
                    f"Canonical JSON mapping keys must be strings, got {type(key).__name__}."
                )
            normalized[key] = normalize_json(item)
        return normalized

    if isinstance(value, (list, tuple)):
        return [normalize_json(item) for item in value]

    if isinstance(value, (set, frozenset)):
        raise CanonicalizationError(
            "Sets are not allowed because their ordering is not explicit."
        )

    if isinstance(value, (bytes, bytearray, memoryview)):
        raise CanonicalizationError(
            "Binary values must be stored externally and referenced by checksum."
        )

    raise CanonicalizationError(
        f"Unsupported canonical JSON value: {type(value).__name__}."
    )


def freeze_json(value: Any) -> Any:
    """Normalize a value and recursively freeze mappings/sequences."""

    normalized = normalize_json(value)

    def freeze(item: Any) -> Any:
        if isinstance(item, dict):
            return MappingProxyType({key: freeze(value) for key, value in item.items()})
        if isinstance(item, list):
            return tuple(freeze(value) for value in item)
        return item

    return freeze(normalized)


def thaw_json(value: Any) -> Any:
    """Return ordinary JSON containers from a recursively frozen value."""

    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return normalize_json(value)


def canonical_json(value: Any) -> str:
    """Serialize a value using the repository's canonical JSON representation."""

    return json.dumps(
        normalize_json(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_json_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))
