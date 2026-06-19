from __future__ import annotations

import unittest

import httpx

from inventory import IssueSeverity, PaginationError, WordPressProtocolError, WordPressReadOnlyClient
from tests.wordpress_fixtures import json_response, post_record


class WordPressInventoryErrorTests(unittest.TestCase):
    def test_changed_pagination_totals_fail_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params["page"])
            if page == 1:
                return json_response(
                    request,
                    [post_record(1), post_record(2)],
                    headers={"X-WP-Total": "3", "X-WP-TotalPages": "2"},
                )
            return json_response(
                request,
                [post_record(3), post_record(4)],
                headers={"X-WP-Total": "4", "X-WP-TotalPages": "2"},
            )

        with WordPressReadOnlyClient(
            "https://example.test",
            per_page=2,
            transport=httpx.MockTransport(handler),
        ) as client:
            with self.assertRaises(PaginationError):
                client.fetch_posts()

    def test_missing_pagination_headers_fail_closed(self) -> None:
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(request, [post_record(1)])
            ),
        ) as client:
            with self.assertRaises(WordPressProtocolError):
                client.fetch_posts()

    def test_non_array_collection_payload_fails_closed(self) -> None:
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(
                    request,
                    {"id": 1},
                    headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                )
            ),
        ) as client:
            with self.assertRaises(WordPressProtocolError):
                client.fetch_posts()

    def test_malformed_record_becomes_explicit_issue(self) -> None:
        malformed = post_record(1)
        malformed["id"] = "not-an-integer"
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(
                    request,
                    [malformed],
                    headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                )
            ),
        ) as client:
            result = client.fetch_posts()

        self.assertEqual(result.records, ())
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].code, "wordpress_record_build_failed")
        self.assertIs(result.issues[0].severity, IssueSeverity.ERROR)

    def test_non_object_record_becomes_explicit_issue(self) -> None:
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(
                    request,
                    ["not-an-object"],
                    headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                )
            ),
        ) as client:
            result = client.fetch_posts()

        self.assertEqual(result.records, ())
        self.assertEqual(result.issues[0].code, "wordpress_invalid_record")

    def test_types_must_be_an_object(self) -> None:
        with WordPressReadOnlyClient(
            "https://example.test",
            transport=httpx.MockTransport(
                lambda request: json_response(request, [])
            ),
        ) as client:
            with self.assertRaises(WordPressProtocolError):
                client.fetch_types()


if __name__ == "__main__":
    unittest.main()
