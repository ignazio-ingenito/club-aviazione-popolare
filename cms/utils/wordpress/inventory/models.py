"""Inventory model classes used by the WordPress migration tooling."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping as MappingABC, Sequence
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import canonical_json, canonical_sha256, canonicalize, sha256_hex, thaw_json
from .errors import InventoryContractError


SCHEMA_VERSION = 1


class InventoryScope(str, Enum):
    SOURCE = "source"
    TARGET = "target"


class IssueSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InventoryContractError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise InventoryContractError(f"{field_name} must not be empty.")
    return normalized


def _normalize_scope(value: InventoryScope | str) -> InventoryScope:
    try:
        return value if isinstance(value, InventoryScope) else InventoryScope(str(value))
    except ValueError as exc:
        raise InventoryContractError(f"Unsupported inventory scope: {value!r}.") from exc


def _normalize_severity(value: IssueSeverity | str) -> IssueSeverity:
    try:
        return value if isinstance(value, IssueSeverity) else IssueSeverity(str(value))
    except ValueError as exc:
        raise InventoryContractError(f"Unsupported issue severity: {value!r}.") from exc


def _freeze_value(value: Any) -> Any:
    normalized = canonicalize(value)
    if isinstance(normalized, MappingABC):
        return MappingProxyType({key: _freeze_value(item) for key, item in normalized.items()})
    if isinstance(normalized, Sequence) and not isinstance(normalized, str):
        return tuple(_freeze_value(item) for item in normalized)
    return normalized


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen = _freeze_value(value)
    if not isinstance(frozen, MappingABC):
        raise InventoryContractError("Expected an inventory mapping.")
    return frozen


class ManifestRecord:
    """One source or target record.

    Supports both the original `system/object_type/object_id/payload` contract
    and the later migration `scope/entity_type/identity/data` JSONL contract.
    """

    def __init__(
        self,
        *,
        scope: InventoryScope | str | None = None,
        entity_type: str | None = None,
        identity: str | None = None,
        data: Mapping[str, Any] | None = None,
        source_url: str | None = None,
        schema_version: int = SCHEMA_VERSION,
        system: str | None = None,
        object_type: str | None = None,
        object_id: str | None = None,
        observed_at: datetime | None = None,
        payload: Mapping[str, Any] | None = None,
        canonical_url: str | None = None,
    ) -> None:
        if schema_version != SCHEMA_VERSION:
            raise InventoryContractError(f"Unsupported record schema version {schema_version}.")
        self.schema_version = schema_version
        self.observed_at = observed_at

        if system is not None or object_type is not None or object_id is not None or payload is not None:
            if observed_at is None or observed_at.tzinfo is None or observed_at.utcoffset() is None:
                raise InventoryContractError("observed_at must be timezone-aware.")
            self.system = _require_text(system, "system")
            self.object_type = _require_text(object_type, "object_type")
            self.object_id = _require_text(object_id, "object_id")
            self.canonical_url = _require_text(canonical_url, "canonical_url") if canonical_url is not None else None
            self.payload = _freeze_mapping(payload or {})
            self.scope = None
            self.entity_type = self.object_type
            self.identity = f"{self.system}:{self.object_type}:{self.object_id}"
            self.source_url = self.canonical_url
            self.data = self.payload
            return

        self.scope = _normalize_scope(scope if scope is not None else "")
        self.entity_type = _require_text(entity_type, "entity_type")
        self.identity = _require_text(identity, "identity")
        self.source_url = _require_text(source_url, "source_url") if source_url is not None else None
        self.data = _freeze_mapping(data or {})
        parts = self.identity.split(":", 2)
        self.system = parts[0] if len(parts) == 3 else self.scope.value
        self.object_type = self.entity_type
        self.object_id = parts[2] if len(parts) == 3 else self.identity
        self.canonical_url = self.source_url
        self.payload = self.data

    @property
    def sha256(self) -> str:
        return canonical_sha256(
            {
                "schema_version": self.schema_version,
                "scope": self.scope.value if self.scope is not None else None,
                "entity_type": self.entity_type,
                "identity": self.identity,
                "source_url": self.source_url,
                "data": dict(self.data),
            }
        )

    def content_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "identity": self.identity,
            "canonical_url": self.canonical_url,
            "payload": thaw_json(self.payload),
        }

    def content_hash(self) -> str:
        return sha256_hex(self.content_dict())

    def to_dict(self) -> dict[str, Any]:
        if self.scope is None:
            return {
                **self.content_dict(),
                "observed_at": canonicalize(self.observed_at),
                "content_hash": self.content_hash(),
            }
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "entity_type": self.entity_type,
            "identity": self.identity,
            "source_url": self.source_url,
            "data": thaw_json(self.data),
            "sha256": self.sha256,
        }


class InventoryIssue:
    def __init__(
        self,
        object_ref: str | None = None,
        code: str | None = None,
        message: str | None = None,
        *,
        scope: InventoryScope | str | None = None,
        severity: IssueSeverity | str = IssueSeverity.ERROR,
        entity_type: str | None = None,
        identity: str | None = None,
        details: Mapping[str, Any] | None = None,
        retryable: bool = False,
        schema_version: int = SCHEMA_VERSION,
    ) -> None:
        if schema_version != SCHEMA_VERSION:
            raise InventoryContractError(f"Unsupported issue schema version {schema_version}.")
        self.schema_version = schema_version
        self.scope = _normalize_scope(scope) if scope is not None else None
        self.severity = _normalize_severity(severity)
        self.object_ref = _require_text(object_ref, "object_ref") if object_ref is not None else identity
        self.code = _require_text(code, "code")
        self.message = _require_text(message, "message")
        self.entity_type = _require_text(entity_type, "entity_type") if entity_type is not None else None
        self.identity = _require_text(identity, "identity") if identity is not None else self.object_ref
        self.details = _freeze_mapping(details or {})
        self.retryable = retryable

    def to_dict(self) -> dict[str, Any]:
        if self.scope is None:
            return {
                "object_ref": self.object_ref,
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
                "details": thaw_json(self.details),
            }
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "entity_type": self.entity_type,
            "identity": self.identity,
            "details": thaw_json(self.details),
        }


class InventoryManifest:
    def __init__(
        self,
        *,
        scope: InventoryScope | str | None = None,
        manifest_type: str | None = None,
        environment: str,
        base_url: str,
        observed_at: datetime,
        records: tuple[ManifestRecord, ...] = (),
        issues: tuple[InventoryIssue, ...] = (),
        metadata: Mapping[str, Any] | None = None,
        schema_version: int = SCHEMA_VERSION,
    ) -> None:
        if schema_version != SCHEMA_VERSION:
            raise InventoryContractError(f"Unsupported manifest schema version {schema_version}.")
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise InventoryContractError("observed_at must be timezone-aware.")
        self.schema_version = schema_version
        self.scope = _normalize_scope(scope) if scope is not None else None
        self.manifest_type = _require_text(manifest_type or (self.scope.value if self.scope is not None else ""), "manifest_type")
        self.environment = _require_text(environment, "environment")
        self.base_url = _require_text(base_url, "base_url")
        self.observed_at = observed_at
        self.records = tuple(records)
        self.issues = tuple(issues)
        self.metadata = _freeze_mapping(metadata or {})
        duplicates = sorted(
            identity for identity, count in Counter(record.identity for record in self.records).items() if count > 1
        )
        if duplicates:
            raise InventoryContractError(f"Duplicate manifest record identities: {', '.join(duplicates)}")
        self.manifest_sha256

    def to_dict(self) -> dict[str, Any]:
        sorted_records = sorted(self.records, key=lambda record: record.identity)
        sorted_issues = sorted(self.issues, key=lambda issue: (issue.identity or issue.object_ref or "", issue.code, issue.message))
        if self.scope is None:
            return {
                "schema_version": self.schema_version,
                "manifest_type": self.manifest_type,
                "environment": self.environment,
                "base_url": self.base_url,
                "observed_at": canonicalize(self.observed_at),
                "records": [record.to_dict() for record in sorted_records],
                "issues": [issue.to_dict() for issue in sorted_issues],
                "metadata": thaw_json(self.metadata),
            }
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "environment": self.environment,
            "base_url": self.base_url,
            "observed_at": canonicalize(self.observed_at),
            "records": [record.to_dict() for record in sorted_records],
            "issues": [issue.to_dict() for issue in sorted_issues],
            "metadata": thaw_json(self.metadata),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    def artifact_hash(self) -> str:
        return sha256_hex(self.to_dict())

    @property
    def content_sha256(self) -> str:
        return canonical_sha256(
            {
                "schema_version": self.schema_version,
                "scope": self.scope.value if self.scope is not None else None,
                "manifest_type": self.manifest_type,
                "environment": self.environment,
                "base_url": self.base_url,
                "records": [record.to_dict() for record in sorted(self.records, key=lambda item: item.identity)],
                "issues": [
                    issue.to_dict()
                    for issue in sorted(
                        self.issues,
                        key=lambda item: (item.identity or item.object_ref or "", item.code, item.message),
                    )
                ],
                "metadata": thaw_json(self.metadata),
            }
        )

    @property
    def manifest_sha256(self) -> str:
        return canonical_sha256({"content_sha256": self.content_sha256, "observed_at": self.observed_at})


__all__ = [
    "InventoryIssue",
    "InventoryManifest",
    "InventoryScope",
    "IssueSeverity",
    "ManifestRecord",
]
