from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from inventory import InventoryManifest, InventoryScope, ManifestRecord
from inventory.jsonl import read_manifest_jsonl
from inventory.member_schema_plan import (
    MEMBER_COLLECTIONS,
    build_member_schema_plan_manifest,
)
from inventory.writer import write_manifest_jsonl


class MemberSchemaPlanTests(unittest.TestCase):
    def test_generates_dry_run_schema_requests_without_forbidden_methods(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline_path = self.write_target_baseline(Path(tmp), collections=("feeds",))
            manifest = build_member_schema_plan_manifest(
                target_manifest_path=baseline_path,
                environment="synthetic",
                observed_at=datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(manifest.issues, ())
        self.assertGreater(len(manifest.records), len(MEMBER_COLLECTIONS))
        methods = {record.data["method"] for record in manifest.records}
        self.assertEqual(methods, {"POST"})
        self.assertTrue(
            all(
                record.data["method"] not in {"PATCH", "PUT", "DELETE"}
                for record in manifest.records
            )
        )
        endpoints = {record.data["endpoint"] for record in manifest.records}
        self.assertIn("/collections", endpoints)
        self.assertIn("/relations", endpoints)
        self.assertIn("/fields/member_feeds", endpoints)
        collections = [
            record.data["body"]["collection"]
            for record in manifest.records
            if record.data["endpoint"] == "/collections"
        ]
        self.assertEqual(tuple(collections), MEMBER_COLLECTIONS)

    def test_schema_plan_does_not_create_directus_auto_primary_keys(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline_path = self.write_target_baseline(Path(tmp), collections=("feeds",))
            manifest = build_member_schema_plan_manifest(
                target_manifest_path=baseline_path,
                environment="synthetic",
                observed_at=datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            )

        explicit_id_fields = [
            record
            for record in manifest.records
            if str(record.data["endpoint"]).startswith("/fields/")
            and record.data["body"]["field"] == "id"
        ]
        self.assertEqual(explicit_id_fields, [])

    def test_schema_plan_uses_fk_field_types_matching_related_primary_keys(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline_path = self.write_target_baseline(Path(tmp), collections=("feeds",))
            manifest = build_member_schema_plan_manifest(
                target_manifest_path=baseline_path,
                environment="synthetic",
                observed_at=datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            )

        field_types = {
            (
                record.data["endpoint"].removeprefix("/fields/"),
                record.data["body"]["field"],
            ): record.data["body"]["schema"]["data_type"]
            for record in manifest.records
            if str(record.data["endpoint"]).startswith("/fields/")
        }

        self.assertEqual(field_types[("member_feeds", "category")], "integer")
        self.assertEqual(field_types[("member_feeds_files", "member_feed")], "integer")
        self.assertEqual(field_types[("member_feeds_topics", "member_feed")], "integer")
        self.assertEqual(field_types[("member_feeds_topics", "member_topic")], "integer")
        self.assertEqual(field_types[("member_feeds", "cover")], "uuid")
        self.assertEqual(field_types[("member_feeds_files", "file")], "uuid")
        self.assertEqual(
            field_types[("legacy_wordpress_credentials", "directus_user")],
            "uuid",
        )

    def test_workflow_collections_include_status_field(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline_path = self.write_target_baseline(Path(tmp), collections=("feeds",))
            manifest = build_member_schema_plan_manifest(
                target_manifest_path=baseline_path,
                environment="synthetic",
                observed_at=datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            )

        status_fields = {
            record.data["endpoint"].removeprefix("/fields/"): record.data["body"]
            for record in manifest.records
            if str(record.data["endpoint"]).startswith("/fields/")
            and record.data["body"]["field"] == "status"
        }

        self.assertEqual(
            set(status_fields),
            {
                "member_categories",
                "member_topics",
                "member_feeds",
                "member_feeds_files",
                "member_feeds_topics",
                "legacy_wordpress_credentials",
            },
        )
        for field in status_fields.values():
            self.assertEqual(field["type"], "string")
            self.assertTrue(field["meta"]["required"])
            self.assertEqual(field["meta"]["interface"], "select-dropdown")

    def test_existing_member_collection_fails_closed_without_requests(self) -> None:
        with TemporaryDirectory() as tmp:
            baseline_path = self.write_target_baseline(
                Path(tmp),
                collections=("feeds", "member_feeds"),
            )
            manifest = build_member_schema_plan_manifest(
                target_manifest_path=baseline_path,
                environment="synthetic",
                observed_at=datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(manifest.records, ())
        self.assertEqual(manifest.issues[0].code, "member_schema_already_exists")
        self.assertEqual(
            manifest.issues[0].details["collections"],
            ("member_feeds",),
        )

    def test_cli_writes_schema_plan_manifest_and_checksum(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            baseline_path = self.write_target_baseline(tmp_path, collections=("feeds",))
            output_dir = tmp_path / "run"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "inventory",
                    "directus-member-schema-plan",
                    "--target-manifest",
                    str(baseline_path),
                    "--output-dir",
                    str(output_dir),
                    "--filename",
                    "directus-member-schema-plan.jsonl",
                    "--environment",
                    "synthetic",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            manifest_path = output_dir / "directus-member-schema-plan.jsonl"
            checksum_path = output_dir / "directus-member-schema-plan.jsonl.sha256"
            self.assertEqual(Path(summary["manifest"]), manifest_path)
            self.assertEqual(Path(summary["checksum"]), checksum_path)
            self.assertTrue(manifest_path.exists())
            self.assertTrue(checksum_path.exists())
            manifest = read_manifest_jsonl(manifest_path)
            self.assertEqual(
                manifest.metadata["inventory_type"],
                "directus_member_schema_plan",
            )

    @staticmethod
    def write_target_baseline(tmp_path: Path, *, collections: tuple[str, ...]) -> Path:
        manifest = InventoryManifest(
            scope=InventoryScope.TARGET,
            environment="synthetic",
            base_url="https://directus.example.test",
            observed_at=datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            records=[
                ManifestRecord(
                    scope=InventoryScope.TARGET,
                    entity_type="directus_collection",
                    identity=f"directus:collection:{collection}",
                    data={"collection": collection},
                )
                for collection in collections
            ],
        )
        result = write_manifest_jsonl(
            manifest,
            output_dir=tmp_path / "baseline",
            filename="target.jsonl",
        )
        return result.manifest_path


if __name__ == "__main__":
    unittest.main()
