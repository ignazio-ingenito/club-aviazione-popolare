"""Fail-closed permission evidence checks for future Directus writes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .models import ManifestRecord


PERMISSION_OPERATIONS = ("create", "read", "update", "delete", "share")


class PermissionGateError(ValueError):
    """Raised when permission evidence is missing, malformed, or too broad."""


@dataclass(frozen=True, slots=True)
class PermissionExpectation:
    """Expected Directus permission matrix for one collection."""

    create: str
    read: str
    update: str
    delete: str
    share: str

    def to_dict(self) -> dict[str, str]:
        return {
            "create": self.create,
            "read": self.read,
            "update": self.update,
            "delete": self.delete,
            "share": self.share,
        }


def validate_permission_evidence(
    permissions_record: ManifestRecord | Mapping[str, Any] | None,
    *,
    expected_access: Mapping[str, PermissionExpectation | Mapping[str, str]],
) -> None:
    """Fail closed unless permission evidence matches the approved matrix."""

    payload = _permission_payload(permissions_record)
    normalized_expected = {
        collection: _normalize_expectation(expectation)
        for collection, expectation in expected_access.items()
    }

    for collection, expectation in normalized_expected.items():
        if collection not in payload:
            raise PermissionGateError(
                f"Permission evidence is missing for collection {collection}."
            )
        actual = _permission_entry(payload[collection], collection=collection)
        for operation in PERMISSION_OPERATIONS:
            expected_access_value = expectation[operation]
            actual_access_value = _permission_access_value(
                actual,
                collection=collection,
                operation=operation,
            )
            if actual_access_value != expected_access_value:
                raise PermissionGateError(
                    "Permission evidence does not match the approved matrix for "
                    f"{collection}.{operation}: expected {expected_access_value!r}, "
                    f"got {actual_access_value!r}."
                )

    for collection, raw_entry in payload.items():
        if collection in normalized_expected:
            continue
        if not isinstance(raw_entry, Mapping):
            raise PermissionGateError(
                f"Permission evidence for collection {collection} must be a mapping."
            )
        for operation in PERMISSION_OPERATIONS:
            block = raw_entry.get(operation)
            if isinstance(block, Mapping) and str(block.get("access")) != "none":
                raise PermissionGateError(
                    f"Unexpected broad permission evidence for {collection}.{operation}: "
                    f"{block.get('access')!r}."
                )


def _permission_payload(
    permissions_record: ManifestRecord | Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    if permissions_record is None:
        raise PermissionGateError("Permission evidence is missing.")
    if isinstance(permissions_record, ManifestRecord):
        payload = permissions_record.data
    else:
        payload = permissions_record
    if not isinstance(payload, Mapping):
        raise PermissionGateError("Permission evidence must be a mapping.")
    if not payload:
        raise PermissionGateError("Permission evidence is empty.")
    return payload


def _normalize_expectation(
    expectation: PermissionExpectation | Mapping[str, str],
) -> dict[str, str]:
    if isinstance(expectation, PermissionExpectation):
        candidate = expectation.to_dict()
    else:
        candidate = dict(expectation)
    normalized = {}
    for operation in PERMISSION_OPERATIONS:
        if operation not in candidate:
            raise PermissionGateError(
                f"Expected permission matrix is missing {operation!r}."
            )
        normalized[operation] = str(candidate[operation])
    return normalized


def _permission_entry(entry: Any, *, collection: str) -> Mapping[str, Any]:
    if not isinstance(entry, Mapping):
        raise PermissionGateError(
            f"Permission evidence for collection {collection} must be a mapping."
        )
    return entry


def _permission_access_value(
    entry: Mapping[str, Any],
    *,
    collection: str,
    operation: str,
) -> str:
    block = entry.get(operation)
    if not isinstance(block, Mapping):
        raise PermissionGateError(
            f"Permission evidence is missing {collection}.{operation}."
        )
    if "access" not in block:
        raise PermissionGateError(
            f"Permission evidence is missing {collection}.{operation}.access."
        )
    return str(block["access"])
