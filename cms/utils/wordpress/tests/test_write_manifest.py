from __future__ import annotations

from datetime import datetime, timezone
import unittest

from inventory import InventoryManifest, InventoryScope, ManifestRecord, reconcile_manifests
from inventory.write_manifest import build_approved_write_manifest


class WriteManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observed_at = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)

    def source_manifest(self, *records: ManifestRecord) -> InventoryManifest:
        return InventoryManifest(
            scope=InventoryScope.SOURCE,
            environment="test",
            base_url="https://source.example.test",
            observed_at=self.observed_at,
            records=records,
        )

    def target_manifest(self, *records: ManifestRecord) -> InventoryManifest:
        return InventoryManifest(
            scope=InventoryScope.TARGET,
            environment="test",
            base_url="https://target.example.test",
            observed_at=self.observed_at,
            records=records,
        )

    def test_only_create_candidates_enter_approved_write_manifest(self) -> None:
        source = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:1",
                source_url="https://example.test/existing/",
                data={"title": "Existing"},
            ),
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:2",
                source_url="https://example.test/new/",
                data={"title": "New"},
            ),
        )
        target = self.target_manifest(
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="directus_feed",
                identity="directus:feed:10",
                data={"original_uri": "https://example.test/existing"},
            )
        )

        report = reconcile_manifests(source, target)
        write_manifest = build_approved_write_manifest(source, report)
        inventory_manifest = write_manifest.to_inventory_manifest(
            environment="synthetic",
            base_url="https://source.example.test",
            observed_at=self.observed_at,
        )

        self.assertEqual((write_manifest.records[0].identity,), ("wordpress:post:2",))
        self.assertEqual(
            tuple(record.identity for record in inventory_manifest.records),
            ("wordpress:post:2",),
        )
        self.assertEqual(inventory_manifest.metadata["approved_create_count"], 1)
        self.assertEqual(
            inventory_manifest.metadata["approved_source_identities"],
            ("wordpress:post:2",),
        )
        self.assertIn("approved_write_manifest_sha256", inventory_manifest.metadata)

    def test_build_manifest_rejects_wrong_scope(self) -> None:
        source = self.target_manifest()
        target = self.target_manifest()
        report = reconcile_manifests(
            InventoryManifest(
                scope=InventoryScope.SOURCE,
                environment="test",
                base_url="https://source.example.test",
                observed_at=self.observed_at,
                records=[],
            ),
            target,
        )
        with self.assertRaises(ValueError):
            build_approved_write_manifest(source, report)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
