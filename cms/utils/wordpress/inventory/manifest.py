"""Canonical manifest model for one read-only inventory run."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .canonical import canonical_json, sha256_hex
from .errors import InventoryContractError
from .records import (
    SCHEMA_VERSION,
    InventoryIssue,
    ManifestRecord,
    _require_text,
    freeze_mapping,
)


@dataclass(frozen=True, slots=True)
class InventoryManifest:
    """Canonical inventory artifact for one environment and observation run."""

    manifest_type: str
    environment: str
    base_url: str
    observed_at: datetime
    records: tuple[ManifestRecord, ...] = ()
    issues: tuple[InventoryIssue, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "manifest_type", _require_text("manifest_type", self.manifest_type)
        )
        object.__setattr__(
            self, "environment", _require_text("environment", self.environment)
        )
        object.__setattr__(self, "base_url", _require_text("base_url", self.base_url))
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise InventoryContractError("observed_at must be timezone-aware.")
        if self.schema_version != SCHEMA_VERSION:
            raise InventoryContractError(
                f"Unsupported manifest schema version {self.schema_version}."
            )
        object.__setattr__(self, "records", tuple(self.records))
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "metadata", freeze_mapping(self.metadata))

        identity_counts = Counter(record.identity for record in self.records)
        duplicates = sorted(
            identity for identity, count in identity_counts.items() if count > 1
        )
        if duplicates:
            raise InventoryContractError(
                f"Duplicate manifest record identities: {', '.join(duplicates)}"
            )

        self.canonical_json()

    def to_dict(self) -> dict[str, Any]:
        sorted_records = sorted(self.records, key=lambda record: record.identity)
        sorted_issues = sorted(
            self.issues,
            key=lambda issue: (issue.object_ref, issue.code, issue.message),
        )
        return {
            "schema_version": self.schema_version,
            "manifest_type": self.manifest_type,
            "environment": self.environment,
            "base_url": self.base_url,
            "observed_at": self.observed_at,
            "records": [record.to_dict() for record in sorted_records],
            "issues": [issue.to_dict() for issue in sorted_issues],
            "metadata": dict(self.metadata),
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())

    def artifact_hash(self) -> str:
        return sha256_hex(self.to_dict())
