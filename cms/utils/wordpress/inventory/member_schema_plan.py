"""Dry-run plan for the approved members-only Directus schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from .jsonl import read_manifest_jsonl
from .models import (
    InventoryIssue,
    InventoryManifest,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
)


MEMBER_COLLECTIONS = (
    "member_categories",
    "member_topics",
    "member_feeds",
    "member_feeds_files",
    "member_feeds_topics",
    "legacy_wordpress_credentials",
)
LEGACY_CREDENTIALS_COLLECTION = "legacy_wordpress_credentials"


@dataclass(frozen=True, slots=True)
class SchemaRequest:
    sequence: int
    method: str
    endpoint: str
    body: Mapping[str, Any]

    def to_record(self) -> ManifestRecord:
        if self.method not in {"POST"}:
            raise ValueError(f"Unsupported schema request method: {self.method}.")
        return ManifestRecord(
            scope=InventoryScope.TARGET,
            entity_type="directus_schema_request",
            identity=f"directus:schema-request:{self.sequence:04d}",
            data={
                "sequence": self.sequence,
                "method": self.method,
                "endpoint": self.endpoint,
                "body": dict(self.body),
            },
        )


def build_member_schema_plan_manifest(
    *,
    target_manifest_path: str | Path,
    environment: str,
    observed_at: datetime,
) -> InventoryManifest:
    target_manifest = read_manifest_jsonl(target_manifest_path)
    existing_collections = _collection_names(target_manifest.records)
    existing_member_collections = sorted(
        collection
        for collection in existing_collections
        if collection in MEMBER_COLLECTIONS
    )
    if existing_member_collections:
        issues = [
            InventoryIssue(
                scope=InventoryScope.TARGET,
                severity=IssueSeverity.FATAL,
                code="member_schema_already_exists",
                message=(
                    "Directus target already contains members-only schema "
                    "collections; manual review is required before apply."
                ),
                details={"collections": existing_member_collections},
            )
        ]
        records: tuple[ManifestRecord, ...] = ()
    else:
        issues = []
        records = tuple(request.to_record() for request in _schema_requests())

    return InventoryManifest(
        scope=InventoryScope.TARGET,
        environment=environment,
        base_url=target_manifest.base_url,
        observed_at=observed_at,
        records=records,
        issues=issues,
        metadata={
            "inventory_type": "directus_member_schema_plan",
            "mode": "dry_run",
            "target_manifest_sha256": target_manifest.manifest_sha256,
            "planned_collection_count": len(MEMBER_COLLECTIONS),
            "forbidden_methods": ("PATCH", "PUT", "DELETE"),
            "schema_apply_plan": "docs/migrations/wordpress-to-directus/members-only-schema-apply-plan.md",
        },
    )


def _collection_names(records: Iterable[ManifestRecord]) -> set[str]:
    names: set[str] = set()
    for record in records:
        if record.entity_type != "directus_collection":
            continue
        collection = record.data.get("collection")
        if isinstance(collection, str):
            names.add(collection)
    return names


def _schema_requests() -> tuple[SchemaRequest, ...]:
    requests: list[SchemaRequest] = []

    def add(method: str, endpoint: str, body: Mapping[str, Any]) -> None:
        requests.append(
            SchemaRequest(
                sequence=len(requests) + 1,
                method=method,
                endpoint=endpoint,
                body=body,
            )
        )

    for collection, icon in (
        ("member_categories", "folder_special"),
        ("member_topics", "sell"),
        ("member_feeds", "article"),
        ("member_feeds_files", "attach_file"),
        ("member_feeds_topics", "hub"),
        (LEGACY_CREDENTIALS_COLLECTION, "key"),
    ):
        add(
            "POST",
            "/collections",
            {
                "collection": collection,
                "meta": {
                    "collection": collection,
                    "icon": icon,
                    "hidden": collection == LEGACY_CREDENTIALS_COLLECTION,
                    "singleton": False,
                    "archive_field": _workflow_value(collection, "status"),
                    "archive_value": _workflow_value(collection, "archived"),
                    "unarchive_value": _workflow_value(collection, "draft"),
                },
                "schema": {"name": collection},
            },
        )

    for collection, fields in _field_specs().items():
        for field in fields:
            add("POST", f"/fields/{collection}", field)

    for relation in _relation_specs():
        add("POST", "/relations", relation)

    return tuple(requests)


def _field_specs() -> dict[str, tuple[dict[str, Any], ...]]:
    return {
        "member_categories": (
            _field("status", "string", required=True, interface="select-dropdown"),
            _field("slug", "string", required=True, unique=True),
            _field("title", "string", required=True),
            _field("description", "text"),
            _field("sort", "integer"),
            _field("source_system", "string", required=True),
            _field("source_identity", "string"),
            _field("source_slug", "string"),
        ),
        "member_topics": (
            _field("slug", "string", required=True, unique=True),
            _field("title", "string", required=True),
            _field("source_taxonomy", "string", required=True),
            _field("source_identity", "string", required=True, unique=True),
            _field("sort", "integer"),
        ),
        "member_feeds": (
            _field("status", "string", required=True, interface="select-dropdown"),
            _field(
                "visibility",
                "string",
                required=True,
                interface="select-dropdown",
            ),
            _field("slug", "string", required=True),
            _field("title", "string", required=True),
            _field("description", "text"),
            _field("content", "text", required=True, interface="input-rich-text-html"),
            _field("content_format", "string", required=True),
            _field("date", "dateTime"),
            _field("modified_source_at", "dateTime"),
            _field("author", "string"),
            _alias("category", "m2o", "integer"),
            _alias("cover", "m2o", "uuid"),
            _field("source_system", "string", required=True),
            _field("source_identity", "string", required=True, unique=True),
            _field("source_post_type", "string", required=True),
            _field("source_url", "string"),
            _field("source_hash", "string", required=True),
            _field("migration_run_id", "string", required=True),
        ),
        "member_feeds_files": (
            _alias("member_feed", "m2o", "integer"),
            _alias("file", "m2o", "uuid"),
            _field("sort", "integer", required=True),
            _field("source_identity", "string", required=True),
        ),
        "member_feeds_topics": (
            _alias("member_feed", "m2o", "integer"),
            _alias("member_topic", "m2o", "integer"),
        ),
        "legacy_wordpress_credentials": (
            _alias("directus_user", "m2o", "uuid"),
            _field("wordpress_user_id", "integer", required=True, unique=True),
            _field("legacy_hash", "string", required=True),
            _field("hash_format", "string", required=True),
            _field("status", "string", required=True, interface="select-dropdown"),
            _field("consumed_at", "dateTime"),
            _field("expires_at", "dateTime", required=True),
            _field("source_hash", "string", required=True),
            _field("migration_run_id", "string", required=True),
        ),
    }


def _field(
    field: str,
    field_type: str,
    *,
    required: bool = False,
    unique: bool = False,
    primary_key: bool = False,
    interface: str | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"name": field, "data_type": field_type}
    if primary_key:
        schema.update({"is_primary_key": True})
    if unique:
        schema.update({"is_unique": True})
    return {
        "field": field,
        "type": field_type,
        "meta": {
            "field": field,
            "interface": interface or _default_interface(field_type),
            "required": required,
            "readonly": primary_key,
            "hidden": False,
        },
        "schema": schema,
    }


def _alias(field: str, special: str, field_type: str) -> dict[str, Any]:
    return {
        "field": field,
        "type": field_type,
        "meta": {
            "field": field,
            "interface": "select-dropdown-m2o",
            "special": (special,),
            "required": True,
            "readonly": False,
            "hidden": False,
        },
        "schema": {"name": field, "data_type": field_type},
    }


def _default_interface(field_type: str) -> str:
    return {
        "text": "input-multiline",
        "dateTime": "datetime",
        "integer": "input",
        "uuid": "input",
    }.get(field_type, "input")


def _relation_specs() -> tuple[dict[str, Any], ...]:
    return (
        _m2o("member_feeds", "category", "member_categories", one_field="feeds"),
        _m2o("member_feeds", "cover", "directus_files"),
        _m2o(
            "member_feeds_files",
            "member_feed",
            "member_feeds",
            one_field="attachments",
        ),
        _m2o("member_feeds_files", "file", "directus_files"),
        _m2o(
            "member_feeds_topics",
            "member_feed",
            "member_feeds",
            one_field="topics",
        ),
        _m2o(
            "member_feeds_topics",
            "member_topic",
            "member_topics",
            one_field="feeds",
        ),
        _m2o(LEGACY_CREDENTIALS_COLLECTION, "directus_user", "directus_users"),
    )


def _workflow_value(collection: str, value: str) -> str | None:
    if collection == LEGACY_CREDENTIALS_COLLECTION:
        return None
    return value


def _m2o(
    collection: str,
    field: str,
    related_collection: str,
    *,
    one_field: str | None = None,
) -> dict[str, Any]:
    return {
        "collection": collection,
        "field": field,
        "related_collection": related_collection,
        "meta": {
            "many_collection": collection,
            "many_field": field,
            "one_collection": related_collection,
            "one_field": one_field,
            "one_deselect_action": "nullify",
        },
        "schema": {
            "table": collection,
            "column": field,
            "foreign_key_table": related_collection,
            "foreign_key_column": "id",
            "on_delete": "SET NULL",
        },
    }
