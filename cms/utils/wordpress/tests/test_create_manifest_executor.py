from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

import httpx

from create_manifest_executor import (
    APPROVED_ARTIFACT_PROFILES,
    CreateManifestExecutorError,
    NARROWED_ARTIFACT_PROFILE,
    build_request_plan,
    load_and_validate_manifest,
    prepare_reports,
    run_executor,
)
from directus_create_only import DirectusCreateOnlyClient, DirectusCreateOnlyConfig
from inventory.canonical import canonical_sha256, sha256_bytes


class CreateManifestExecutorTests(unittest.TestCase):
    def test_real_approved_manifest_builds_draft_only_allowlisted_plan(self) -> None:
        with self.artifact_paths() as (manifest_path, approval_path, manifest_sha, approval_sha, _counts):
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

    def test_narrowed_manifest_builds_draft_only_allowlisted_plan(self) -> None:
        with self.artifact_paths(feed_count=21, gallery_count=7) as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            counts,
        ):
            manifest = load_and_validate_manifest(
                manifest_path,
                approval_path=approval_path,
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
                expected_counts=counts,
            )
        plan = build_request_plan(manifest)

        self.assertEqual(len(plan), 28)
        self.assertEqual({item.method for item in plan}, {"POST"})
        self.assertEqual({item.endpoint for item in plan}, {"/items/feeds"})
        self.assertEqual(sum(1 for item in plan if item.operation == "create_feed_draft"), 21)
        self.assertEqual(sum(1 for item in plan if item.operation == "create_gallery_draft"), 7)
        self.assertEqual({item.payload["status"] for item in plan}, {"draft"})
        self.assertEqual(set(APPROVED_ARTIFACT_PROFILES[NARROWED_ARTIFACT_PROFILE].counts), set(counts))

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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
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

    def test_narrowed_dry_run_does_not_emit_post(self) -> None:
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
        with self.artifact_paths(feed_count=21, gallery_count=7) as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            counts,
        ), TemporaryDirectory() as tmp:
            result = run_executor(
                manifest_path=manifest_path,
                approval_path=approval_path,
                output_dir=Path(tmp),
                execute=False,
                client=client,
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
                expected_counts=counts,
            )
            request_plan = json.loads(Path(result["reports"]["request_plan"]).read_text(encoding="utf-8"))
            dry_run = json.loads(Path(result["reports"]["dry_run_report"]).read_text(encoding="utf-8"))

        self.assertEqual(result["executed_operations"], 0)
        self.assertEqual(requests, [])
        self.assertEqual(request_plan["operation_count"], 28)
        self.assertEqual(request_plan["planned_methods"], ["POST"])
        self.assertEqual(request_plan["planned_endpoints"], ["/items/feeds"])
        self.assertEqual(dry_run["dry_run"], True)
        self.assertEqual(dry_run["non_read_requests_sent"], 0)
        self.assertEqual(dry_run["post_requests_sent"], 0)
        self.assertEqual(
            {operation["method"] for operation in request_plan["operations"]},
            {"POST"},
        )
        self.assertEqual(
            {operation["endpoint"] for operation in request_plan["operations"]},
            {"/items/feeds"},
        )

    def test_narrowed_profile_supplies_expected_counts(self) -> None:
        with self.artifact_paths(feed_count=21, gallery_count=7) as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ):
            manifest = load_and_validate_manifest(
                manifest_path,
                approval_path=approval_path,
                artifact_profile=NARROWED_ARTIFACT_PROFILE,
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
            )

        self.assertEqual(manifest["counts"]["total_operations"], 28)

    def test_execute_without_flag_does_not_write(self) -> None:
        with self.artifact_paths() as (manifest_path, approval_path, manifest_sha, approval_sha, _counts):
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

    def test_execute_without_permission_gate_fails_before_transport(self) -> None:
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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(CreateManifestExecutorError, "--permission-evidence"):
                run_executor(
                    manifest_path=manifest_path,
                    approval_path=approval_path,
                    output_dir=Path(tmp),
                    execute=True,
                    client=client,
                    auth_token="token",
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=approval_sha,
                )
        self.assertEqual(requests, [])

    def test_execute_without_target_absence_gate_fails_before_transport(self) -> None:
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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
            permission_path = Path(tmp) / "permission-evidence-create-only.json"
            permission_path.write_text(
                json.dumps(self.permission_report(target_url="https://directus.example.test")),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CreateManifestExecutorError, "--fresh-target-absence"):
                run_executor(
                    manifest_path=manifest_path,
                    approval_path=approval_path,
                    output_dir=Path(tmp) / "reports",
                    execute=True,
                    client=client,
                    auth_token="token",
                    permission_evidence_path=permission_path,
                    directus_url="https://directus.example.test",
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=approval_sha,
                )
        self.assertEqual(requests, [])

    def test_execute_with_missing_token_fails_before_transport(self) -> None:
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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
            permission_path, absence_path = self.write_gate_reports(
                Path(tmp),
                manifest_path=manifest_path,
                manifest_sha=manifest_sha,
                approval_sha=approval_sha,
                target_url="https://directus.example.test",
            )
            with self.assertRaisesRegex(CreateManifestExecutorError, "DIRECTUS_TOKEN"):
                run_executor(
                    manifest_path=manifest_path,
                    approval_path=approval_path,
                    output_dir=Path(tmp) / "reports",
                    execute=True,
                    client=client,
                    permission_evidence_path=permission_path,
                    fresh_target_absence_path=absence_path,
                    directus_url="https://directus.example.test",
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=approval_sha,
                )
        self.assertEqual(requests, [])

    def test_execute_with_rejected_permission_gate_fails_before_transport(self) -> None:
        self.assert_rejected_gate_fails_before_transport(reject_permission=True)

    def test_execute_with_rejected_target_gate_fails_before_transport(self) -> None:
        self.assert_rejected_gate_fails_before_transport(reject_permission=False)

    def test_execute_with_approved_gates_posts_draft_items_serially(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            payload = json.loads(request.content.decode("utf-8"))
            return httpx.Response(
                201,
                request=request,
                json={"data": {"id": f"created-{len(requests)}", "status": payload["status"]}},
            )

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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
            permission_path, absence_path = self.write_gate_reports(
                Path(tmp),
                manifest_path=manifest_path,
                manifest_sha=manifest_sha,
                approval_sha=approval_sha,
                target_url="https://directus.example.test",
            )
            result = run_executor(
                manifest_path=manifest_path,
                approval_path=approval_path,
                output_dir=Path(tmp) / "reports",
                execute=True,
                client=client,
                auth_token="token",
                permission_evidence_path=permission_path,
                fresh_target_absence_path=absence_path,
                directus_url="https://directus.example.test",
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
            )
            execution_report = json.loads(Path(result["reports"]["execution_report"]).read_text(encoding="utf-8"))
            execution_events = (Path(tmp) / "reports" / "execution_events.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(result["executed_operations"], 35)
        self.assertEqual(len(requests), 35)
        self.assertEqual(len(execution_events), 35)
        self.assertEqual({request.method for request in requests}, {"POST"})
        self.assertEqual({request.url.path for request in requests}, {"/items/feeds"})
        self.assertEqual(execution_report["executed_operations"], 35)
        self.assertEqual({item["status"] for item in execution_report["created"]}, {"draft"})

    def test_execute_accepts_explicit_fresh_target_absence_hash(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(201, request=request, json={"data": {"id": len(requests), "status": "draft"}})

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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
            permission_path, absence_path = self.write_gate_reports(
                Path(tmp),
                manifest_path=manifest_path,
                manifest_sha=manifest_sha,
                approval_sha=approval_sha,
                target_url="https://directus.example.test",
            )
            result = run_executor(
                manifest_path=manifest_path,
                approval_path=approval_path,
                output_dir=Path(tmp) / "reports",
                execute=True,
                client=client,
                auth_token="token",
                permission_evidence_path=permission_path,
                fresh_target_absence_path=absence_path,
                fresh_target_absence_sha256=sha256_bytes(absence_path.read_bytes()),
                directus_url="https://directus.example.test",
                expected_manifest_sha256=manifest_sha,
                expected_approval_sha256=approval_sha,
            )
        self.assertEqual(result["executed_operations"], 35)
        self.assertEqual(len(requests), 35)

    def test_execute_stops_on_first_failed_post(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if len(requests) == 3:
                return httpx.Response(500, request=request, json={"errors": [{"message": "boom"}]})
            return httpx.Response(201, request=request, json={"data": {"id": len(requests), "status": "draft"}})

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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
            permission_path, absence_path = self.write_gate_reports(
                Path(tmp),
                manifest_path=manifest_path,
                manifest_sha=manifest_sha,
                approval_sha=approval_sha,
                target_url="https://directus.example.test",
            )
            with self.assertRaises(httpx.HTTPStatusError):
                run_executor(
                    manifest_path=manifest_path,
                    approval_path=approval_path,
                    output_dir=Path(tmp) / "reports",
                    execute=True,
                    client=client,
                    auth_token="token",
                    permission_evidence_path=permission_path,
                    fresh_target_absence_path=absence_path,
                    directus_url="https://directus.example.test",
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=approval_sha,
                )
            execution_events = (Path(tmp) / "reports" / "execution_events.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(requests), 3)
        self.assertEqual(len(execution_events), 2)

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

    def test_narrowed_wrong_count_fails(self) -> None:
        with self.artifact_paths(feed_count=21, gallery_count=7) as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            counts,
        ):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["counts"]["create_feed_draft"] = 22
            manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
            manifest_sha = sha256_bytes(manifest_path.read_bytes())
            with self.assertRaisesRegex(CreateManifestExecutorError, "count mismatch"):
                load_and_validate_manifest(
                    manifest_path,
                    approval_path=approval_path,
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=approval_sha,
                    expected_counts=counts,
                )

    def test_mismatched_narrowed_approval_manifest_pair_fails(self) -> None:
        with self.artifact_paths(feed_count=21, gallery_count=7) as (
            manifest_path,
            _approval_path,
            manifest_sha,
            _approval_sha,
            counts,
        ), self.artifact_paths() as (
            _original_manifest_path,
            original_approval_path,
            _original_manifest_sha,
            original_approval_sha,
            _original_counts,
        ):
            with self.assertRaisesRegex(CreateManifestExecutorError, "does not reference"):
                load_and_validate_manifest(
                    manifest_path,
                    approval_path=original_approval_path,
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=original_approval_sha,
                    expected_counts=counts,
                )

    def test_narrowed_profile_records_gate2_hash(self) -> None:
        profile = APPROVED_ARTIFACT_PROFILES[NARROWED_ARTIFACT_PROFILE]
        self.assertEqual(profile.counts["create_feed_draft"], 21)
        self.assertEqual(profile.counts["create_gallery_draft"], 7)
        self.assertEqual(profile.counts["total_operations"], 28)
        self.assertEqual(
            profile.fresh_target_absence_sha256,
            "bbf399f35c138396dc3240c5198c05ef8d45f7d7f95296f087bc377ab39a8a55",
        )

    def test_manifest_sha_mismatch_fails(self) -> None:
        with self.artifact_paths() as (manifest_path, approval_path, _manifest_sha, approval_sha, _counts):
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

    def synthetic_manifest(self, *, feed_count: int = 28, gallery_count: int = 7):
        operations = []
        for index in range(feed_count + gallery_count):
            is_gallery = index >= feed_count
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
                "create_feed_draft": feed_count,
                "create_gallery_draft": gallery_count,
                "total_operations": feed_count + gallery_count,
            },
            "operations": operations,
        }

    def synthetic_approval(self, *, feed_count: int = 28, gallery_count: int = 7):
        return {
            "kind": "cap_wordpress_migration_approval",
            "run_dir": "/tmp/synthetic",
            "approved": {
                "article_create_candidates": [
                    f"https://source.example.test/article-{index}" for index in range(feed_count)
                ],
                "gallery_create_candidates": [
                    f"https://source.example.test/gallery-{index}" for index in range(gallery_count)
                ],
            },
            "counts": {
                "approved_article_create_candidates": feed_count,
                "approved_gallery_create_candidates": gallery_count,
                "excluded_non_article_candidates": 13,
                "excluded_wordpress_type_manual_review": 6,
            },
        }

    def assert_rejected_gate_fails_before_transport(self, *, reject_permission: bool) -> None:
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
        with self.artifact_paths() as (
            manifest_path,
            approval_path,
            manifest_sha,
            approval_sha,
            _counts,
        ), TemporaryDirectory() as tmp:
            permission_path, absence_path = self.write_gate_reports(
                Path(tmp),
                manifest_path=manifest_path,
                manifest_sha=manifest_sha,
                approval_sha=approval_sha,
                target_url="https://directus.example.test",
                permission_status="rejected" if reject_permission else "approved",
                absence_status="approved" if reject_permission else "rejected",
            )
            with self.assertRaises(CreateManifestExecutorError):
                run_executor(
                    manifest_path=manifest_path,
                    approval_path=approval_path,
                    output_dir=Path(tmp) / "reports",
                    execute=True,
                    client=client,
                    auth_token="token",
                    permission_evidence_path=permission_path,
                    fresh_target_absence_path=absence_path,
                    directus_url="https://directus.example.test",
                    expected_manifest_sha256=manifest_sha,
                    expected_approval_sha256=approval_sha,
                )
        self.assertEqual(requests, [])

    def write_gate_reports(
        self,
        directory: Path,
        *,
        manifest_path: Path,
        manifest_sha: str,
        approval_sha: str,
        target_url: str,
        permission_status: str = "approved",
        absence_status: str = "approved",
    ) -> tuple[Path, Path]:
        permission_path = directory / "permission-evidence-create-only.json"
        absence_path = directory / "fresh-target-absence-before-create.json"
        permission_path.write_text(
            json.dumps(self.permission_report(status=permission_status, target_url=target_url), sort_keys=True),
            encoding="utf-8",
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        absence_path.write_text(
            json.dumps(
                self.fresh_target_absence_report(
                    manifest,
                    status=absence_status,
                    manifest_sha=manifest_sha,
                    approval_sha=approval_sha,
                    target_url=target_url,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return permission_path, absence_path

    def permission_report(self, *, status: str = "approved", target_url: str = "https://cap-cms.skunklabs.uk"):
        return {
            "kind": "permission_evidence_create_only",
            "status": status,
            "target_url": target_url,
            "observed_at": "2026-06-22T12:00:00Z",
            "execution_identity": {
                "id": "directus-user:migration-create-only",
                "role": "migration-create-only",
            },
            "capabilities": {
                "admin": False,
                "system_wildcard": False,
                "broad_token": False,
            },
            "probes": {
                "create": {"method": "POST", "resource": "/items/feeds", "result": "allowed", "success": True},
                "patch": {"method": "PATCH", "resource": "/items/feeds", "result": "denied", "success": False},
                "put": {"method": "PUT", "resource": "/items/feeds", "result": "denied", "success": False},
                "delete": {"method": "DELETE", "resource": "/items/feeds", "result": "denied", "success": False},
                "schema": {"method": "GET", "resource": "/schema", "result": "denied", "success": False},
                "settings": {"method": "GET", "resource": "/settings", "result": "denied", "success": False},
                "users": {"method": "GET", "resource": "/users", "result": "denied", "success": False},
                "roles": {"method": "GET", "resource": "/roles", "result": "denied", "success": False},
                "permissions": {"method": "GET", "resource": "/permissions", "result": "denied", "success": False},
            },
        }

    def fresh_target_absence_report(
        self,
        manifest,
        *,
        status: str = "approved",
        manifest_sha: str,
        approval_sha: str,
        target_url: str,
    ):
        original_uris = [operation["original_uri"] for operation in manifest["operations"]]
        return {
            "kind": "fresh_target_absence_before_create",
            "status": status,
            "target_url": target_url,
            "observed_at": "2026-06-22T12:05:00Z",
            "approval_sha256": approval_sha,
            "manifest_sha256": manifest_sha,
            "target_baseline_sha256": "7" * 64,
            "checked_operation_count": len(original_uris),
            "checked_original_uris": original_uris,
            "absence_evidence": {
                original_uri: {"status": "absent", "checked": True, "matches": []}
                for original_uri in original_uris
            },
            "route_collisions": [],
            "slug_collisions": [],
            "protected_collisions": [],
            "drift_protected_collisions": [],
            "ambiguous_matches": [],
            "skipped_checks": [],
            "stale_baseline": False,
        }

    def artifact_paths(self, *, feed_count: int = 28, gallery_count: int = 7):
        case = self

        class ArtifactContext:
            def __init__(self, *, feed_count: int, gallery_count: int) -> None:
                self.feed_count = feed_count
                self.gallery_count = gallery_count
                self.temp: TemporaryDirectory | None = None

            def __enter__(self):
                self.temp = TemporaryDirectory()
                directory = Path(self.temp.name)
                feed_count = self.feed_count
                gallery_count = self.gallery_count
                approval = case.synthetic_approval(feed_count=feed_count, gallery_count=gallery_count)
                approval_path = directory / "migration-approval.json"
                approval_path.write_text(json.dumps(approval, sort_keys=True), encoding="utf-8")
                approval_sha = sha256_bytes(approval_path.read_bytes())
                manifest = case.synthetic_manifest(feed_count=feed_count, gallery_count=gallery_count)
                manifest["approval"]["sha256"] = approval_sha
                manifest_path = directory / "create-manifest-draft-only.json"
                manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
                manifest_sha = sha256_bytes(manifest_path.read_bytes())
                counts = {
                    "create_feed_draft": feed_count,
                    "create_gallery_draft": gallery_count,
                    "total_operations": feed_count + gallery_count,
                }
                return manifest_path, approval_path, manifest_sha, approval_sha, counts

            def __exit__(self, exc_type, exc, traceback):
                if self.temp is not None:
                    self.temp.cleanup()

        context = ArtifactContext(feed_count=feed_count, gallery_count=gallery_count)
        return context


if __name__ == "__main__":
    unittest.main()
