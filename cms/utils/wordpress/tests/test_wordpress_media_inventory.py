from __future__ import annotations

import unittest

import httpx

from inventory import IssueSeverity, WordPressReadOnlyClient
from tests.wordpress_fixtures import json_response


def media_record(*, source_url: str = "https://example.test/uploads/image.jpg") -> dict[str, object]:
    return {
        "id": 9,
        "type": "attachment",
        "slug": "image",
        "status": "inherit",
        "date": "2025-01-01T10:00:00",
        "date_gmt": "2025-01-01T09:00:00",
        "modified": "2025-01-01T10:00:00",
        "modified_gmt": "2025-01-01T09:00:00",
        "post": 1,
        "link": "https://example.test/image/",
        "title": {"rendered": "Image"},
        "caption": {"rendered": ""},
        "description": {"rendered": ""},
        "alt_text": "Featured",
        "media_type": "image",
        "mime_type": "image/jpeg",
        "source_url": source_url,
        "media_details": {"width": 1000, "height": 800},
    }


class WordPressMediaInventoryTests(unittest.TestCase):
    def test_media_metadata_is_normalized_without_downloading_binary(self) -> None:
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(
                    request,
                    [media_record()],
                    headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                )
            ),
        ) as client:
            result = client.fetch_media()

        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record.identity, "wordpress:media:9")
        self.assertEqual(record.data["mime_type"], "image/jpeg")
        self.assertEqual(record.data["media_details"]["width"], 1000)
        self.assertEqual(result.issues, ())

    def test_invalid_media_file_url_is_an_explicit_error(self) -> None:
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(
                    request,
                    [media_record(source_url="relative/image.jpg")],
                    headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                )
            ),
        ) as client:
            result = client.fetch_media()

        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.issues[0].code, "wordpress_media_invalid_source_url")
        self.assertIs(result.issues[0].severity, IssueSeverity.ERROR)


if __name__ == "__main__":
    unittest.main()
