"""Immutable manifest and issue models for read-only migration inventories."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from .canonical import canonical_sha256, freeze_json, normalize_json, thaw_json


MANIFEST_SCHEMA_VERSION = 1


class InventoryScope(StrEnum):
    SOURCE = "source"
    TARGET = "target"


class IssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


def _require_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty.")
    return normalized


def _require_absolute_http_url(value: str, field_name: str) -> str:
    normalized = _require_text(value, field_name).rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be an absolute HTTP(S) URL.")
    return normalized


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class ManifestRecord:
    scope: InventoryScope
    entity_type: str
    identity: str
    data: Mapping[str, Any]
    source_url: str | None = None
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", InventoryScope(self.scope))
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported record schema_version={self.schema_version}; "
                f"expected {MANIFEST_SCHEMA_VERSION}."
            )

        object.__setattr__(
            self, "entity_type", _require_text(self.entity_type, "entity_type")
        )
        object.__setattr__(self, "identity", _require_text(self.identity, "identity"))
        object.__setattr__(self, "data", freeze_json(self.data))

        if self.source_url is not None:
            object.__setattr__(
                self,
                "source_url",
                _require_absolute_http_url(self.source_url, "source_url"),
            )

    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "entity_type": self.entity_type,
            "identity": self.identity,
            "source_url": self.source_url,
            "data": thaw_json(self.data),
        }

    @property
    def sha256(self) -> str:
        return canonical_sha256(self.fingerprint_payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self.fingerprint_payload(), "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class InventoryIssue:
    scope: InventoryScope
    code: str
    message: str
    severity: IssueSeverity = IssueSeverity.ERROR
    entity_type: str | None = None
    identity: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", InventoryScope(self.scope))
        object.__setattr__(self, "severity", IssueSeverity(self.severity))
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported issue schema_version={self.schema_version}; "
                f"expected {MANIFEST_SCHEMA_VERSION}."
            )

        object.__setattr__(self, "code", _require_text(self.code, "code"))
        object.__setattr__(self, "message", _require_text(self.message, "message"))
        object.__setattr__(self, "details", freeze_json(self.details))

        if self.entity_type is not None:
            object.__setattr__(
                self, "entity_type", _require_text(self.entity_type, "entity_type")
            )
        if self.identity is not None:
            object.__setattr__(
                self, "identity", _require_text(self.identity, "identity")
            )

        if (self.entity_type is None) != (self.identity is None):
            raise ValueError(
                "entity_type and identity must either both be set or both be omitted."
            )

    def fingerprint_payload(self) -> dict[str, Any]:
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

    @property
    def sha256(self) -> str:
        return canonical_sha256(self.fingerprint_payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self.fingerprint_payload(), "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class InventoryManifest:
    scope: InventoryScope
    environment: str
    base_url: str
    observed_at: datetime
    records: tuple[ManifestRecord, ...]
    issues: tuple[InventoryIssue, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = MANIFEST_SCHEMA_VERSION

    def __init__(
        self,
        *,
        scope: InventoryScope,
        environment: str,
        base_url: str,
        observed_at: datetime,
        records: Iterable[ManifestRecord],
        issues: Iterable[InventoryIssue] = (),
        metadata: Mapping[str, Any] | None = None,
        schema_version: int = MANIFEST_SCHEMA_VERSION,
    ) -> None:
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "base_url", base_url)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "records", tuple(records))
        object.__setattr__(self, "issues", tuple(issues))
        object.__setattr__(self, "metadata", metadata or {})
        object.__setattr__(self, "schema_version", schema_version)
        self.__post_init__()

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", InventoryScope(self.scope))
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported manifest schema_version={self.schema_version}; "
                f"expected {MANIFEST_SCHEMA_VERSION}."
            )

        object.__setattr__(
            self, "environment", _require_text(self.environment, "environment")
        )
        object.__setattr__(
            self, "base_url", _require_absolute_http_url(self.base_url, "base_url")
        )
        object.__setattr__(
            self,
            "observed_at",
            _require_aware_datetime(self.observed_at, "observed_at"),
        )
        object.__setattr__(self, "metadata", freeze_json(self.metadata))

        records = tuple(
            sorted(
                self.records,
                key=lambda record: (
                    record.scope.value,
                    record.entity_type,
                    record.identity,
                ),
            )
        )
        issues = tuple(
            sorted(
                self.issues,
                key=lambda issue: (
                    issue.scope.value,
                    issue.severity.value,
                    issue.entity_type or "",
                    issue.identity or "",
                    issue.code,
                    issue.sha256,
                ),
            )
        )

        for record in records:
            if record.scope is not self.scope:
                raise ValueError(
                    f"Record {record.identity} has scope={record.scope.value}; "
                    f"manifest scope is {self.scope.value}."
                )
        for issue in issues:
            if issue.scope is not self.scope:
                raise ValueError(
                    f"Issue {issue.code} has scope={issue.scope.value}; "
                    f"manifest scope is {self.scope.value}."
                )

        identity_counts = Counter(
            (record.entity_type, record.identity) for record in records
        )
        duplicates = sorted(
            identity for identity, count in identity_counts.items() if count > 1
        )
        if duplicates:
            raise ValueError(f"Duplicate manifest identities: {duplicates}.")

        object.__setattr__(self, "records", records)
        object.__setattr__(self, "issues", issues)

    def content_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "records": [record.fingerprint_payload() for record in self.records],
            "issues": [issue.fingerprint_payload() for issue in self.issues],
        }

    @property
    def content_sha256(self) -> str:
        """Fingerprint inventory content independently from run metadata/time."""

        return canonical_sha256(self.content_payload())

    def document_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "environment": self.environment,
            "base_url": self.base_url,
            "observed_at": normalize_json(self.observed_at),
            "metadata": thaw_json(self.metadata),
            "records": [record.to_dict() for record in self.records],
            "issues": [issue.to_dict() for issue in self.issues],
            "content_sha256": self.content_sha256,
        }

    @property
    def manifest_sha256(self) -> str:
        return canonical_sha256(self.document_payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self.document_payload(), "manifest_sha256": self.manifest_sha256}
