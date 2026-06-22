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
