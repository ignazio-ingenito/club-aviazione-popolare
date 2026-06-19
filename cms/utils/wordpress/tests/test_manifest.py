from __future__ import annotations

import unittest
from datetime import datetime, timezone

from inventory.errors import InventoryContractError
from inventory.models import InventoryIssue, InventoryManifest, ManifestRecord

UTC = timezone.utc


class ManifestTests(unittest.TestCase):
    def _record(
        self,
        object_id: str,
        *,
        images: list[str] | None = None,
        observed_at: datetime | None = None,
    ) -> ManifestRecord:
        return ManifestRecord(
            system="wordpress",
            object_type="post",
            object_id=object_id,
            canonical_url=f"https://example.test/{object_id}/",
            observed_at=observed_at or datetime(2026, 6, 19, 10, tzinfo=UTC),
            payload={"title": f"Post {object_id}", "images": images or []},
        )

    def test_content_hash_excludes_observation_timestamp(self) -> None:
        first = self._record("10", observed_at=datetime(2026, 6, 19, 10, tzinfo=UTC))
        second = self._record("10", observed_at=datetime(2026, 6, 20, 10, tzinfo=UTC))
        self.assertEqual(first.content_hash(), second.content_hash())

    def test_record_copies_and_freezes_nested_payload(self) -> None:
        payload = {"title": "Original", "images": ["a.jpg"]}
        record = ManifestRecord(
            system="wordpress",
            object_type="post",
            object_id="10",
            observed_at=datetime(2026, 6, 19, 10, tzinfo=UTC),
            payload=payload,
        )
        digest = record.content_hash()

        payload["title"] = "Changed"
        payload["images"].append("b.jpg")

        self.assertEqual(record.content_hash(), digest)
        self.assertEqual(record.payload["title"], "Original")
        self.assertEqual(record.payload["images"], ("a.jpg",))

    def test_gallery_sequence_is_hash_significant(self) -> None:
        first = self._record("gallery", images=["a.jpg", "b.jpg"])
        second = self._record("gallery", images=["b.jpg", "a.jpg"])
        self.assertNotEqual(first.content_hash(), second.content_hash())

    def test_manifest_hash_is_independent_of_record_and_issue_input_order(self) -> None:
        at = datetime(2026, 6, 19, 10, tzinfo=UTC)
        first_issue = InventoryIssue("wordpress:post:2", "missing_media", "Missing")
        second_issue = InventoryIssue("wordpress:post:1", "bad_url", "Invalid")
        first = InventoryManifest(
            manifest_type="source",
            environment="test",
            base_url="https://example.test",
            observed_at=at,
            records=(self._record("2"), self._record("1")),
            issues=(first_issue, second_issue),
        )
        second = InventoryManifest(
            manifest_type="source",
            environment="test",
            base_url="https://example.test",
            observed_at=at,
            records=(self._record("1"), self._record("2")),
            issues=(second_issue, first_issue),
        )
        self.assertEqual(first.artifact_hash(), second.artifact_hash())
        self.assertEqual(first.canonical_json(), second.canonical_json())

    def test_duplicate_record_identity_is_rejected(self) -> None:
        with self.assertRaises(InventoryContractError):
            InventoryManifest(
                manifest_type="source",
                environment="test",
                base_url="https://example.test",
                observed_at=datetime(2026, 6, 19, 10, tzinfo=UTC),
                records=(self._record("1"), self._record("1")),
            )

    def test_naive_observation_time_is_rejected(self) -> None:
        with self.assertRaises(InventoryContractError):
            ManifestRecord(
                system="wordpress",
                object_type="post",
                object_id="1",
                observed_at=datetime(2026, 6, 19, 10),
                payload={"title": "Post"},
            )

    def test_blank_identity_parts_are_rejected(self) -> None:
        with self.assertRaises(InventoryContractError):
            ManifestRecord(
                system=" ",
                object_type="post",
                object_id="1",
                observed_at=datetime(2026, 6, 19, 10, tzinfo=UTC),
                payload={"title": "Post"},
            )


if __name__ == "__main__":
    unittest.main()
