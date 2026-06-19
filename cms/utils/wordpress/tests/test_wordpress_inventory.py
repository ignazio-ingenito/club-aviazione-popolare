from __future__ import annotations

from datetime import datetime, timezone
import json
import unittest

import httpx

from inventory.http import ReadOnlyHttpClient, ReadOnlyMethodError
from inventory.models import InventoryScope, IssueSeverity
from inventory.wordpress import (
    WordPressHttpError,
    WordPressInventoryClient,
    WordPressInventoryConfig,
    WordPressProtocolError,
)


class WordPressInventoryClientTests(unittest.TestCase):
    def make_client(self, handler, *, per_page: int = 2):
        requests: list[httpx.Request] = []

        def recording_handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return handler(request)

        raw_client = httpx.Client(
            transport=httpx.MockTransport(recording_handler),
            follow_redirects=True,
        )
        self.addCleanup(raw_client.close)
        readonly = ReadOnlyHttpClient(client=raw_client)
        client = WordPressInventoryClient(
            config=WordPressInventoryConfig(
                base_url="https://wordpress.example.test",
                per_page=per_page,
            ),
            http=readonly,
        )
        return client, readonly, requests

    @staticmethod
    def paginated_response(
        request: httpx.Request,
        payload,
        *,
        total: int,
        total_pages: int,
        status_code: int = 200,
    ) -> httpx.Response:
        return httpx.Response(
            status_code,
            request=request,
            headers={
                "X-WP-Total": str(total),
                "X-WP-TotalPages": str(total_pages),
            },
            json=payload,
        )

    def test_transport_rejects_write_method_before_network_use(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, request=request)

        _, readonly, requests = self.make_client(handler)
        with self.assertRaises(ReadOnlyMethodError):
            readonly.request("POST", "https://wordpress.example.test/wp-json/wp/v2/posts")
        self.assertEqual(requests, [])

    def test_categories_fetch_all_pages_with_stable_query(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/wp-json/wp/v2/categories")
            self.assertEqual(request.url.params["context"], "view")
            self.assertEqual(request.url.params["per_page"], "2")
            self.assertEqual(request.url.params["orderby"], "id")
            self.assertEqual(request.url.params["order"], "asc")
            self.assertEqual(request.url.params["hide_empty"], "false")
            page = int(request.url.params["page"])
            payload = {
                1: [
                    {"id": 3, "slug": "eventi", "link": "https://wordpress.example.test/eventi/"},
                    {"id": 5, "slug": "corsi", "link": "https://wordpress.example.test/corsi/"},
                ],
                2: [
                    {"id": 6, "slug": "news", "link": "https://wordpress.example.test/news/"},
                ],
            }[page]
            return self.paginated_response(
                request, payload, total=3, total_pages=2
            )

        client, _, requests = self.make_client(handler)
        result = client.get_categories()

        self.assertEqual(len(requests), 2)
        self.assertEqual(result.total_items, 3)
        self.assertEqual(result.total_pages, 2)
        self.assertEqual(result.raw_item_count, 3)
        self.assertEqual(
            [record.identity for record in result.records],
            [
                "wordpress:category:3",
                "wordpress:category:5",
                "wordpress:category:6",
            ],
        )
        self.assertEqual(result.issues, ())

    def test_posts_are_fetched_fresh_without_implicit_cache(self) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            self.assertEqual(request.url.params["status"], "publish")
            self.assertEqual(request.url.params["_embed"], "1")
            return self.paginated_response(
                request,
                [
                    {
                        "id": 10,
                        "slug": "post",
                        "link": "https://wordpress.example.test/post/",
                        "title": {"rendered": f"Version {call_count}"},
                    }
                ],
                total=1,
                total_pages=1,
            )

        client, _, _ = self.make_client(handler)
        first = client.get_posts()
        second = client.get_posts()

        self.assertEqual(call_count, 2)
        self.assertEqual(first.records[0].data["title"]["rendered"], "Version 1")
        self.assertEqual(second.records[0].data["title"]["rendered"], "Version 2")

    def test_empty_collection_is_valid(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return self.paginated_response(
                request, [], total=0, total_pages=0
            )

        client, _, requests = self.make_client(handler)
        result = client.get_posts()
        self.assertEqual(len(requests), 1)
        self.assertEqual(result.records, ())
        self.assertEqual(result.issues, ())
        self.assertEqual(result.total_items, 0)
        self.assertEqual(result.total_pages, 0)

    def test_missing_pagination_headers_fail_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, request=request, json=[])

        client, _, _ = self.make_client(handler)
        with self.assertRaises(WordPressProtocolError) as captured:
            client.get_posts()
        self.assertEqual(captured.exception.code, "missing_pagination_headers")
        self.assertEqual(
            captured.exception.to_issue().severity, IssueSeverity.FATAL
        )

    def test_inconsistent_totals_between_pages_fail_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            page = int(request.url.params["page"])
            if page == 1:
                return self.paginated_response(
                    request,
                    [{"id": 1}, {"id": 2}],
                    total=3,
                    total_pages=2,
                )
            return self.paginated_response(
                request,
                [{"id": 3}, {"id": 4}],
                total=4,
                total_pages=2,
            )

        client, _, _ = self.make_client(handler)
        with self.assertRaises(WordPressProtocolError) as captured:
            client.get_media()
        self.assertEqual(captured.exception.code, "incomplete_pagination")

    def test_invalid_json_fails_closed_without_response_body_in_issue(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                request=request,
                headers={"Content-Type": "application/json"},
                content=b"not-json",
            )

        client, _, _ = self.make_client(handler)
        with self.assertRaises(WordPressProtocolError) as captured:
            client.get_types()
        issue = captured.exception.to_issue()
        self.assertEqual(issue.code, "invalid_json")
        self.assertNotIn("not-json", json.dumps(issue.to_dict()))

    def test_wrong_json_shape_fails_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                request=request,
                headers={"X-WP-Total": "1", "X-WP-TotalPages": "1"},
                json={"id": 1},
            )

        client, _, _ = self.make_client(handler)
        with self.assertRaises(WordPressProtocolError) as captured:
            client.get_categories()
        self.assertEqual(captured.exception.code, "invalid_json_shape")

    def test_http_error_is_fatal_and_does_not_include_body(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                503,
                request=request,
                text="private upstream response",
            )

        client, _, _ = self.make_client(handler)
        with self.assertRaises(WordPressHttpError) as captured:
            client.get_types()
        issue = captured.exception.to_issue()
        self.assertEqual(issue.severity, IssueSeverity.FATAL)
        self.assertEqual(issue.details["status_code"], 503)
        self.assertNotIn("private upstream response", json.dumps(issue.to_dict()))

    def test_malformed_items_are_explicit_issues(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return self.paginated_response(
                request,
                [
                    {
                        "id": 7,
                        "slug": "valid",
                        "link": "https://wordpress.example.test/valid/",
                    },
                    {"id": 0, "slug": "invalid"},
                ],
                total=2,
                total_pages=1,
            )

        client, _, _ = self.make_client(handler)
        result = client.get_posts()
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.raw_item_count, 2)
        self.assertEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].code, "invalid_wordpress_id")
        self.assertEqual(result.issues[0].severity, IssueSeverity.ERROR)

    def test_invalid_source_url_is_warning_but_record_is_preserved(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return self.paginated_response(
                request,
                [{"id": 9, "link": "/relative-only"}],
                total=1,
                total_pages=1,
            )

        client, _, _ = self.make_client(handler)
        result = client.get_posts()
        self.assertEqual(len(result.records), 1)
        self.assertIsNone(result.records[0].source_url)
        self.assertEqual(result.issues[0].code, "invalid_source_url")
        self.assertEqual(result.issues[0].severity, IssueSeverity.WARNING)
        self.assertEqual(result.issues[0].identity, "wordpress:post:9")

    def test_types_create_records_and_malformed_type_issue(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                request=request,
                json={
                    "post": {"slug": "post", "rest_base": "posts"},
                    "broken": ["not", "an", "object"],
                },
            )

        client, _, _ = self.make_client(handler)
        result = client.get_types()
        self.assertEqual(result.total_items, 2)
        self.assertEqual(
            [record.identity for record in result.records],
            ["wordpress:type:post"],
        )
        self.assertEqual(result.issues[0].code, "malformed_wordpress_type")

    def test_core_snapshot_builds_source_manifest_and_uses_get_only(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            endpoint = request.url.path.rsplit("/", 1)[-1]
            if endpoint == "types":
                return httpx.Response(
                    200,
                    request=request,
                    json={"post": {"slug": "post", "rest_base": "posts"}},
                )
            payloads = {
                "categories": [{"id": 3, "link": "https://wordpress.example.test/cat/"}],
                "posts": [{"id": 10, "link": "https://wordpress.example.test/post/"}],
                "media": [{"id": 20, "source_url": "https://wordpress.example.test/media.jpg"}],
            }
            if endpoint == "media":
                self.assertNotIn("status", request.url.params)
                self.assertNotIn("orderby", request.url.params)
            return self.paginated_response(
                request,
                payloads[endpoint],
                total=1,
                total_pages=1,
            )

        client, _, requests = self.make_client(handler)
        snapshot = client.inventory_core()
        manifest = snapshot.to_manifest(
            environment="synthetic",
            observed_at=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(requests), 4)
        self.assertTrue(all(request.method == "GET" for request in requests))
        self.assertEqual(manifest.scope, InventoryScope.SOURCE)
        self.assertEqual(len(manifest.records), 4)
        self.assertEqual(manifest.issues, ())
        self.assertEqual(
            set(manifest.metadata["endpoints"].keys()),
            {"types", "categories", "posts", "media"},
        )
        json.dumps(manifest.to_dict())

    def test_invalid_config_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WordPressInventoryConfig(base_url="relative/path")
        with self.assertRaises(ValueError):
            WordPressInventoryConfig(
                base_url="https://wordpress.example.test", per_page=101
            )


if __name__ == "__main__":
    unittest.main()
