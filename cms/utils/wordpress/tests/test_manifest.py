from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import unittest

from inventory import (
    CanonicalizationError,
    InventoryIssue,
    InventoryManifest,
    InventoryPage,
    InventoryScope,
    IssueSeverity,
    ManifestRecord,
    PageMetadata,
    PaginationError,
    canonical_json,
    canonical_sha256,
    manifest_jsonl_sha256,
    merge_complete_pages,
    render_manifest_jsonl,
)


class CanonicalJsonTests(unittest.TestCase):
    def test_mapping_order_does_not_change_hash(self) -> None:
        left = {"b": 2, "a": {"z": 3, "y": 4}}
        right = {"a": {"y": 4, "z": 3}, "b": 2}

        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(canonical_sha256(left), canonical_sha256(right))

    def test_sequence_order_changes_hash(self) -> None:
        self.assertNotEqual(
            canonical_sha256({"images": ["a.jpg", "b.jpg"]}),
            canonical_sha256({"images": ["b.jpg", "a.jpg"]}),
        )

    def test_equivalent_timezones_have_same_representation(self) -> None:
        utc = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)
        cest = datetime(
            2026,
            6,
            19,
            12,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        )
        self.assertEqual(canonical_json({"at": utc}), canonical_json({"at": cest}))

    def test_naive_datetime_is_rejected(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonical_json({"at": datetime(2026, 6, 19, 10, 0)})

    def test_sets_and_binary_data_are_rejected(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonical_json({"items": {"a", "b"}})
        with self.assertRaises(CanonicalizationError):
            canonical_json({"content": b"binary"})


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observed_at = datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc)

    def test_record_copies_and_freezes_input_data(self) -> None:
        source = {"title": "Original", "images": ["a.jpg", "b.jpg"]}
        record = ManifestRecord(
            scope=InventoryScope.SOURCE,
            entity_type="wordpress_post",
            identity="wordpress:post:1",
            source_url="https://example.test/post-1/",
            data=source,
        )

        source["title"] = "Changed"
        source["images"].append("c.jpg")

        self.assertEqual(record.data["title"], "Original")
        self.assertEqual(record.data["images"], ("a.jpg", "b.jpg"))
        with self.assertRaises(TypeError):
            record.data["title"] = "Mutation"  # type: ignore[index]

    def test_manifest_sorts_records_and_rejects_duplicate_identity(self) -> None:
        second = ManifestRecord(
            scope=InventoryScope.SOURCE,
            entity_type="wordpress_post",
            identity="wordpress:post:2",
            data={"title": "Second"},
        )
        first = ManifestRecord(
            scope=InventoryScope.SOURCE,
            entity_type="wordpress_post",
            identity="wordpress:post:1",
            data={"title": "First"},
        )

        manifest = InventoryManifest(
            scope=InventoryScope.SOURCE,
            environment="test",
            base_url="https://example.test",
            observed_at=self.observed_at,
            records=[second, first],
        )
        self.assertEqual(
            [record.identity for record in manifest.records],
            ["wordpress:post:1", "wordpress:post:2"],
        )

        with self.assertRaises(ValueError):
            InventoryManifest(
                scope=InventoryScope.SOURCE,
                environment="test",
                base_url="https://example.test",
                observed_at=self.observed_at,
                records=[first, first],
            )

    def test_content_hash_ignores_observation_time_but_manifest_hash_does_not(self) -> None:
        record = ManifestRecord(
            scope=InventoryScope.TARGET,
            entity_type="directus_feed",
            identity="directus:feeds:10",
            data={"title": "Protected"},
        )
        first = InventoryManifest(
            scope=InventoryScope.TARGET,
            environment="production",
            base_url="https://cms.example.test",
            observed_at=self.observed_at,
            records=[record],
        )
        second = InventoryManifest(
            scope=InventoryScope.TARGET,
            environment="production",
            base_url="https://cms.example.test",
            observed_at=self.observed_at + timedelta(minutes=1),
            records=[record],
        )

        self.assertEqual(first.content_sha256, second.content_sha256)
        self.assertNotEqual(first.manifest_sha256, second.manifest_sha256)

    def test_scope_mismatch_is_rejected(self) -> None:
        record = ManifestRecord(
            scope=InventoryScope.SOURCE,
            entity_type="wordpress_post",
            identity="wordpress:post:1",
            data={},
        )
        with self.assertRaises(ValueError):
            InventoryManifest(
                scope=InventoryScope.TARGET,
                environment="test",
                base_url="https://cms.example.test",
                observed_at=self.observed_at,
                records=[record],
            )

    def test_string_enum_values_are_coerced_and_to_dict_is_json_serializable(self) -> None:
        record = ManifestRecord(
            scope="source",  # type: ignore[arg-type]
            entity_type="wordpress_post",
            identity="wordpress:post:1",
            data={"title": "Post"},
        )
        issue = InventoryIssue(
            scope="source",  # type: ignore[arg-type]
            severity="warning",  # type: ignore[arg-type]
            code="synthetic",
            message="Synthetic warning.",
        )
        manifest = InventoryManifest(
            scope="source",  # type: ignore[arg-type]
            environment="test",
            base_url="https://example.test",
            observed_at=self.observed_at,
            records=[record],
            issues=[issue],
        )

        self.assertIs(record.scope, InventoryScope.SOURCE)
        self.assertIs(issue.severity, IssueSeverity.WARNING)
        json.dumps(manifest.to_dict())

    def test_jsonl_is_deterministic_and_contains_trailer_hashes(self) -> None:
        issue = InventoryIssue(
            scope=InventoryScope.SOURCE,
            severity=IssueSeverity.WARNING,
            code="missing_optional_alt",
            message="Image has no alt text.",
            entity_type="wordpress_media",
            identity="wordpress:media:4",
            details={"url": "https://example.test/image.jpg"},
        )
        record = ManifestRecord(
            scope=InventoryScope.SOURCE,
            entity_type="wordpress_post",
            identity="wordpress:post:1",
            data={"title": "Post"},
        )
        manifest = InventoryManifest(
            scope=InventoryScope.SOURCE,
            environment="test",
            base_url="https://example.test",
            observed_at=self.observed_at,
            records=[record],
            issues=[issue],
            metadata={"client": "synthetic"},
        )

        rendered = render_manifest_jsonl(manifest)
        self.assertEqual(rendered, render_manifest_jsonl(manifest))
        self.assertEqual(manifest_jsonl_sha256(manifest), manifest_jsonl_sha256(manifest))

        lines = [json.loads(line) for line in rendered.decode().splitlines()]
        self.assertEqual(
            [line["kind"] for line in lines],
            ["manifest_header", "record", "issue", "manifest_trailer"],
        )
        self.assertEqual(lines[-1]["content_sha256"], manifest.content_sha256)
        self.assertEqual(lines[-1]["manifest_sha256"], manifest.manifest_sha256)


class PaginationTests(unittest.TestCase):
    def test_complete_pages_are_merged_in_page_order(self) -> None:
        pages = [
            InventoryPage(PageMetadata(1, 2, 5, 3), ["a", "b"]),
            InventoryPage(PageMetadata(2, 2, 5, 3), ["c", "d"]),
            InventoryPage(PageMetadata(3, 2, 5, 3), ["e"]),
        ]
        self.assertEqual(merge_complete_pages(pages), ("a", "b", "c", "d", "e"))

    def test_missing_page_is_rejected(self) -> None:
        pages = [
            InventoryPage(PageMetadata(1, 2, 5, 3), ["a", "b"]),
            InventoryPage(PageMetadata(3, 2, 5, 3), ["e"]),
        ]
        with self.assertRaises(PaginationError):
            merge_complete_pages(pages)

    def test_incorrect_page_item_count_is_rejected(self) -> None:
        with self.assertRaises(PaginationError):
            InventoryPage(PageMetadata(1, 2, 5, 3), ["a"])

    def test_changed_totals_between_pages_are_rejected(self) -> None:
        pages = [
            InventoryPage(PageMetadata(1, 2, 4, 2), ["a", "b"]),
            InventoryPage(PageMetadata(2, 2, 3, 2), ["c"]),
        ]
        with self.assertRaises(PaginationError):
            merge_complete_pages(pages)

    def test_empty_inventory_has_one_empty_response_page(self) -> None:
        page = InventoryPage(PageMetadata(1, 100, 0, 0), [])
        self.assertEqual(merge_complete_pages([page]), ())


if __name__ == "__main__":
    unittest.main()
