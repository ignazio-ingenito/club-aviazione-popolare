from __future__ import annotations

from datetime import datetime, timezone
import json
import unittest

import httpx

from inventory.directus import (
    DirectusHttpError,
    DirectusInventoryClient,
    DirectusInventoryConfig,
    DirectusProtocolError,
    CATEGORY_FIELDS,
    FEED_FIELDS,
)
from inventory.http import ReadOnlyHttpClient, ReadOnlyMethodError
from inventory.models import InventoryScope, IssueSeverity


class DirectusInventoryClientTests(unittest.TestCase):
    def make_client(self, handler, *, limit: int = 2):
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
        client = DirectusInventoryClient(
            config=DirectusInventoryConfig(
                base_url="https://directus.example.test",
                limit=limit,
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
        status_code: int = 200,
    ) -> httpx.Response:
        return httpx.Response(
            status_code,
            request=request,
            json={
                "data": payload,
                "meta": {
                    "filter_count": total,
                    "total_count": total,
                },
            },
        )

    def test_transport_rejects_write_method_before_network_use(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, request=request)

        _, readonly, requests = self.make_client(handler)
        with self.assertRaises(ReadOnlyMethodError):
            readonly.request("PATCH", "https://directus.example.test/items/feeds/1")
        self.assertEqual(requests, [])

    def test_auth_token_is_sent_as_bearer_header(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["Authorization"], "Bearer secret-token")
            return httpx.Response(
                200,
                request=request,
                json={"data": {"version": "x"}},
            )

        client, _, _ = self.make_client(handler)
        client.config = DirectusInventoryConfig(
            base_url="https://directus.example.test",
            limit=2,
            auth_token="secret-token",
        )

        result = client.get_server_info()
        self.assertEqual(result.records[0].identity, "directus:server:info")

    def test_feeds_fetch_all_pages_with_stable_query(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/items/feeds")
            self.assertEqual(request.url.params["limit"], "2")
            self.assertEqual(request.url.params["sort"], "id")
            self.assertEqual(request.url.params["meta"], "filter_count,total_count")
            requested_fields = set(request.url.params["fields"].split(","))
            self.assertTrue(set(FEED_FIELDS).issubset(requested_fields))
            self.assertNotIn("modified_on", requested_fields)
            offset = int(request.url.params["offset"])
            payload = {
                0: [
                    {"id": 1, "slug": "one", "status": "published"},
                    {"id": 2, "slug": "two", "status": "draft"},
                ],
                2: [{"id": 3, "slug": "three", "status": "archived"}],
            }[offset]
            return self.paginated_response(request, payload, total=3)

        client, _, requests = self.make_client(handler)
        result = client.get_feeds()

        self.assertEqual(len(requests), 2)
        self.assertEqual(result.total_items, 3)
        self.assertEqual(result.total_pages, 2)
        self.assertEqual(result.raw_item_count, 3)
        self.assertEqual(
            [record.identity for record in result.records],
            ["directus:feed:1", "directus:feed:2", "directus:feed:3"],
        )
        self.assertEqual(result.issues, ())

    def test_categories_fetch_application_route_fields(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.url.path, "/items/categories")
            self.assertEqual(request.url.params["sort"], "key")
            requested_fields = set(request.url.params["fields"].split(","))
            self.assertEqual(
                requested_fields,
                {
                    "key",
                    "title",
                    "description",
                    "status",
                    "sort",
                    "date_created",
                    "date_updated",
                },
            )
            self.assertEqual(set(CATEGORY_FIELDS), requested_fields)
            return self.paginated_response(
                request,
                [{"key": "news", "title": "News"}],
                total=1,
            )

        client, _, _ = self.make_client(handler)
        result = client.get_categories()

        self.assertEqual(result.records[0].identity, "directus:category:news")
        self.assertEqual(result.issues, ())

    def test_inaccessible_endpoint_becomes_fatal_target_issue(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, request=request, text="not json")

        client, _, requests = self.make_client(handler)
        result = client.get_fields()

        self.assertEqual(len(requests), 1)
        self.assertEqual(result.records, ())
        self.assertEqual(result.total_items, 0)
        self.assertEqual(result.issues[0].code, "directus_endpoint_inaccessible")
        self.assertEqual(result.issues[0].severity, IssueSeverity.FATAL)
        self.assertEqual(result.issues[0].scope, InventoryScope.TARGET)

    def test_server_info_singleton_record(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.path, "/server/info")
            return httpx.Response(
                200,
                request=request,
                json={"data": {"project": {"project_name": "CAP"}, "directus": {"version": "11"}}},
            )

        client, _, _ = self.make_client(handler)
        result = client.get_server_info()

        self.assertEqual(result.total_items, 1)
        self.assertEqual(result.records[0].identity, "directus:server:info")
        self.assertEqual(result.records[0].data["project"]["project_name"], "CAP")

    def test_system_metadata_records_stable_identities(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payloads = {
                "/collections": {
                    "data": [{"collection": "feeds"}, {"collection": "categories"}]
                },
                "/fields": {
                    "data": [
                        {"collection": "feeds", "field": "slug"},
                        {"collection": "feeds", "field": "gallery"},
                    ]
                },
                "/relations": {
                    "data": [
                        {
                            "collection": "feeds",
                            "field": "category",
                            "related_collection": "categories",
                            "related_field": "id",
                        }
                    ]
                },
            }
            return httpx.Response(200, request=request, json=payloads[request.url.path])

        client, _, _ = self.make_client(handler)

        self.assertEqual(
            [record.identity for record in client.get_collections().records],
            ["directus:collection:feeds", "directus:collection:categories"],
        )
        self.assertEqual(
            [record.identity for record in client.get_fields().records],
            ["directus:field:feeds.slug", "directus:field:feeds.gallery"],
        )
        self.assertEqual(
            [record.identity for record in client.get_relations().records],
            ["directus:relation:feeds.category->categories.id"],
        )

    def test_core_snapshot_builds_target_manifest_and_uses_get_only(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            if request.url.path == "/server/info":
                return httpx.Response(200, request=request, json={"data": {"version": "x"}})
            if request.url.path in {"/permissions/me", "/collections", "/fields", "/relations"}:
                return httpx.Response(403, request=request, json={"errors": []})
            payloads = {
                "/items/feeds": [{"id": 1, "slug": "one"}],
                "/items/categories": [{"key": "news", "title": "News"}],
                "/files": [{"id": "file-1", "filename_disk": "a.jpg"}],
                "/folders": [{"id": "folder-1", "name": "gallery"}],
            }
            return self.paginated_response(
                request,
                payloads[request.url.path],
                total=1,
            )

        client, _, requests = self.make_client(handler)
        snapshot = client.inventory_core()
        manifest = snapshot.to_manifest(
            environment="synthetic",
            observed_at=datetime(2026, 6, 19, 15, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(len(requests), 9)
        self.assertTrue(all(request.method == "GET" for request in requests))
        self.assertEqual(manifest.scope, InventoryScope.TARGET)
        self.assertEqual(len(manifest.records), 5)
        self.assertEqual(len(manifest.issues), 4)
        self.assertEqual(
            {issue.code for issue in manifest.issues},
            {"directus_endpoint_inaccessible"},
        )
        self.assertEqual(
            set(manifest.metadata["endpoints"].keys()),
            {
                "server/info",
                "permissions/me",
                "collections",
                "fields",
                "relations",
                "items/feeds",
                "items/categories",
                "files",
                "folders",
            },
        )
        json.dumps(manifest.to_dict())

    def test_inventory_is_fresh_without_implicit_cache(self) -> None:
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return self.paginated_response(
                request,
                [{"id": call_count, "name": f"folder-{call_count}"}],
                total=1,
            )

        client, _, _ = self.make_client(handler)
        first = client.get_folders()
        second = client.get_folders()

        self.assertEqual(call_count, 2)
        self.assertEqual(first.records[0].identity, "directus:folder:1")
        self.assertEqual(second.records[0].identity, "directus:folder:2")

    def test_missing_pagination_meta_fails_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, request=request, json={"data": []})

        client, _, _ = self.make_client(handler)
        with self.assertRaises(DirectusProtocolError) as captured:
            client.get_files()
        self.assertEqual(captured.exception.code, "missing_pagination_meta")
        self.assertEqual(captured.exception.to_issue().severity, IssueSeverity.FATAL)

    def test_inconsistent_total_count_fails_closed(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                request=request,
                json={
                    "data": [],
                    "meta": {"filter_count": 0, "total_count": 1},
                },
            )

        client, _, _ = self.make_client(handler)
        with self.assertRaises(DirectusProtocolError) as captured:
            client.get_folders()
        self.assertEqual(captured.exception.code, "inconsistent_pagination")

    def test_http_error_is_fatal_and_does_not_include_body(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, request=request, text="private upstream response")

        client, _, _ = self.make_client(handler)
        with self.assertRaises(DirectusHttpError) as captured:
            client.get_server_info()
        issue = captured.exception.to_issue()
        self.assertEqual(issue.severity, IssueSeverity.FATAL)
        self.assertEqual(issue.details["status_code"], 503)
        self.assertNotIn("private upstream response", json.dumps(issue.to_dict()))

    def test_invalid_json_fails_closed_without_response_body_in_issue(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                request=request,
                headers={"Content-Type": "application/json"},
                content=b"not-json",
            )

        client, _, _ = self.make_client(handler)
        with self.assertRaises(DirectusProtocolError) as captured:
            client.get_server_info()
        issue = captured.exception.to_issue()
        self.assertEqual(issue.code, "invalid_json")
        self.assertNotIn("not-json", json.dumps(issue.to_dict()))

    def test_invalid_config_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DirectusInventoryConfig(base_url="relative/path")
        with self.assertRaises(ValueError):
            DirectusInventoryConfig(
                base_url="https://directus.example.test", limit=101
            )
        with self.assertRaises(ValueError):
            DirectusInventoryConfig(
                base_url="https://directus.example.test",
                auth_token="   ",
            )


if __name__ == "__main__":
    unittest.main()
