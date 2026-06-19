from __future__ import annotations

from datetime import datetime, timezone
import unittest

import httpx

from inventory import IssueSeverity, WordPressReadOnlyClient
from tests.wordpress_fixtures import (
    category_record,
    json_response,
    post_record,
    types_payload,
)


class WordPressInventoryTests(unittest.TestCase):
    def test_collect_manifest_fetches_complete_inventory_with_get_only(self) -> None:
        seen: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append((request.method, request.url.path))
            path = request.url.path
            if path.endswith("/types"):
                return json_response(request, types_payload())
            if path.endswith("/categories"):
                return json_response(
                    request,
                    [category_record()],
                    headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                )
            if path.endswith("/posts"):
                page = int(request.url.params["page"])
                payload = [post_record(1), post_record(2)] if page == 1 else [post_record(3)]
                return json_response(
                    request,
                    payload,
                    headers={"X-WP-Total": "3", "X-WP-TotalPages": "2"},
                )
            if path.endswith("/media"):
                return json_response(
                    request,
                    [],
                    headers={"X-WP-Total": "0", "X-WP-TotalPages": "0"},
                )
            raise AssertionError(path)

        with WordPressReadOnlyClient(
            "https://example.test",
            per_page=2,
            transport=httpx.MockTransport(handler),
        ) as client:
            manifest = client.collect_manifest(
                environment="test",
                observed_at=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc),
            )

        self.assertTrue(all(method == "GET" for method, _ in seen))
        self.assertEqual(
            [record.identity for record in manifest.records],
            [
                "wordpress:category:6",
                "wordpress:media:9",
                "wordpress:post:1",
                "wordpress:post:2",
                "wordpress:post:3",
                "wordpress:type:attachment",
                "wordpress:type:post",
            ],
        )
        post = next(record for record in manifest.records if record.identity == "wordpress:post:1")
        self.assertEqual(post.data["categories"], (3, 6))
        self.assertEqual(
            post.data["html_references"]["images"][0]["src"],
            "https://example.test/image.jpg",
        )
        self.assertEqual(
            post.data["html_references"]["links"][0]["href"],
            "https://example.test/file.pdf",
        )
        self.assertEqual(
            manifest.metadata["collections"]["posts"]["api_total_items"],
            3,
        )
        self.assertEqual(len([path for _, path in seen if path.endswith("/posts")]), 2)

    def test_fetch_is_fresh_by_default(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return json_response(
                request,
                [post_record(1)],
                headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
            )

        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(handler),
        ) as client:
            client.fetch_posts()
            client.fetch_posts()
        self.assertEqual(calls, 2)

    def test_empty_collection_is_valid(self) -> None:
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(
                    request,
                    [],
                    headers={"X-WP-Total": "0", "X-WP-TotalPages": "0"},
                )
            ),
        ) as client:
            result = client.fetch_media()

        self.assertEqual(result.records, ())
        self.assertEqual(result.issues, ())
        self.assertEqual(result.total_items, 0)
        self.assertEqual(result.total_pages, 0)

    def test_empty_slug_and_title_are_explicit_warnings(self) -> None:
        source = post_record(1, slug="", title="")
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(
                    request,
                    [source],
                    headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                )
            ),
        ) as client:
            result = client.fetch_posts()

        self.assertEqual(len(result.records), 1)
        self.assertEqual(
            {issue.code for issue in result.issues},
            {"wordpress_post_missing_slug", "wordpress_post_empty_title"},
        )
        self.assertTrue(
            all(issue.severity is IssueSeverity.WARNING for issue in result.issues)
        )

    def test_per_page_is_validated(self) -> None:
        for value in (0, 101, True, 1.5):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    WordPressReadOnlyClient("https://example.test", per_page=value)


if __name__ == "__main__":
    unittest.main()
