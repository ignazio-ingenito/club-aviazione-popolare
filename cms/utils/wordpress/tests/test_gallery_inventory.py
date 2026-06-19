from __future__ import annotations

from datetime import datetime, timezone
import unittest

import httpx

from inventory.gallery import WordPressGalleryDiscoveryClient
from inventory.http import ReadOnlyHttpClient, ReadOnlyMethodError
from inventory.models import InventoryScope, IssueSeverity
from inventory.wordpress import WordPressInventoryConfig


class GalleryDiscoveryClientTests(unittest.TestCase):
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
        readonly = ReadOnlyHttpClient(client=raw_client)
        client = WordPressGalleryDiscoveryClient(
            config=WordPressInventoryConfig(
                base_url="https://wordpress.example.test",
                per_page=2,
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

    def test_exposed_gallery_rest_type_is_used_before_html_fallback(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            if request.url.path.endswith("/types"):
                return httpx.Response(
                    200,
                    request=request,
                    json={
                        "post": {"slug": "post", "rest_base": "posts"},
                        "dt_gallery": {
                            "slug": "dt_gallery",
                            "rest_base": "dt-gallery",
                            "name": "Gallery",
                        },
                    },
                )
            self.assertEqual(request.url.path, "/wp-json/wp/v2/dt-gallery")
            self.assertEqual(request.url.params["_embed"], "1")
            return self.paginated_response(
                request,
                [
                    {
                        "id": 42,
                        "slug": "album-rest",
                        "link": "https://wordpress.example.test/dt-gallery/album-rest/",
                        "content": {
                            "rendered": """
                            <figure>
                              <a href="/wp-content/uploads/full-b.jpg">
                                <img src="/wp-content/uploads/thumb-b.jpg" alt="B">
                              </a>
                              <figcaption>Second source item</figcaption>
                            </figure>
                            """
                        },
                    }
                ],
                total=1,
                total_pages=1,
            )

        client, _, requests = self.make_client(handler)
        discovery = client.discover()

        self.assertEqual(discovery.method, "rest")
        self.assertEqual(discovery.rest_endpoint, "dt-gallery")
        self.assertEqual(len(requests), 2)
        self.assertEqual(discovery.result.endpoint, "dt-gallery")
        self.assertEqual(discovery.result.issues, ())
        record = discovery.result.records[0]
        self.assertEqual(record.identity, "wordpress:gallery:42")
        self.assertEqual(record.data["discovery_method"], "rest")
        self.assertEqual(record.data["images"][0]["source_url"], "https://wordpress.example.test/wp-content/uploads/full-b.jpg")
        self.assertEqual(record.data["images"][0]["caption"], "Second source item")

    def test_gallery_rest_type_detection_handles_loose_type_metadata(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/types"):
                return httpx.Response(
                    200,
                    request=request,
                    json={
                        "album": {
                            "slug": "album",
                            "rest_base": "album",
                            "rewrite": "not-an-object",
                            "description": "Public gallery albums",
                        },
                    },
                )
            self.assertEqual(request.url.path, "/wp-json/wp/v2/album")
            return self.paginated_response(
                request,
                [{"id": 9, "slug": "album", "link": "https://wordpress.example.test/dt-gallery/album/"}],
                total=1,
                total_pages=1,
            )

        client, _, _ = self.make_client(handler)
        discovery = client.discover()

        self.assertEqual(discovery.method, "rest")
        self.assertEqual(discovery.rest_endpoint, "album")
        self.assertEqual(discovery.result.records[0].identity, "wordpress:gallery:9")

    def test_public_html_fallback_preserves_archive_and_dom_order(self) -> None:
        archive_html = """
        <main>
          <a href="/dt-gallery/ozzano-2021/"><img src="/covers/ozzano.jpg" alt="Ozzano">49 Raduno</a>
          <a href="/dt-gallery/foto-recenti/">Foto recenti</a>
          <a href="/dt-gallery/ozzano-2021/">duplicate ignored</a>
        </main>
        """
        album_ozzano = """
        <article>
          <a href="/wp-content/uploads/IMG_3161.jpg"><img src="/wp-content/uploads/IMG_3161-150x150.jpg" alt="IMG 3161"></a>
          <a href="/wp-content/uploads/IMG_3175.jpg"><img src="/wp-content/uploads/IMG_3175-150x150.jpg" alt="IMG 3175"></a>
          <a href="/wp-content/uploads/IMG_3174.jpg"><img src="/wp-content/uploads/IMG_3174-150x150.jpg" alt="IMG 3174"></a>
        </article>
        """
        album_recenti = """
        <article>
          <figure>
            <img src="/wp-content/uploads/recent-a.jpg" title="Recent A">
            <figcaption>Recent caption</figcaption>
          </figure>
        </article>
        """

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            if request.url.path.endswith("/types"):
                return httpx.Response(
                    200,
                    request=request,
                    json={"post": {"slug": "post", "rest_base": "posts"}},
                )
            if request.url.path == "/gallery/":
                return httpx.Response(200, request=request, text=archive_html)
            if request.url.path == "/dt-gallery/ozzano-2021/":
                return httpx.Response(200, request=request, text=album_ozzano)
            if request.url.path == "/dt-gallery/foto-recenti/":
                return httpx.Response(200, request=request, text=album_recenti)
            return httpx.Response(404, request=request)

        client, _, requests = self.make_client(handler)
        discovery = client.discover()

        self.assertEqual(discovery.method, "public_html")
        self.assertTrue(all(request.method == "GET" for request in requests))
        self.assertEqual(
            [record.identity for record in discovery.result.records],
            [
                "wordpress:gallery:ozzano-2021",
                "wordpress:gallery:foto-recenti",
            ],
        )
        first_album = discovery.result.records[0]
        self.assertEqual(first_album.data["order"], 1)
        self.assertEqual(first_album.data["cover_url"], "https://wordpress.example.test/covers/ozzano.jpg")
        self.assertEqual(
            [image["source_url"].rsplit("/", 1)[-1] for image in first_album.data["images"]],
            ["IMG_3161.jpg", "IMG_3175.jpg", "IMG_3174.jpg"],
        )
        second_album = discovery.result.records[1]
        self.assertEqual(second_album.data["images"][0]["caption"], "Recent caption")
        self.assertEqual(
            [issue.code for issue in discovery.result.issues],
            ["gallery_rest_type_not_exposed"],
        )
        self.assertEqual(discovery.result.issues[0].severity, IssueSeverity.WARNING)

    def test_album_fetch_error_is_explicit_issue_and_album_record_is_kept(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/types"):
                return httpx.Response(200, request=request, json={})
            if request.url.path == "/gallery/":
                return httpx.Response(
                    200,
                    request=request,
                    text='<a href="/dt-gallery/broken/">Broken album</a>',
                )
            if request.url.path == "/dt-gallery/broken/":
                return httpx.Response(503, request=request, text="upstream detail")
            return httpx.Response(404, request=request)

        client, _, _ = self.make_client(handler)
        discovery = client.discover()

        self.assertEqual(len(discovery.result.records), 1)
        self.assertEqual(discovery.result.records[0].data["images"], ())
        issue_codes = [issue.code for issue in discovery.result.issues]
        self.assertIn("gallery_album_fetch_failed", issue_codes)

    def test_archive_without_gallery_links_records_error_issue(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/gallery/":
                return httpx.Response(200, request=request, text="<main>No albums</main>")
            return httpx.Response(404, request=request)

        client, _, _ = self.make_client(handler)
        discovery = client.discover_public_html()

        self.assertEqual(discovery.result.records, ())
        self.assertEqual(discovery.result.issues[0].code, "gallery_archive_has_no_albums")
        self.assertEqual(discovery.result.issues[0].severity, IssueSeverity.ERROR)

    def test_gallery_manifest_is_source_scoped_and_serializable(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/gallery/":
                return httpx.Response(
                    200,
                    request=request,
                    text='<a href="/dt-gallery/album/">Album</a>',
                )
            if request.url.path == "/dt-gallery/album/":
                return httpx.Response(
                    200,
                    request=request,
                    text='<img src="/wp-content/uploads/a.jpg" alt="A">',
                )
            return httpx.Response(404, request=request)

        client, _, _ = self.make_client(handler)
        discovery = client.discover_public_html()
        manifest = discovery.to_manifest(
            base_url="https://wordpress.example.test",
            environment="synthetic",
            observed_at=datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(manifest.scope, InventoryScope.SOURCE)
        self.assertEqual(manifest.records[0].identity, "wordpress:gallery:album")
        self.assertEqual(manifest.issues, ())
        self.assertEqual(manifest.metadata["gallery_discovery_method"], "public_html")
        self.assertTrue(manifest.manifest_sha256)

    def test_transport_rejects_write_method_before_network_use(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, request=request)

        _, readonly, requests = self.make_client(handler)
        with self.assertRaises(ReadOnlyMethodError):
            readonly.request("POST", "https://wordpress.example.test/gallery/")
        self.assertEqual(requests, [])


if __name__ == "__main__":
    unittest.main()
