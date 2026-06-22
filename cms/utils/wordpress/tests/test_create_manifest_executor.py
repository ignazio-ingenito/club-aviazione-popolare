from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

import httpx

from create_manifest_executor import (
    CreateManifestExecutorError,
    build_request_plan,
    load_and_validate_manifest,
    prepare_reports,
    run_executor,
)
from directus_create_only import DirectusCreateOnlyClient, DirectusCreateOnlyConfig
from inventory.canonical import canonical_sha256, sha256_bytes


class CreateManifestExecutorTests(unittest.TestCase):
    def test_real_approved_manifest_builds_draft_only_allowlisted_plan(self) -> None:
        with self.artifact_paths() as (manifest_path, approval_path, manifest_sha, approval_sha):
            manifest = load_and_validate_manifest(
                manifest_path,
                approval_path=approval_path,
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
            )
        plan = build_request_plan(manifest)

        self.assertEqual(len(plan), 35)
        self.assertEqual({item.method for item in plan}, {"POST"})
        self.assertEqual({item.endpoint for item in plan}, {"/items/feeds"})
        self.assertEqual(sum(1 for item in plan if item.operation == "create_feed_draft"), 28)
        self.assertEqual(sum(1 for item in plan if item.operation == "create_gallery_draft"), 7)
        self.assertEqual({item.payload["status"] for item in plan}, {"draft"})

    def test_dry_run_does_not_emit_post(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(201, request=request, json={"data": {"id": 1}})

        raw = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(raw.close)
        client = DirectusCreateOnlyClient(
            config=DirectusCreateOnlyConfig(
                base_url="https://directus.example.test",
                allowed_item_collections=("feeds",),
                auth_token="token",
            ),
            http=raw,
        )
        with self.artifact_paths() as (manifest_path, approval_path, manifest_sha, approval_sha), TemporaryDirectory() as tmp:
            result = run_executor(
                manifest_path=manifest_path,
                approval_path=approval_path,
                output_dir=Path(tmp),
                execute=False,
                client=client,
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
            )

        self.assertEqual(result["executed_operations"], 0)
        self.assertEqual(requests, [])

    def test_execute_without_flag_does_not_write(self) -> None:
        with self.artifact_paths() as (manifest_path, approval_path, manifest_sha, approval_sha):
            reports = prepare_reports(
                manifest_path=manifest_path,
                approval_path=approval_path,
                execute=False,
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
            )

        self.assertTrue(reports.dry_run_report["dry_run"])
        self.assertEqual(reports.dry_run_report["post_requests_sent"], 0)

    def test_forbidden_transport_methods_are_blocked_before_transport(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(500, request=request)

        raw = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(raw.close)
        client = DirectusCreateOnlyClient(
            config=DirectusCreateOnlyConfig(
                base_url="https://directus.example.test",
                allowed_item_collections=("feeds",),
                auth_token="token",
            ),
            http=raw,
        )

        with self.assertRaises(Exception):
            client.request("PATCH", "/items/feeds/1")
        self.assertEqual(requests, [])

    def test_execute_flag_is_blocked_until_permission_and_target_gates_exist(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(201, request=request, json={"data": {"id": 1}})

        raw = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(raw.close)
        client = DirectusCreateOnlyClient(
            config=DirectusCreateOnlyConfig(
                base_url="https://directus.example.test",
                allowed_item_collections=("feeds",),
                auth_token="token",
            ),
            http=raw,
        )
        with self.artifact_paths() as (manifest_path, approval_path, manifest_sha, approval_sha), TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(CreateManifestExecutorError, "Execution is intentionally blocked"):
                run_executor(
                    manifest_path=manifest_path,
                    approval_path=approval_path,
                    output_dir=Path(tmp),
                    execute=True,
                    client=client,
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=approval_sha,
                )
        self.assertEqual(requests, [])

    def test_non_draft_operation_fails(self) -> None:
        manifest = self.synthetic_manifest()
        manifest["operations"][0]["target_status"] = "published"
        with self.assertRaisesRegex(CreateManifestExecutorError, "draft"):
            self.validated_synthetic_manifest(manifest)

    def test_unknown_operation_fails(self) -> None:
        manifest = self.synthetic_manifest()
        manifest["operations"][0]["operation"] = "update_feed"
        with self.assertRaisesRegex(CreateManifestExecutorError, "Unsupported operation"):
            self.validated_synthetic_manifest(manifest)

    def test_count_mismatch_fails(self) -> None:
        manifest = self.synthetic_manifest()
        manifest["counts"]["total_operations"] = 34
        with self.assertRaisesRegex(CreateManifestExecutorError, "count mismatch"):
            self.validated_synthetic_manifest(manifest)

    def test_manifest_sha_mismatch_fails(self) -> None:
        with self.artifact_paths() as (manifest_path, approval_path, _manifest_sha, approval_sha):
            with self.assertRaisesRegex(CreateManifestExecutorError, "Manifest sha256 mismatch"):
                load_and_validate_manifest(
                    manifest_path,
                    approval_path=approval_path,
                    expected_manifest_sha256="0" * 64,
                    expected_approval_sha256=approval_sha,
                )

    def test_missing_source_record_fails(self) -> None:
        manifest = self.synthetic_manifest()
        manifest["operations"][0].pop("source_record")
        with self.assertRaisesRegex(CreateManifestExecutorError, "source_record"):
            self.validated_synthetic_manifest(manifest)

    def validated_synthetic_manifest(self, manifest):
        from create_manifest_executor import _validate_counts, _validate_operations

        _validate_counts(manifest)
        _validate_operations(manifest)
        return manifest

    def synthetic_manifest(self):
        operations = []
        for index in range(35):
            is_gallery = index >= 28
            source_record = {
                "kind": "record",
                "scope": "source",
                "schema_version": 1,
                "entity_type": "wordpress_gallery_album" if is_gallery else "wordpress_post",
                "identity": f"wordpress:{'gallery' if is_gallery else 'post'}:{index}",
                "source_url": f"https://source.example.test/{index}",
                "data": {
                    "slug": f"source-{index}",
                    "title": {"rendered": f"Source {index}"},
                    "content": {"rendered": "<p>Body</p>"},
                    "excerpt": {"rendered": "<p>Excerpt</p>"},
                    "date": "2026-06-22T10:00:00",
                },
            }
            source_record["sha256"] = canonical_sha256(
                {
                    "schema_version": source_record["schema_version"],
                    "scope": source_record["scope"],
                    "entity_type": source_record["entity_type"],
                    "identity": source_record["identity"],
                    "source_url": source_record["source_url"],
                    "data": source_record["data"],
                }
            )
            operations.append(
                {
                    "operation": "create_gallery_draft" if is_gallery else "create_feed_draft",
                    "operation_id": f"op-{index}",
                    "source_identity": source_record["identity"],
                    "source_sha256": source_record["sha256"],
                    "source_record": source_record,
                    "original_uri": source_record["source_url"],
                    "target_status": "draft",
                    "write_policy": "create_only",
                    "forbidden_methods": ["PATCH", "PUT", "DELETE"],
                }
            )
        return {
            "kind": "create_manifest_draft_only",
            "schema_version": 1,
            "approval": {"sha256": "approval-sha-placeholder"},
            "counts": {
                "create_feed_draft": 28,
                "create_gallery_draft": 7,
                "total_operations": 35,
            },
            "operations": operations,
        }

    def synthetic_approval(self):
        return {
            "kind": "cap_wordpress_migration_approval",
            "run_dir": "/tmp/synthetic",
            "approved": {
                "article_create_candidates": [
                    f"https://source.example.test/article-{index}" for index in range(28)
                ],
                "gallery_create_candidates": [
                    f"https://source.example.test/gallery-{index}" for index in range(7)
                ],
            },
            "counts": {
                "approved_article_create_candidates": 28,
                "approved_gallery_create_candidates": 7,
                "excluded_non_article_candidates": 13,
                "excluded_wordpress_type_manual_review": 6,
            },
        }

    def artifact_paths(self):
        case = self

        class ArtifactContext:
            def __enter__(self):
                self.temp = TemporaryDirectory()
                directory = Path(self.temp.name)
                approval = case.synthetic_approval()
                approval_path = directory / "migration-approval.json"
                approval_path.write_text(json.dumps(approval, sort_keys=True), encoding="utf-8")
                approval_sha = sha256_bytes(approval_path.read_bytes())
                manifest = case.synthetic_manifest()
                manifest["approval"]["sha256"] = approval_sha
                manifest_path = directory / "create-manifest-draft-only.json"
                manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
                manifest_sha = sha256_bytes(manifest_path.read_bytes())
                return manifest_path, approval_path, manifest_sha, approval_sha

            def __exit__(self, exc_type, exc, traceback):
                self.temp.cleanup()

        return ArtifactContext()


if __name__ == "__main__":
    unittest.main()
