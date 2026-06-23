"""Approved write-manifest selection from a reconciliation report.

This module does not write production data. It only derives the immutable set of
source records that are eligible to enter a future approved create-only manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_sha256
from .models import InventoryManifest, InventoryScope, ManifestRecord
from .reconciliation import ReconciliationReport, ReconciliationState


class WriteManifestError(ValueError):
    """Raised when a reconciliation report cannot produce an approved manifest."""


@dataclass(frozen=True, slots=True)
class ApprovedWriteManifest:
    scope: InventoryScope
    source_manifest_sha256: str
    target_manifest_sha256: str
    reconciliation_sha256: str
    records: tuple[ManifestRecord, ...]
    metadata: dict[str, Any]

    @property
    def sha256(self) -> str:
        return canonical_sha256(
            {
                "source_manifest_sha256": self.source_manifest_sha256,
                "target_manifest_sha256": self.target_manifest_sha256,
                "reconciliation_sha256": self.reconciliation_sha256,
                "records": [record.sha256 for record in self.records],
                "metadata": self.metadata,
            }
        )

    def to_inventory_manifest(
        self,
        *,
        environment: str,
        base_url: str,
        observed_at,
    ) -> InventoryManifest:
        return InventoryManifest(
            scope=self.scope,
            environment=environment,
            base_url=base_url,
            observed_at=observed_at,
            records=self.records,
            metadata={**self.metadata, "approved_write_manifest_sha256": self.sha256},
        )


def build_approved_write_manifest(
    source_manifest: InventoryManifest,
    report: ReconciliationReport,
) -> ApprovedWriteManifest:
    if source_manifest.scope is not InventoryScope.SOURCE:
        raise WriteManifestError("source_manifest must have source scope.")

    candidate_identities = {
        result.source_identity
        for result in report.results
        if result.state is ReconciliationState.CREATE_CANDIDATE
    }
    source_by_identity = {record.identity: record for record in source_manifest.records}
    missing = sorted(identity for identity in candidate_identities if identity not in source_by_identity)
    if missing:
        raise WriteManifestError(
            f"Source inventory is missing create candidates: {missing}."
        )

    records = tuple(
        source_by_identity[result.source_identity]
        for result in report.results
        if result.state is ReconciliationState.CREATE_CANDIDATE
    )
    metadata = {
        "approved_source_identities": [record.identity for record in records],
        "approved_create_count": len(records),
    }
    return ApprovedWriteManifest(
        scope=source_manifest.scope,
        source_manifest_sha256=source_manifest.manifest_sha256,
        target_manifest_sha256=report.target_manifest_sha256,
        reconciliation_sha256=canonical_sha256(report.to_dict()),
        records=records,
        metadata=metadata,
    )
