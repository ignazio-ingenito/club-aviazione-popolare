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
from typing import Any
from uuid import UUID

from .errors import CanonicalizationError


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise CanonicalizationError("Naive datetimes are not allowed in inventory artifacts.")
    normalized = value.astimezone(timezone.utc)
    text = normalized.isoformat(timespec="microseconds")
    return text.replace("+00:00", "Z")


def canonicalize(value: Any) -> Any:
    """Convert supported values into a deterministic JSON-compatible structure.

    Mapping keys are sorted by the JSON serializer. Sequence order is preserved,
    because it can be semantically relevant for gallery images and relations.
    Sets and arbitrary objects are rejected rather than normalized heuristically.
    """

    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("Non-finite floats are not allowed.")
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

    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray, memoryview)
    ):
        return [canonicalize(item) for item in value]

    raise CanonicalizationError(
        f"Unsupported inventory value type: {type(value).__name__}."
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a value as UTF-8 canonical JSON without insignificant spaces."""

    normalized = canonicalize(value)
    try:
        serialized = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError(str(exc)) from exc
    return serialized.encode("utf-8")


def canonical_json(value: Any) -> str:
    """Return the canonical JSON representation as text."""

    return canonical_json_bytes(value).decode("utf-8")


def sha256_hex(value: Any) -> str:
    """Hash a supported value after canonical JSON normalization."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
