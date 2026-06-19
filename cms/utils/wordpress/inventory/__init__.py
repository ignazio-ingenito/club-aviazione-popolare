"""Read-only inventory contracts for the WordPress-to-Directus migration."""

from .canonical import (
    CanonicalizationError,
    canonical_json,
    canonical_json_bytes,
    canonical_sha256,
    freeze_json,
    normalize_json,
    sha256_bytes,
    thaw_json,
)
from .jsonl import (
    iter_manifest_jsonl_lines,
    manifest_jsonl_sha256,
    read_manifest_jsonl,
    render_manifest_jsonl,
)
from .reconciliation import (
    HistoricalMappingEvidence,
    ReconciliationEvidence,
    ReconciliationEvidenceKind,
    ReconciliationReport,
    ReconciliationResult,
    ReconciliationState,
    historical_mappings_from_parser_yaml,
    reconcile_manifest_files,
    reconcile_manifests,
    reconcile_record,
)
from .models import (
    MANIFEST_SCHEMA_VERSION,
    InventoryIssue,
    InventoryManifest,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
)
from .pagination import (
    InventoryPage,
    PageMetadata,
    PaginationError,
    merge_complete_pages,
)

__all__ = [
    "MANIFEST_SCHEMA_VERSION",
    "CanonicalizationError",
    "InventoryIssue",
    "InventoryManifest",
    "InventoryPage",
    "InventoryScope",
    "IssueSeverity",
    "HistoricalMappingEvidence",
    "ManifestRecord",
    "PageMetadata",
    "PaginationError",
    "ReconciliationEvidence",
    "ReconciliationEvidenceKind",
    "ReconciliationReport",
    "ReconciliationResult",
    "ReconciliationState",
    "canonical_json",
    "canonical_json_bytes",
    "canonical_sha256",
    "historical_mappings_from_parser_yaml",
    "freeze_json",
    "iter_manifest_jsonl_lines",
    "manifest_jsonl_sha256",
    "read_manifest_jsonl",
    "merge_complete_pages",
    "reconcile_manifest_files",
    "reconcile_manifests",
    "reconcile_record",
    "normalize_json",
    "render_manifest_jsonl",
    "sha256_bytes",
    "thaw_json",
]
