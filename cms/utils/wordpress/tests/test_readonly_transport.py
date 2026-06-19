from __future__ import annotations

import unittest

import httpx

from inventory.transport import (
    InventoryHttpError,
    ReadOnlyEndpointError,
    ReadOnlyHttpClient,
    ReadOnlyMethodError,
)


def _json_response(request: httpx.Request, payload: object, *, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=payload, request=request)


class ReadOnlyTransportTests(unittest.TestCase):
    def test_forbidden_method_is_rejected_before_transport(self) -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.method)
            return _json_response(request, {})

        client = ReadOnlyHttpClient(
            "https://example.test/api/",
            transport=httpx.MockTransport(handler),
        )
        with self.assertRaises(ReadOnlyMethodError):
            client.request("POST", "posts")
        self.assertEqual(seen, [])
        client.close()

    def test_absolute_endpoint_and_parent_traversal_are_rejected(self) -> None:
        client = ReadOnlyHttpClient(
            "https://example.test/api/",
            transport=httpx.MockTransport(lambda request: _json_response(request, {})),
        )
        with self.assertRaises(ReadOnlyEndpointError):
            client.get("https://outside.test/data")
        with self.assertRaises(ReadOnlyEndpointError):
            client.get("../users")
        client.close()

    def test_cross_origin_redirect_is_rejected(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "example.test":
                return httpx.Response(
                    302,
                    headers={"Location": "https://outside.test/data"},
                    request=request,
                )
            return _json_response(request, {})

        client = ReadOnlyHttpClient(
            "https://example.test/api/",
            transport=httpx.MockTransport(handler),
        )
        with self.assertRaises(InventoryHttpError):
            client.get_json("posts")
        client.close()

    def test_invalid_json_is_sanitized(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"not-json",
                headers={"content-type": "application/json"},
                request=request,
            )

        client = ReadOnlyHttpClient(
            "https://example.test/api/",
            transport=httpx.MockTransport(handler),
        )
        with self.assertRaises(InventoryHttpError) as raised:
            client.get_json("posts")
        self.assertEqual(raised.exception.status_code, 200)
        client.close()

    def test_http_failure_does_not_expose_response_content(self) -> None:
        client = ReadOnlyHttpClient(
            "https://example.test/api/",
            transport=httpx.MockTransport(
                lambda request: _json_response(
                    request,
                    {"marker": "body-content"},
                    status_code=500,
                )
            ),
        )
        with self.assertRaises(InventoryHttpError) as raised:
            client.get_json("posts")
        self.assertEqual(raised.exception.status_code, 500)
        self.assertNotIn("body-content", str(raised.exception))
        client.close()


if __name__ == "__main__":
    unittest.main()
