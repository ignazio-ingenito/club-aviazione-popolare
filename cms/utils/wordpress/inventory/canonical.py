"""Canonical JSON and SHA-256 helpers for immutable inventory artifacts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any
from uuid import UUID

from .errors import CanonicalizationError


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise CanonicalizationError("Naive datetimes are not allowed in inventory artifacts.")
    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonicalize(value: Any) -> Any:
    """Convert supported values into a deterministic JSON-compatible structure."""

    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("NaN and infinite floats are not allowed.")
        return value

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise CanonicalizationError("Non-finite decimals are not allowed.")
        return format(value, "f")

    if isinstance(value, datetime):
        return _canonical_datetime(value)

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, (UUID, Path)):
        return str(value)

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return canonicalize(dataclasses.asdict(value))

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(
                    f"Inventory mapping keys must be strings, got {type(key).__name__}."
                )
            normalized[key] = canonicalize(item)
        return normalized

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, memoryview)):
        return [canonicalize(item) for item in value]

    if isinstance(value, (set, frozenset)):
        raise CanonicalizationError("Sets are not allowed because their ordering is not explicit.")

    if isinstance(value, (bytes, bytearray, memoryview)):
        raise CanonicalizationError("Binary values must be stored externally and referenced by checksum.")

    raise CanonicalizationError(f"Unsupported canonical JSON value: {type(value).__name__}.")


def normalize_json(value: Any) -> Any:
    """Backward-compatible alias for canonicalize."""

    return canonicalize(value)


def freeze_json(value: Any) -> Any:
    """Normalize a value and recursively freeze mappings/sequences."""

    normalized = canonicalize(value)

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
    return canonicalize(value)


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
    """Serialize a value as UTF-8 canonical JSON without insignificant spaces."""

    return canonical_json(value).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_hex(value: Any) -> str:
    """Backward-compatible alias for canonical_sha256."""

    return canonical_sha256(value)
