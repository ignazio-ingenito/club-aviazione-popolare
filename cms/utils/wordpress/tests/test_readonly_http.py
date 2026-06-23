from __future__ import annotations

import unittest

import httpx

from inventory.errors import ReadOnlyMethodError, ResponseContractError
from inventory.readonly_http import ReadOnlyHttpClient


class ReadOnlyHttpClientTests(unittest.TestCase):
    def test_non_read_method_is_rejected_before_transport(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json={"ok": True})

        with ReadOnlyHttpClient(
            base_url="https://example.test/wp-json/wp/v2/",
            transport=httpx.MockTransport(handler),
        ) as client:
            with self.assertRaises(ReadOnlyMethodError):
                client.request("POST", "posts")

        self.assertEqual(requests, [])

    def test_get_and_head_are_the_only_transmitted_methods(self) -> None:
        methods: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            methods.append(request.method)
            return httpx.Response(200, json={"ok": True})

        with ReadOnlyHttpClient(
            base_url="https://example.test/wp-json/wp/v2/",
            transport=httpx.MockTransport(handler),
        ) as client:
            client.get("posts")
            client.head("posts")

        self.assertEqual(methods, ["GET", "HEAD"])

    def test_absolute_request_path_is_rejected(self) -> None:
        with ReadOnlyHttpClient(
            base_url="https://example.test/wp-json/wp/v2/",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"ok": True})
            ),
        ) as client:
            for path in (
                "https://other.test/posts",
                "/wp-json/wp/v2/posts",
                "//other.test/posts",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError):
                        client.get(path)

    def test_invalid_json_is_reported_as_contract_error(self) -> None:
        with ReadOnlyHttpClient(
            base_url="https://example.test/wp-json/wp/v2/",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, text="not-json")
            ),
        ) as client:
            with self.assertRaises(ResponseContractError):
                client.get_json("posts")


if __name__ == "__main__":
    unittest.main()
