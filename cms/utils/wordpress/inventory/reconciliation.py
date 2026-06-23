"""Pure read-only reconciliation for source and target inventory manifests."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .canonical import thaw_json
from .jsonl import read_manifest_jsonl
from .models import InventoryManifest, InventoryScope, ManifestRecord


class ReconciliationState(StrEnum):
    ALREADY_IMPORTED = "already_imported"
    CREATE_CANDIDATE = "create_candidate"
    CONFLICT = "conflict"
    MANUAL_REVIEW = "manual_review"


class ReconciliationEvidenceKind(StrEnum):
    EXACT_ORIGINAL_URI_MATCH = "exact_original_uri_match"
    EXACT_SOURCE_URL_MATCH = "exact_source_url_match"
    EXACT_FILENAME_DOWNLOAD_MATCH = "exact_filename_download_match"
    HISTORICAL_MAPPING = "historical_mapping"
    HISTORICAL_MAPPING_CORROBORATED = "historical_mapping_corroborated"
    HISTORICAL_MAPPING_WITHOUT_CORROBORATION = (
        "historical_mapping_without_corroboration"
    )
    HISTORICAL_MAPPING_MISMATCH = "historical_mapping_mismatch"
    MISSING_SOURCE_URL = "missing_source_url"
    MULTIPLE_EXACT_MATCHES = "multiple_exact_matches"
    NO_EXACT_MATCH = "no_exact_match"


@dataclass(frozen=True, slots=True)
class ReconciliationEvidence:
    kind: ReconciliationEvidenceKind
    message: str
    source_field: str | None = None
    source_value: str | None = None
    target_field: str | None = None
    target_identities: tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "message": self.message,
            "source_field": self.source_field,
            "source_value": self.source_value,
            "target_field": self.target_field,
            "target_identities": list(self.target_identities),
            "details": thaw_json(self.details),
        }


@dataclass(frozen=True, slots=True)
class HistoricalMappingEvidence:
    source_identity: str
    target_identity: str | None = None
    source_url: str | None = None
    target_url: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_identity": self.source_identity,
            "target_identity": self.target_identity,
            "source_url": self.source_url,
            "target_url": self.target_url,
            "details": thaw_json(self.details),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    source_identity: str
    source_entity_type: str
    state: ReconciliationState
    source_url: str | None
    target_identities: tuple[str, ...] = ()
    evidence: tuple[ReconciliationEvidence, ...] = ()

    @property
    def matched_target_identity(self) -> str | None:
        return self.target_identities[0] if self.target_identities else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_identity": self.source_identity,
            "source_entity_type": self.source_entity_type,
            "state": self.state.value,
            "source_url": self.source_url,
            "target_identities": list(self.target_identities),
            "matched_target_identity": self.matched_target_identity,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    source_manifest_sha256: str
    target_manifest_sha256: str
    results: tuple[ReconciliationResult, ...]
    summary: Mapping[str, int] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_manifest_sha256": self.source_manifest_sha256,
            "target_manifest_sha256": self.target_manifest_sha256,
            "results": [result.to_dict() for result in self.results],
            "summary": dict(self.summary),
            "metadata": thaw_json(self.metadata),
        }


def reconcile_manifests(
    source_manifest: InventoryManifest,
    target_manifest: InventoryManifest,
    *,
    historical_mappings: Mapping[str, HistoricalMappingEvidence | Mapping[str, Any]]
    | None = None,
) -> ReconciliationReport:
    """Classify source records against the current target inventory."""

    _require_scope(source_manifest, InventoryScope.SOURCE)
    _require_scope(target_manifest, InventoryScope.TARGET)
    normalized_historical = _coerce_historical_mappings(historical_mappings)
    target_indexes = _build_target_indexes(target_manifest.records)

    results: list[ReconciliationResult] = []
    matched_target_identities: set[str] = set()
    for source_record in source_manifest.records:
        result = reconcile_record(
            source_record,
            target_manifest.records,
            historical_mapping=normalized_historical.get(source_record.identity),
            target_indexes=target_indexes,
        )
        if result.matched_target_identity is not None:
            matched_target_identities.add(result.matched_target_identity)
        results.append(result)

    summary = Counter(result.state.value for result in results)
    summary["target_only_count"] = len(target_manifest.records) - len(
        matched_target_identities
    )
    metadata = {
        "source_record_count": len(source_manifest.records),
        "target_record_count": len(target_manifest.records),
        "historical_mapping_count": len(normalized_historical),
        "matched_target_count": len(matched_target_identities),
    }
    return ReconciliationReport(
        source_manifest_sha256=source_manifest.manifest_sha256,
        target_manifest_sha256=target_manifest.manifest_sha256,
        results=tuple(results),
        summary=dict(summary),
        metadata=metadata,
    )


def reconcile_manifest_files(
    source_manifest_path: str,
    target_manifest_path: str,
    *,
    historical_mappings: Mapping[str, HistoricalMappingEvidence | Mapping[str, Any]]
    | None = None,
) -> ReconciliationReport:
    """Load manifests from disk and reconcile them read-only."""

    return reconcile_manifests(
        read_manifest_jsonl(source_manifest_path),
        read_manifest_jsonl(target_manifest_path),
        historical_mappings=historical_mappings,
    )


def reconcile_record(
    source_record: ManifestRecord,
    target_records: tuple[ManifestRecord, ...] | list[ManifestRecord],
    *,
    historical_mapping: HistoricalMappingEvidence | None = None,
    target_indexes: Mapping[str, Mapping[str, tuple[ManifestRecord, ...]]] | None = None,
) -> ReconciliationResult:
    """Classify one source record against one target inventory."""

    indexes = target_indexes or _build_target_indexes(tuple(target_records))
    source_data = thaw_json(source_record.data)
    is_media = _is_media_like_entity(source_record.entity_type)
    source_field = "source_url" if is_media else "original_uri"
    source_url = _source_url(source_record, source_data, is_media=is_media)
    target_field = "source_url" if is_media else "original_uri"
    source_filename = _source_filename(source_url) if is_media and source_url is not None else None

    evidence: list[ReconciliationEvidence] = []
    if historical_mapping is not None:
        evidence.append(
            ReconciliationEvidence(
                kind=ReconciliationEvidenceKind.HISTORICAL_MAPPING,
                message="Historical mapping evidence is present.",
                target_identities=(
                    (historical_mapping.target_identity,)
                    if historical_mapping.target_identity is not None
                    else ()
                ),
                details=historical_mapping.to_dict(),
            )
        )

    if source_url is None:
        evidence.append(
            ReconciliationEvidence(
                kind=ReconciliationEvidenceKind.MISSING_SOURCE_URL,
                message="Source record has no URL strong enough for an automatic match.",
                source_field=source_field,
                details={"entity_type": source_record.entity_type},
            )
        )
        if historical_mapping is not None:
            evidence.append(
                ReconciliationEvidence(
                    kind=ReconciliationEvidenceKind.HISTORICAL_MAPPING_WITHOUT_CORROBORATION,
                    message="Historical mapping exists but cannot be corroborated without a source URL.",
                    target_identities=(
                        (historical_mapping.target_identity,)
                        if historical_mapping.target_identity is not None
                        else ()
                    ),
                    details=historical_mapping.to_dict(),
                )
            )
        return ReconciliationResult(
            source_identity=source_record.identity,
            source_entity_type=source_record.entity_type,
            state=ReconciliationState.MANUAL_REVIEW,
            source_url=None,
            evidence=tuple(evidence),
        )

    normalized_source_url = _normalize_url(source_url)
    matches = _exact_matches(indexes.get(target_field, {}), normalized_source_url)
    if is_media and not matches and source_filename is not None:
        target_field = "filename_download"
        matches = _exact_matches(
            indexes.get(target_field, {}),
            source_filename,
        )

    if len(matches) > 1:
        return ReconciliationResult(
            source_identity=source_record.identity,
            source_entity_type=source_record.entity_type,
            state=ReconciliationState.CONFLICT,
            source_url=source_url,
            target_identities=tuple(record.identity for record in matches),
            evidence=(
                *evidence,
                ReconciliationEvidence(
                    kind=ReconciliationEvidenceKind.MULTIPLE_EXACT_MATCHES,
                    message=(
                        "Multiple target records share the same normalized URL and "
                        "cannot be matched automatically."
                    ),
                    source_field=source_field,
                    source_value=normalized_source_url,
                    target_field=target_field,
                    target_identities=tuple(record.identity for record in matches),
                    details={
                        "match_count": len(matches),
                        "target_field": target_field,
                    },
                ),
            ),
        )

    if len(matches) == 1:
        matched_target = matches[0]
        exact_kind = ReconciliationEvidenceKind.EXACT_ORIGINAL_URI_MATCH
        if is_media:
            exact_kind = (
                ReconciliationEvidenceKind.EXACT_SOURCE_URL_MATCH
                if target_field == "source_url"
                else ReconciliationEvidenceKind.EXACT_FILENAME_DOWNLOAD_MATCH
            )
        if is_media and target_field == "source_url":
            exact_message = "Exact normalized source URL match found in the target."
            exact_source_value = normalized_source_url
        elif is_media:
            exact_message = "Exact filename_download match found in the target."
            exact_source_value = source_filename
        else:
            exact_message = "Exact normalized original_uri match found in the target."
            exact_source_value = normalized_source_url
        match_evidence = ReconciliationEvidence(
            kind=exact_kind,
            message=exact_message,
            source_field=source_field,
            source_value=exact_source_value,
            target_field=target_field,
            target_identities=(matched_target.identity,),
            details={
                "target_identity": matched_target.identity,
                "target_field": target_field,
            },
        )
        evidence.append(match_evidence)

        if historical_mapping is not None:
            historical_evidence = _historical_corroboration_evidence(
                source_record=source_record,
                source_field=source_field,
                source_url=source_url,
                matched_target=matched_target,
                historical_mapping=historical_mapping,
            )
            if historical_evidence is not None:
                evidence.append(historical_evidence)

        return ReconciliationResult(
            source_identity=source_record.identity,
            source_entity_type=source_record.entity_type,
            state=ReconciliationState.ALREADY_IMPORTED,
            source_url=source_url,
            target_identities=(matched_target.identity,),
            evidence=tuple(evidence),
        )

    evidence.append(
        ReconciliationEvidence(
            kind=ReconciliationEvidenceKind.NO_EXACT_MATCH,
            message="No exact normalized target match was found.",
            source_field=source_field,
            source_value=normalized_source_url,
            target_field=target_field,
        )
    )

    if historical_mapping is not None:
        evidence.append(
            ReconciliationEvidence(
                kind=ReconciliationEvidenceKind.HISTORICAL_MAPPING_WITHOUT_CORROBORATION,
                message="Historical mapping exists, but it is not corroborated by the current target inventory.",
                target_identities=(
                    (historical_mapping.target_identity,)
                    if historical_mapping.target_identity is not None
                    else ()
                ),
                details={
                    **historical_mapping.to_dict(),
                    "current_target_count_for_url": 0,
                },
            )
        )
        return ReconciliationResult(
            source_identity=source_record.identity,
            source_entity_type=source_record.entity_type,
            state=ReconciliationState.MANUAL_REVIEW,
            source_url=source_url,
            evidence=tuple(evidence),
        )

    return ReconciliationResult(
        source_identity=source_record.identity,
        source_entity_type=source_record.entity_type,
        state=ReconciliationState.CREATE_CANDIDATE,
        source_url=source_url,
        evidence=tuple(evidence),
    )


def historical_mappings_from_parser_yaml(
    parser_yaml: Mapping[str, Any],
    *,
    source_identity_prefix: str = "wordpress:post",
    target_identity_prefix: str = "directus:feed",
) -> dict[str, HistoricalMappingEvidence]:
    """Convert parser.yaml rows into historical corroboration-only evidence."""

    source_prefix = source_identity_prefix.strip().rstrip(":")
    target_prefix = target_identity_prefix.strip().rstrip(":")
    mappings: dict[str, HistoricalMappingEvidence] = {}
    for raw_source_id, raw_row in parser_yaml.items():
        source_id = str(raw_source_id).strip()
        if not source_id:
            continue
        if not isinstance(raw_row, Mapping):
            continue

        row = thaw_json(raw_row)
        target_id = row.get("id_directus")
        target_identity = None
        if target_id not in {None, ""}:
            target_identity = f"{target_prefix}:{target_id}"

        source_url = row.get("wp_link")
        if source_url is not None:
            source_url = str(source_url)

        mappings[f"{source_prefix}:{source_id}"] = HistoricalMappingEvidence(
            source_identity=f"{source_prefix}:{source_id}",
            target_identity=target_identity,
            source_url=source_url,
            target_url=None,
            details=row,
        )
    return mappings


def _historical_corroboration_evidence(
    *,
    source_record: ManifestRecord,
    source_field: str,
    source_url: str,
    matched_target: ManifestRecord,
    historical_mapping: HistoricalMappingEvidence,
) -> ReconciliationEvidence | None:
    normalized_source_url = _normalize_url(source_url)
    normalized_historical_source = (
        _normalize_url(historical_mapping.source_url)
        if historical_mapping.source_url is not None
        else None
    )
    if historical_mapping.target_identity is not None and (
        historical_mapping.target_identity != matched_target.identity
    ):
        return ReconciliationEvidence(
            kind=ReconciliationEvidenceKind.HISTORICAL_MAPPING_MISMATCH,
            message="Historical mapping points to a different target identity than the exact match.",
            source_field=source_field,
            source_value=normalized_source_url,
            target_field="historical_target_identity",
            target_identities=(historical_mapping.target_identity, matched_target.identity),
            details={
                "historical_mapping": historical_mapping.to_dict(),
                "matched_target_identity": matched_target.identity,
            },
        )

    if normalized_historical_source is not None and normalized_historical_source != normalized_source_url:
        return ReconciliationEvidence(
            kind=ReconciliationEvidenceKind.HISTORICAL_MAPPING_MISMATCH,
            message="Historical source URL does not exactly match the current source URL.",
            source_field=source_field,
            source_value=normalized_source_url,
            target_field="historical_source_url",
            target_identities=(matched_target.identity,),
            details={
                "historical_source_url": normalized_historical_source,
                "matched_target_identity": matched_target.identity,
            },
        )

    return ReconciliationEvidence(
        kind=ReconciliationEvidenceKind.HISTORICAL_MAPPING_CORROBORATED,
        message="Historical mapping corroborates the exact target match.",
        source_field=source_field,
        source_value=normalized_source_url,
        target_field="historical_target_identity",
        target_identities=(matched_target.identity,),
        details={
            "historical_mapping": historical_mapping.to_dict(),
            "source_identity": source_record.identity,
            "matched_target_identity": matched_target.identity,
        },
    )


def _require_scope(manifest: InventoryManifest, scope: InventoryScope) -> None:
    if manifest.scope is not scope:
        raise ValueError(
            f"manifest scope must be {scope.value}, got {manifest.scope.value}."
        )


def _coerce_historical_mappings(
    historical_mappings: Mapping[str, HistoricalMappingEvidence | Mapping[str, Any]]
    | None,
) -> dict[str, HistoricalMappingEvidence]:
    if historical_mappings is None:
        return {}

    normalized: dict[str, HistoricalMappingEvidence] = {}
    for source_identity, evidence in historical_mappings.items():
        if isinstance(evidence, HistoricalMappingEvidence):
            normalized[source_identity] = evidence
            continue
        if not isinstance(evidence, Mapping):
            raise TypeError(
                "historical_mappings values must be HistoricalMappingEvidence or mappings."
            )
        normalized[source_identity] = HistoricalMappingEvidence(
            source_identity=str(evidence.get("source_identity") or source_identity),
            target_identity=(
                str(evidence["target_identity"])
                if evidence.get("target_identity") not in {None, ""}
                else None
            ),
            source_url=(
                str(evidence["source_url"])
                if evidence.get("source_url") not in {None, ""}
                else None
            ),
            target_url=(
                str(evidence["target_url"])
                if evidence.get("target_url") not in {None, ""}
                else None
            ),
            details={
                key: value
                for key, value in evidence.items()
                if key
                not in {
                    "source_identity",
                    "target_identity",
                    "source_url",
                    "target_url",
                }
            },
        )
    return normalized


def _build_target_indexes(
    target_records: tuple[ManifestRecord, ...] | list[ManifestRecord],
) -> dict[str, dict[str, tuple[ManifestRecord, ...]]]:
    indexed: dict[str, dict[str, list[ManifestRecord]]] = {
        "original_uri": defaultdict(list),
        "source_url": defaultdict(list),
        "filename_download": defaultdict(list),
    }
    for record in target_records:
        data = thaw_json(record.data)
        original_uri = _record_url(data, "original_uri")
        if original_uri is not None:
            indexed["original_uri"][_normalize_url(original_uri)].append(record)
        source_url = _record_url(data, "source_url")
        if source_url is not None:
            indexed["source_url"][_normalize_url(source_url)].append(record)
        filename_download = _record_url(data, "filename_download")
        if filename_download is not None:
            indexed["filename_download"][filename_download].append(record)
    return {
        field: {
            normalized: tuple(records)
            for normalized, records in field_index.items()
        }
        for field, field_index in indexed.items()
    }


def _exact_matches(
    field_index: Mapping[str, tuple[ManifestRecord, ...]],
    normalized_source_url: str,
) -> tuple[ManifestRecord, ...]:
    return field_index.get(normalized_source_url, ())


def _source_url(
    record: ManifestRecord,
    data: Mapping[str, Any],
    *,
    is_media: bool,
) -> str | None:
    candidates = [record.source_url, _record_url(data, "source_url")]
    if not is_media:
        candidates.append(_record_url(data, "original_uri"))
    for candidate in candidates:
        if candidate is None:
            continue
        normalized = str(candidate).strip()
        if normalized:
            return normalized
    return None


def _source_filename(source_url: str) -> str | None:
    from pathlib import Path
    from urllib.parse import urlparse

    parsed = urlparse(source_url)
    filename = Path(parsed.path).name.strip()
    return filename or None


def _record_url(data: Mapping[str, Any], field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_url(value: str) -> str:
    return value.strip().rstrip("/")


def _is_media_like_entity(entity_type: str) -> bool:
    lowered = entity_type.lower()
    return any(marker in lowered for marker in ("media", "attachment", "file"))
