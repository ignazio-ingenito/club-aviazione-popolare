from __future__ import annotations

import json
import unittest

import httpx

from directus_create_only import (
    DirectusCreateOnlyClient,
    DirectusCreateOnlyConfig,
    DirectusCreateOnlyEndpointError,
    DirectusCreateOnlyMethodError,
)


class DirectusCreateOnlyClientTests(unittest.TestCase):
    def make_client(self, handler):
        requests: list[httpx.Request] = []

        def recording_handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return handler(request)

        raw_client = httpx.Client(
            transport=httpx.MockTransport(recording_handler),
            follow_redirects=True,
        )
        self.addCleanup(raw_client.close)
        client = DirectusCreateOnlyClient(
            config=DirectusCreateOnlyConfig(
                base_url="https://directus.example.test",
                allowed_item_collections=("feeds", "migration_ledger"),
                auth_token="secret-token",
            ),
            http=raw_client,
        )
        return client, requests

    def test_create_only_client_rejects_patch_before_network_use(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, request=request)

        client, requests = self.make_client(handler)
        with self.assertRaises(DirectusCreateOnlyMethodError):
            client.request("PATCH", "/items/feeds/1")
        self.assertEqual(requests, [])

    def test_create_only_client_rejects_unallowed_post_endpoint(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, request=request)

        client, requests = self.make_client(handler)
        with self.assertRaises(DirectusCreateOnlyEndpointError):
            client.post("/items/categories", json={"title": "News"})
        self.assertEqual(requests, [])

    def test_create_only_client_allows_configured_create_endpoints(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["Authorization"], "Bearer secret-token")
            if request.url.path == "/items/feeds":
                self.assertEqual(request.method, "POST")
                self.assertEqual(json.loads(request.content), {"title": "Draft"})
                return httpx.Response(200, request=request, json={"data": {"id": 123}})
            if request.url.path == "/folders":
                self.assertEqual(request.method, "POST")
                self.assertEqual(json.loads(request.content), {"name": "Run-owned"})
                return httpx.Response(200, request=request, json={"data": {"id": "folder-1"}})
            if request.url.path == "/files":
                self.assertEqual(request.method, "POST")
                self.assertIn("multipart/form-data", request.headers["Content-Type"])
                self.assertIn(b"image.jpg", request.content)
                self.assertIn(b"binary-content", request.content)
                return httpx.Response(200, request=request, json={"data": {"id": "file-1"}})
            return httpx.Response(404, request=request)

        client, requests = self.make_client(handler)

        item = client.create_item("feeds", {"title": "Draft"})
        folder = client.create_folder("Run-owned")
        uploaded = client.upload_file(
            folder_id="folder-1",
            filename="image.jpg",
            content_type="image/jpeg",
            content=b"binary-content",
        )

        self.assertEqual(item["id"], 123)
        self.assertEqual(folder["id"], "folder-1")
        self.assertEqual(uploaded["id"], "file-1")
        self.assertEqual([request.method for request in requests], ["POST", "POST", "POST"])

    def test_empty_auth_token_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DirectusCreateOnlyConfig(
                base_url="https://directus.example.test",
                auth_token="   ",
            )


if __name__ == "__main__":
    unittest.main()
