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

from directus_policy_collector import DirectusPolicyCollectorError, collect_directus_policy_graph_raw
from directus_policy_evidence import evaluate_policy_graph_evidence, main, normalize_directus_policy_graph_payload


class DirectusPolicyCollectorTests(unittest.TestCase):
    def test_collector_performs_only_get_requests(self) -> None:
        requests, client = self.client()

        collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token="secret-token",
            http=client,
        )

        self.assertEqual({request.method for request in requests}, {"GET"})
        self.assertEqual(
            [request.url.path for request in requests],
            ["/server/info", "/roles/role-create-only", "/policies", "/permissions"],
        )

    def test_collector_uses_directus_11_policy_role_filter(self) -> None:
        requests, client = self.client()

        collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token="secret-token",
            http=client,
        )

        policies_request = next(request for request in requests if request.url.path == "/policies")
        self.assertEqual(policies_request.url.params.get("filter[roles][role][_eq]"), "role-create-only")
        self.assertEqual(policies_request.url.params.get("fields"), "id,name,roles.role.*")
        self.assertNotIn("filter[roles][_contains]", policies_request.url.params)

    def test_collector_accepts_directus_access_role_linkage(self) -> None:
        policies = self.default_payloads()["/policies"]["data"]
        policies[0]["roles"] = [
            {
                "id": "access-link",
                "policy": "policy-create-only",
                "role": "role-create-only",
                "sort": None,
                "user": None,
            }
        ]
        _, client = self.client(overrides={"/policies": {"data": policies}})

        raw = collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token="secret-token",
            http=client,
        )

        self.assertEqual(raw["policies"][0]["roles"], ["role-create-only"])

    def test_collector_never_uses_write_methods(self) -> None:
        requests, client = self.client()

        collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token="secret-token",
            http=client,
        )

        self.assertFalse({"POST", "PATCH", "PUT", "DELETE"} & {request.method for request in requests})

    def test_collector_adds_authorization_header_without_serializing_token(self) -> None:
        token = "secret-token-value"
        requests, client = self.client()

        raw = collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token=token,
            http=client,
        )

        self.assertTrue(all(request.headers["Authorization"] == f"Bearer {token}" for request in requests))
        self.assertTrue(all(request.headers["User-Agent"] == "cap-wordpress-migration/1.0" for request in requests))
        self.assertNotIn(token, json.dumps(raw))

    def test_collector_rejects_missing_token(self) -> None:
        _, client = self.client()

        with self.assertRaises(DirectusPolicyCollectorError):
            collect_directus_policy_graph_raw(
                directus_url="https://cap-cms.skunklabs.uk",
                role_id="role-create-only",
                auth_token="",
                http=client,
            )

    def test_collector_rejects_empty_role_id(self) -> None:
        _, client = self.client()

        with self.assertRaises(DirectusPolicyCollectorError):
            collect_directus_policy_graph_raw(
                directus_url="https://cap-cms.skunklabs.uk",
                role_id=" ",
                auth_token="secret-token",
                http=client,
            )

    def test_collector_rejects_malformed_directus_url(self) -> None:
        _, client = self.client()

        with self.assertRaises(DirectusPolicyCollectorError):
            collect_directus_policy_graph_raw(
                directus_url="cap-cms.skunklabs.uk",
                role_id="role-create-only",
                auth_token="secret-token",
                http=client,
            )

    def test_collector_rejects_missing_role_response(self) -> None:
        _, client = self.client(status_by_path={"/roles/role-create-only": 404})

        with self.assertRaises(DirectusPolicyCollectorError):
            collect_directus_policy_graph_raw(
                directus_url="https://cap-cms.skunklabs.uk",
                role_id="role-create-only",
                auth_token="secret-token",
                http=client,
            )

    def test_collector_rejects_missing_policies_response(self) -> None:
        _, client = self.client(overrides={"/policies": {"data": []}})

        with self.assertRaises(DirectusPolicyCollectorError):
            collect_directus_policy_graph_raw(
                directus_url="https://cap-cms.skunklabs.uk",
                role_id="role-create-only",
                auth_token="secret-token",
                http=client,
            )

    def test_collector_rejects_missing_permissions_response(self) -> None:
        _, client = self.client(overrides={"/permissions": {"data": []}})

        with self.assertRaises(DirectusPolicyCollectorError):
            collect_directus_policy_graph_raw(
                directus_url="https://cap-cms.skunklabs.uk",
                role_id="role-create-only",
                auth_token="secret-token",
                http=client,
            )

    def test_collector_output_is_accepted_by_normalizer(self) -> None:
        _, client = self.client()

        raw = collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token="secret-token",
            http=client,
        )
        normalized = normalize_directus_policy_graph_payload(raw)

        self.assertEqual(normalized["identity"]["role"], "role-create-only")
        self.assertEqual(normalized["directus_version"], "11.13.2")

    def test_collector_to_evaluator_approves_safe_mocked_graph(self) -> None:
        _, client = self.client()

        raw = collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token="secret-token",
            http=client,
        )
        evaluation = evaluate_policy_graph_evidence(normalize_directus_policy_graph_payload(raw))

        self.assertEqual(evaluation["status"], "approved")

    def test_collector_to_evaluator_rejects_broad_mocked_graph(self) -> None:
        permissions = self.default_payloads()["/permissions"]["data"]
        permissions.append(
            {
                "id": "perm-feeds-update",
                "policy": "policy-create-only",
                "collection": "feeds",
                "action": "update",
                "permissions": {},
                "validation": {},
                "presets": None,
                "fields": ["title"],
            },
        )
        _, client = self.client(overrides={"/permissions": {"data": permissions}})

        raw = collect_directus_policy_graph_raw(
            directus_url="https://cap-cms.skunklabs.uk",
            role_id="role-create-only",
            auth_token="secret-token",
            http=client,
        )
        evaluation = evaluate_policy_graph_evidence(normalize_directus_policy_graph_payload(raw))

        self.assertEqual(evaluation["status"], "rejected")
        self.assertIn("forbidden_update_permission", evaluation["reasons"])

    def test_cli_without_collect_live_performs_no_network(self) -> None:
        def failing_handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError(f"unexpected network request: {request.method} {request.url}")

        client = httpx.Client(transport=httpx.MockTransport(failing_handler))
        with TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "evidence.json"
            output_path = Path(tmp) / "evaluation.json"
            input_path.write_text(json.dumps(self.normalized_payload()), encoding="utf-8")

            exit_code = main(["--input", str(input_path), "--output", str(output_path)], http=client)

        self.assertEqual(exit_code, 0)

    def test_cli_collect_live_with_mocked_http_writes_outputs_without_token(self) -> None:
        token = "secret-token-value"
        requests, client = self.client()
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"DIRECTUS_TOKEN": token}, clear=True):
            raw_path = Path(tmp) / "raw.json"
            normalized_path = Path(tmp) / "normalized.json"
            evaluation_path = Path(tmp) / "evaluation.json"
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--collect-live",
                        "--directus-url",
                        "https://cap-cms.skunklabs.uk",
                        "--role-id",
                        "role-create-only",
                        "--raw-output",
                        str(raw_path),
                        "--normalized-output",
                        str(normalized_path),
                        "--evaluation-output",
                        str(evaluation_path),
                    ],
                    http=client,
                )

            written = raw_path.read_text(encoding="utf-8") + normalized_path.read_text(encoding="utf-8")
            written += evaluation_path.read_text(encoding="utf-8") + stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertEqual({request.method for request in requests}, {"GET"})
        self.assertNotIn(token, written)

    def test_cli_collect_live_rejects_missing_token(self) -> None:
        _, client = self.client()
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            exit_code = main(
                [
                    "--collect-live",
                    "--directus-url",
                    "https://cap-cms.skunklabs.uk",
                    "--role-id",
                    "role-create-only",
                    "--raw-output",
                    str(Path(tmp) / "raw.json"),
                    "--normalized-output",
                    str(Path(tmp) / "normalized.json"),
                    "--evaluation-output",
                    str(Path(tmp) / "evaluation.json"),
                ],
                http=client,
            )

        self.assertEqual(exit_code, 1)

    def test_cli_collect_live_refuses_overwrite_before_network(self) -> None:
        def failing_handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError(f"unexpected network request: {request.method} {request.url}")

        client = httpx.Client(transport=httpx.MockTransport(failing_handler))
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"DIRECTUS_TOKEN": "secret-token"}, clear=True):
            raw_path = Path(tmp) / "raw.json"
            raw_path.write_text("{}", encoding="utf-8")

            exit_code = main(
                [
                    "--collect-live",
                    "--directus-url",
                    "https://cap-cms.skunklabs.uk",
                    "--role-id",
                    "role-create-only",
                    "--raw-output",
                    str(raw_path),
                    "--normalized-output",
                    str(Path(tmp) / "normalized.json"),
                    "--evaluation-output",
                    str(Path(tmp) / "evaluation.json"),
                ],
                http=client,
            )

        self.assertEqual(exit_code, 1)

    def test_cli_collect_live_refuses_output_inside_repository(self) -> None:
        def failing_handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError(f"unexpected network request: {request.method} {request.url}")

        client = httpx.Client(transport=httpx.MockTransport(failing_handler))
        repo_root = Path(__file__).resolve().parents[4]
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"DIRECTUS_TOKEN": "secret-token"}, clear=True):
            exit_code = main(
                [
                    "--collect-live",
                    "--directus-url",
                    "https://cap-cms.skunklabs.uk",
                    "--role-id",
                    "role-create-only",
                    "--raw-output",
                    str(repo_root / "collector.raw.json"),
                    "--normalized-output",
                    str(Path(tmp) / "normalized.json"),
                    "--evaluation-output",
                    str(Path(tmp) / "evaluation.json"),
                ],
                http=client,
            )

        self.assertEqual(exit_code, 1)
        self.assertFalse((repo_root / "collector.raw.json").exists())

    def client(
        self,
        *,
        overrides: dict[str, dict[str, object]] | None = None,
        status_by_path: dict[str, int] | None = None,
    ) -> tuple[list[httpx.Request], httpx.Client]:
        payloads = self.default_payloads()
        if overrides:
            payloads.update(overrides)
        statuses = status_by_path or {}
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            status = statuses.get(request.url.path, 200)
            if status != 200:
                return httpx.Response(status, request=request, json={"errors": []})
            return httpx.Response(200, request=request, json=payloads[request.url.path])

        return requests, httpx.Client(transport=httpx.MockTransport(handler))

    def default_payloads(self) -> dict[str, dict[str, object]]:
        return {
            "/server/info": {"data": {"directus": {"version": "11.13.2"}}},
            "/roles/role-create-only": {"data": {"id": "role-create-only", "name": "CAP WordPress create-only"}},
            "/policies": {
                "data": [
                    {
                        "id": "policy-create-only",
                        "name": "CAP WordPress create-only content migration",
                        "roles": ["role-create-only"],
                    }
                ]
            },
            "/permissions": {"data": [self.feeds_create_permission()]},
        }

    def normalized_payload(self) -> dict:
        return {
            "kind": "directus_policy_graph_evidence",
            "target_url": "https://cap-cms.skunklabs.uk",
            "observed_at": "2026-06-22T12:00:00Z",
            "identity": {
                "label": "CAP WordPress create-only",
                "role": "role-create-only",
            },
            "policies": [
                {
                    "id": "policy-create-only",
                    "name": "CAP WordPress create-only content migration",
                }
            ],
            "permissions": [self.feeds_create_permission()],
        }

    def feeds_create_permission(self) -> dict:
        return {
            "id": "perm-feeds-create",
            "policy": "policy-create-only",
            "collection": "feeds",
            "action": "create",
            "permissions": {},
            "validation": {
                "status": {
                    "_eq": "draft",
                }
            },
            "presets": {
                "status": "draft",
            },
            "fields": [
                "status",
                "slug",
                "title",
                "content",
                "description",
                "date",
                "original_uri",
                "gallery",
            ],
        }


if __name__ == "__main__":
    unittest.main()
