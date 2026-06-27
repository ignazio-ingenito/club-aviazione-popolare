from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import httpx

from gallery_media_token_recovery import (
    APPLY_GATE,
    GalleryMediaTokenRecoveryError,
    discover_gallery_media_identity,
    main,
    probe_gallery_media_token,
    regenerate_gallery_media_token,
)


class GalleryMediaTokenRecoveryTests(unittest.TestCase):
    def test_discovery_is_get_only_and_sanitized(self) -> None:
        requests, client = self.client()

        report = discover_gallery_media_identity(
            directus_url="https://cap-cms.skunklabs.uk",
            admin_token="admin-secret",
            http=client,
        )

        self.assertEqual(report["status"], "ready_for_token_recovery")
        self.assertEqual({request.method for request in requests}, {"GET"})
        self.assertNotIn("admin-secret", json.dumps(report))

    def test_discovery_blocks_unexpected_permission(self) -> None:
        permissions = self.payloads()["/permissions"]["data"]
        permissions.append({"collection": "feeds", "action": "update"})
        _, client = self.client(overrides={"/permissions": {"data": permissions}})

        report = discover_gallery_media_identity(
            directus_url="https://cap-cms.skunklabs.uk",
            admin_token="admin-secret",
            http=client,
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["permissions"]["unexpected"], ["feeds.update"])

    def test_regenerate_requires_apply_gate_before_patch(self) -> None:
        requests, client = self.client()

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(GalleryMediaTokenRecoveryError):
                regenerate_gallery_media_token(
                    directus_url="https://cap-cms.skunklabs.uk",
                    admin_token="admin-secret",
                    http=client,
                    token="new-secret-token",
                )

        self.assertEqual(requests, [])

    def test_regenerate_patches_only_existing_user_token_and_omits_token_from_report(self) -> None:
        requests, client = self.client()

        with patch.dict(os.environ, {APPLY_GATE: "true"}, clear=True):
            report = regenerate_gallery_media_token(
                directus_url="https://cap-cms.skunklabs.uk",
                admin_token="admin-secret",
                http=client,
                token="new-secret-token",
            )

        self.assertEqual(report["status"], "token_regenerated")
        self.assertEqual(report["plaintext_token"], "new-secret-token")
        sanitized = dict(report)
        sanitized.pop("plaintext_token")
        self.assertNotIn("new-secret-token", json.dumps(sanitized))
        patch_requests = [request for request in requests if request.method == "PATCH"]
        self.assertEqual(len(patch_requests), 1)
        self.assertEqual(patch_requests[0].url.path, "/users/user-gallery")
        self.assertEqual(json.loads(patch_requests[0].content), {"token": "new-secret-token"})
        self.assertFalse(any(request.method in {"POST", "PUT", "DELETE"} for request in requests))

    def test_token_probe_accepts_expected_reads_and_forbidden_system_reads(self) -> None:
        requests, client = self.probe_client(
            {
                "/server/info": 200,
                "/items/feeds": 200,
                "/folders": 200,
                "/files": 200,
                "/permissions": 403,
                "/users": 403,
            }
        )

        report = probe_gallery_media_token(
            directus_url="https://cap-cms.skunklabs.uk",
            gallery_media_token="gallery-token",
            http=client,
        )

        self.assertEqual(report["status"], "approved")
        self.assertEqual({request.method for request in requests}, {"GET"})
        self.assertNotIn("gallery-token", json.dumps(report))

    def test_token_probe_rejects_broad_system_access(self) -> None:
        _, client = self.probe_client(
            {
                "/server/info": 200,
                "/items/feeds": 200,
                "/folders": 200,
                "/files": 200,
                "/permissions": 200,
                "/users": 403,
            }
        )

        report = probe_gallery_media_token(
            directus_url="https://cap-cms.skunklabs.uk",
            gallery_media_token="gallery-token",
            http=client,
        )

        self.assertEqual(report["status"], "rejected")

    def test_cli_writes_sanitized_reports_outside_repo(self) -> None:
        _, client = self.client()
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"DIRECTUS_ADMIN_TOKEN": "admin-secret"}, clear=True):
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--output-dir", str(Path(tmp) / "reports")], http=client)

            written = (Path(tmp) / "reports" / "gallery-media-token-recovery.discovery.json").read_text(
                encoding="utf-8"
            )

        self.assertEqual(exit_code, 0)
        self.assertNotIn("admin-secret", written)
        self.assertEqual(stdout.getvalue(), "")

    def test_cli_refuses_output_inside_repo_before_network(self) -> None:
        def failing_handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError(f"unexpected network request: {request.method} {request.url}")

        client = httpx.Client(transport=httpx.MockTransport(failing_handler))
        self.addCleanup(client.close)
        repo_root = Path(__file__).resolve().parents[4]
        with patch.dict(os.environ, {"DIRECTUS_ADMIN_TOKEN": "admin-secret"}, clear=True):
            exit_code = main(["--output-dir", str(repo_root / "token-recovery")], http=client)

        self.assertEqual(exit_code, 1)

    def client(
        self,
        *,
        overrides: dict[str, dict[str, object]] | None = None,
    ) -> tuple[list[httpx.Request], httpx.Client]:
        payloads = self.payloads()
        if overrides:
            payloads.update(overrides)
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.method == "PATCH" and request.url.path == "/users/user-gallery":
                return httpx.Response(200, request=request, json={"data": {"id": "user-gallery"}})
            return httpx.Response(200, request=request, json=payloads[request.url.path])

        client = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        return requests, client

    def probe_client(self, status_by_path: dict[str, int]) -> tuple[list[httpx.Request], httpx.Client]:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            status = status_by_path[request.url.path]
            return httpx.Response(status, request=request, json={"data": {}})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        return requests, client

    def payloads(self) -> dict[str, dict[str, object]]:
        return {
            "/server/info": {"data": {"directus": {"version": "11.13.2"}}},
            "/users": {
                "data": [
                    {
                        "id": "user-gallery",
                        "email": "cap-gallery-media-migration@skunklabs.uk",
                        "status": "active",
                        "role": "role-gallery",
                    }
                ]
            },
            "/policies": {
                "data": [
                    {
                        "id": "policy-gallery",
                        "name": "directus-createonly-gallery-media-migration",
                        "roles": [{"role": "role-gallery"}],
                    }
                ]
            },
            "/permissions": {
                "data": [
                    {"collection": "feeds", "action": "read"},
                    {"collection": "directus_folders", "action": "read"},
                    {"collection": "directus_folders", "action": "create"},
                    {"collection": "directus_files", "action": "read"},
                    {"collection": "directus_files", "action": "create"},
                ]
            },
        }


if __name__ == "__main__":
    unittest.main()
