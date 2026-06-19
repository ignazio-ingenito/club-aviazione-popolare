from __future__ import annotations

import unittest
from datetime import datetime, timezone
from typing import Any

import httpx

from inventory.errors import PaginationContractError, ResponseContractError
from inventory.wordpress_client import WordPressInventoryClient

UTC = timezone.utc
OBSERVED_AT = datetime(2026, 6, 19, 10, tzinfo=UTC)


def _post(post_id: int, title: str, *, content: str = "<p>Test</p>") -> dict[str, Any]:
    return {
        "id": post_id,
        "date": "2025-01-01T10:00:00",
        "date_gmt": "2025-01-01T09:00:00",
        "modified": "2025-01-02T10:00:00",
        "modified_gmt": "2025-01-02T09:00:00",
        "guid": {"rendered": f"https://legacy.test/?p={post_id}"},
        "link": f"https://example.test/post-{post_id}/",
        "slug": f"post-{post_id}",
        "status": "publish",
        "type": "post",
        "title": {"rendered": title},
        "excerpt": {"rendered": "Excerpt"},
        "content": {"rendered": content},
        "author": 2,
        "featured_media": 20,
        "categories": [6, 3, 6],
        "tags": [4, 2],
        "_embedded": {
            "wp:featuredmedia": [
                {
                    "id": 20,
                    "source_url": "https://example.test/wp-content/uploads/cover.jpg",
                    "alt_text": "Cover",
                    "mime_type": "image/jpeg",
                    "media_type": "image",
                }
            ]
        },
    }


def _category(category_id: int, name: str) -> dict[str, Any]:
    return {
        "id": category_id,
        "count": 1,
        "description": "",
        "link": f"https://example.test/category/{category_id}/",
        "name": name,
        "slug": name.lower().replace(" ", "-"),
        "taxonomy": "category",
        "parent": 0,
    }


def _media(media_id: int) -> dict[str, Any]:
    return {
        "id": media_id,
        "date": "2025-01-01T10:00:00",
        "date_gmt": "2025-01-01T09:00:00",
        "modified": "2025-01-01T10:00:00",
        "modified_gmt": "2025-01-01T09:00:00",
        "link": f"https://example.test/media/{media_id}/",
        "slug": f"media-{media_id}",
        "status": "inherit",
        "type": "attachment",
        "title": {"rendered": "Media"},
        "author": 2,
        "caption": {"rendered": "Caption"},
        "description": {"rendered": "Description"},
        "alt_text": "Alternative",
        "media_type": "image",
        "mime_type": "image/jpeg",
        "source_url": "https://example.test/wp-content/uploads/media.jpg",
        "media_details": {"width": 1200, "height": 800},
        "post": 10,
    }


def _paged_response(
    request: httpx.Request,
    items: list[dict[str, Any]],
    *,
    total: int,
    total_pages: int,
) -> httpx.Response:
    return httpx.Response(
        200,
        json=items,
        headers={
            "X-WP-Total": str(total),
            "X-WP-TotalPages": str(total_pages),
        },
        request=request,
    )


class WordPressInventoryClientTests(unittest.TestCase):
    def test_build_manifest_uses_complete_get_only_pagination(self) -> None:
        requests: list[httpx.Request] = []
        content = (
            '<p><img src="/wp-content/uploads/a.jpg" '
            'srcset="/wp-content/uploads/a-300.jpg 300w, '
            'https://cdn.test/a.jpg 800w"></p>'
            '<p><a href="/wp-content/uploads/manual.pdf">Manual</a></p>'
        )
        posts = [_post(10, "Ten", content=content), _post(11, "Eleven"), _post(12, "Twelve")]
        categories = [_category(3, "Eventi"), _category(5, "Corsi"), _category(6, "News")]

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            path = request.url.path
            page = int(request.url.params.get("page", "1"))
            if path.endswith("/types"):
                return httpx.Response(
                    200,
                    json={
                        "attachment": {
                            "name": "Media",
                            "slug": "attachment",
                            "rest_base": "media",
                            "rest_namespace": "wp/v2",
                            "hierarchical": False,
                            "taxonomies": [],
                            "supports": {},
                        },
                        "post": {
                            "name": "Posts",
                            "slug": "post",
                            "rest_base": "posts",
                            "rest_namespace": "wp/v2",
                            "hierarchical": False,
                            "taxonomies": ["category", "post_tag"],
                            "supports": {"title": True},
                        },
                    },
                    request=request,
                )
            if path.endswith("/categories"):
                page_items = categories[(page - 1) * 2 : page * 2]
                return _paged_response(request, page_items, total=3, total_pages=2)
            if path.endswith("/posts"):
                page_items = posts[(page - 1) * 2 : page * 2]
                return _paged_response(request, page_items, total=3, total_pages=2)
            if path.endswith("/media"):
                return _paged_response(request, [_media(20)], total=1, total_pages=1)
            return httpx.Response(404, request=request)

        with WordPressInventoryClient(
            "https://example.test",
            per_page=2,
            transport=httpx.MockTransport(handler),
        ) as client:
            manifest = client.build_manifest(
                environment="test",
                observed_at=OBSERVED_AT,
            )

        self.assertEqual(len(manifest.records), 9)
        self.assertEqual(manifest.issues, ())
        self.assertEqual(manifest.metadata["collection_counts"]["posts"], 3)
        self.assertEqual({request.method for request in requests}, {"GET"})

        post_record = next(
            record for record in manifest.records if record.identity == "wordpress:post:10"
        )
        self.assertEqual(post_record.payload["categories"], (3, 6))
        self.assertEqual(post_record.payload["tags"], (2, 4))
        self.assertEqual(
            post_record.payload["image_urls"],
            (
                "https://example.test/wp-content/uploads/a.jpg",
                "https://example.test/wp-content/uploads/a-300.jpg",
                "https://cdn.test/a.jpg",
            ),
        )
        self.assertEqual(
            post_record.payload["linked_media_urls"],
            ("https://example.test/wp-content/uploads/manual.pdf",),
        )
        self.assertEqual(
            post_record.payload["featured_media"]["source_url"],
            "https://example.test/wp-content/uploads/cover.jpg",
        )

        post_requests = [request for request in requests if request.url.path.endswith("/posts")]
        self.assertEqual(len(post_requests), 2)
        self.assertTrue(all(request.url.params["orderby"] == "id" for request in post_requests))
        self.assertTrue(all(request.url.params["order"] == "asc" for request in post_requests))
        self.assertTrue(all(request.url.params["status"] == "publish" for request in post_requests))
        self.assertTrue(all(request.url.params["per_page"] == "2" for request in post_requests))

    def test_malformed_source_record_becomes_explicit_issue(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return _paged_response(
                request,
                [_post(10, "Valid"), {"link": "https://example.test/bad/"}],
                total=2,
                total_pages=1,
            )

        with WordPressInventoryClient(
            "https://example.test",
            per_page=2,
            transport=httpx.MockTransport(handler),
        ) as client:
            batch = client.fetch_posts(observed_at=OBSERVED_AT)

        self.assertEqual(len(batch.records), 1)
        self.assertEqual(len(batch.issues), 1)
        self.assertEqual(batch.issues[0].code, "invalid_source_record")
        self.assertEqual(batch.issues[0].object_ref, "wordpress:post:index-1")

    def test_client_does_not_cache_responses(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return _paged_response(
                request,
                [_post(10, f"Version {calls}")],
                total=1,
                total_pages=1,
            )

        with WordPressInventoryClient(
            "https://example.test",
            transport=httpx.MockTransport(handler),
        ) as client:
            first = client.fetch_posts(observed_at=OBSERVED_AT)
            second = client.fetch_posts(observed_at=OBSERVED_AT)

        self.assertEqual(calls, 2)
        self.assertNotEqual(first.records[0].content_hash(), second.records[0].content_hash())

    def test_missing_pagination_headers_fail_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[_post(10, "Ten")], request=request)

        with WordPressInventoryClient(
            "https://example.test",
            transport=httpx.MockTransport(handler),
        ) as client:
            with self.assertRaises(PaginationContractError):
                client.fetch_posts(observed_at=OBSERVED_AT)

    def test_non_array_collection_response_is_rejected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"id": 10}, request=request)

        with WordPressInventoryClient(
            "https://example.test",
            transport=httpx.MockTransport(handler),
        ) as client:
            with self.assertRaises(ResponseContractError):
                client.fetch_posts(observed_at=OBSERVED_AT)

    def test_invalid_per_page_is_rejected(self) -> None:
        for per_page in (0, 101):
            with self.subTest(per_page=per_page):
                with self.assertRaises(ValueError):
                    WordPressInventoryClient("https://example.test", per_page=per_page)


if __name__ == "__main__":
    unittest.main()
