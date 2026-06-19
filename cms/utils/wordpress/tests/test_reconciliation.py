from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import unittest

from inventory import (
    HistoricalMappingEvidence,
    InventoryManifest,
    InventoryScope,
    ManifestRecord,
    ReconciliationState,
    historical_mappings_from_parser_yaml,
    read_manifest_jsonl,
    reconcile_manifests,
    render_manifest_jsonl,
)


class ReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observed_at = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)

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

    def test_exact_original_uri_match_is_already_imported(self) -> None:
        source = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:1",
                source_url="https://example.test/article/",
                data={"title": "Article"},
            )
        )
        target = self.target_manifest(
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="directus_feed",
                identity="directus:feed:10",
                data={"original_uri": "https://example.test/article"},
            )
        )

        report = reconcile_manifests(source, target)
        result = report.results[0]

        self.assertIs(result.state, ReconciliationState.ALREADY_IMPORTED)
        self.assertEqual(result.matched_target_identity, "directus:feed:10")
        self.assertIn("already_imported", report.summary)
        self.assertEqual(result.evidence[0].kind.value, "exact_original_uri_match")

    def test_exact_filename_download_match_is_already_imported_for_media(self) -> None:
        source = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_media",
                identity="wordpress:media:5",
                source_url="https://example.test/image.jpg",
                data={"title": "Image"},
            )
        )
        target = self.target_manifest(
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="directus_file",
                identity="directus:file:20",
                data={"filename_download": "image.jpg"},
            )
        )

        report = reconcile_manifests(source, target)
        result = report.results[0]

        self.assertIs(result.state, ReconciliationState.ALREADY_IMPORTED)
        self.assertEqual(result.matched_target_identity, "directus:file:20")
        self.assertEqual(result.evidence[0].kind.value, "exact_filename_download_match")

    def test_no_match_becomes_create_candidate(self) -> None:
        source = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:2",
                source_url="https://example.test/new-article/",
                data={"title": "New article"},
            )
        )
        target = self.target_manifest()

        report = reconcile_manifests(source, target)
        result = report.results[0]

        self.assertIs(result.state, ReconciliationState.CREATE_CANDIDATE)
        self.assertIsNone(result.matched_target_identity)
        self.assertIn("create_candidate", report.summary)

    def test_two_target_matches_become_conflict(self) -> None:
        source = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:3",
                source_url="https://example.test/dup/",
                data={"title": "Duplicate"},
            )
        )
        target = self.target_manifest(
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="directus_feed",
                identity="directus:feed:11",
                data={"original_uri": "https://example.test/dup"},
            ),
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="directus_feed",
                identity="directus:feed:12",
                data={"original_uri": "https://example.test/dup/"},
            ),
        )

        report = reconcile_manifests(source, target)
        result = report.results[0]

        self.assertIs(result.state, ReconciliationState.CONFLICT)
        self.assertEqual(
            result.target_identities,
            ("directus:feed:11", "directus:feed:12"),
        )
        self.assertEqual(result.evidence[-1].kind.value, "multiple_exact_matches")

    def test_historical_map_without_corroboration_becomes_manual_review(self) -> None:
        source = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:4",
                source_url="https://example.test/source/",
                data={"title": "Historical"},
            )
        )
        target = self.target_manifest(
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="directus_feed",
                identity="directus:feed:99",
                data={"original_uri": "https://example.test/other"},
            )
        )
        historical = {
            "wordpress:post:4": HistoricalMappingEvidence(
                source_identity="wordpress:post:4",
                target_identity="directus:feed:99",
                source_url="https://example.test/source/",
                details={"parser": "yaml"},
            )
        }

        report = reconcile_manifests(source, target, historical_mappings=historical)
        result = report.results[0]

        self.assertIs(result.state, ReconciliationState.MANUAL_REVIEW)
        self.assertEqual(
            [evidence.kind.value for evidence in result.evidence],
            ["historical_mapping", "no_exact_match", "historical_mapping_without_corroboration"],
        )

    def test_parser_yaml_only_corroborates_and_never_authorizes_by_itself(self) -> None:
        parser_yaml = {
            "2582": {
                "id_wordpress": "2582",
                "id_directus": 175,
                "slug": "welcome",
                "title": "Benvenuti sul sito del CAP",
                "wp_link": "https://www.clubaviazionepopolare.org/welcome/",
            }
        }
        historical = historical_mappings_from_parser_yaml(parser_yaml)
        source = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:2582",
                source_url="https://example.test/not-the-same/",
                data={"title": "Benvenuti"},
            )
        )
        target = self.target_manifest(
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="directus_feed",
                identity="directus:feed:175",
                data={"original_uri": "https://example.test/still-not-the-same/"},
            )
        )

        report = reconcile_manifests(source, target, historical_mappings=historical)
        result = report.results[0]

        self.assertIs(result.state, ReconciliationState.MANUAL_REVIEW)
        self.assertTrue(any(e.kind.value == "historical_mapping" for e in result.evidence))
        self.assertTrue(
            any(
                e.kind.value == "historical_mapping_without_corroboration"
                for e in result.evidence
            )
        )

    def test_manifest_jsonl_reader_round_trips_render_format(self) -> None:
        manifest = self.source_manifest(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_post",
                identity="wordpress:post:7",
                source_url="https://example.test/round-trip/",
                data={"title": "Round trip"},
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "source.jsonl"
            path.write_text(render_manifest_jsonl(manifest).decode("utf-8"), encoding="utf-8")
            loaded = read_manifest_jsonl(path)

        self.assertEqual(loaded.to_dict(), manifest.to_dict())
        json.dumps(loaded.to_dict())


if __name__ == "__main__":
    unittest.main()
