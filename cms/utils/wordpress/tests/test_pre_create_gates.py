from __future__ import annotations

import unittest

from pre_create_gates import (
    PreCreateGateError,
    validate_fresh_target_absence_report,
    validate_permission_evidence_report,
)


DIRECTUS_URL = "https://cap-cms.skunklabs.uk"
MANIFEST_SHA = "9" * 64
APPROVAL_SHA = "8" * 64


class PreCreateGateTests(unittest.TestCase):
    def test_approved_permission_report_passes(self) -> None:
        validate_permission_evidence_report(
            self.permission_report(),
            expected_target_url=DIRECTUS_URL,
        )

    def test_rejected_permission_report_fails(self) -> None:
        report = self.permission_report(status="rejected")
        with self.assertRaises(PreCreateGateError):
            validate_permission_evidence_report(report, expected_target_url=DIRECTUS_URL)

    def test_missing_permission_report_fails(self) -> None:
        with self.assertRaises(PreCreateGateError):
            validate_permission_evidence_report(None, expected_target_url=DIRECTUS_URL)  # type: ignore[arg-type]

    def test_malformed_permission_report_fails(self) -> None:
        with self.assertRaises(PreCreateGateError):
            validate_permission_evidence_report([], expected_target_url=DIRECTUS_URL)  # type: ignore[arg-type]

    def test_missing_create_probe_fails(self) -> None:
        report = self.permission_report()
        report["probes"].pop("create")
        with self.assertRaises(PreCreateGateError):
            validate_permission_evidence_report(report, expected_target_url=DIRECTUS_URL)

    def test_create_denied_fails(self) -> None:
        report = self.permission_report()
        report["probes"]["create"]["result"] = "denied"
        with self.assertRaises(PreCreateGateError):
            validate_permission_evidence_report(report, expected_target_url=DIRECTUS_URL)

    def test_forbidden_permission_probe_allowed_fails(self) -> None:
        for probe_name in ("patch", "put", "delete", "schema", "settings", "users", "roles", "permissions"):
            with self.subTest(probe=probe_name):
                report = self.permission_report()
                report["probes"][probe_name]["result"] = "allowed"
                report["probes"][probe_name]["success"] = True
                with self.assertRaises(PreCreateGateError):
                    validate_permission_evidence_report(report, expected_target_url=DIRECTUS_URL)

    def test_ambiguous_permission_probe_fails(self) -> None:
        report = self.permission_report()
        report["probes"]["patch"]["result"] = "inconclusive"
        with self.assertRaises(PreCreateGateError):
            validate_permission_evidence_report(report, expected_target_url=DIRECTUS_URL)

    def test_broad_permission_capability_fails(self) -> None:
        report = self.permission_report()
        report["capabilities"]["admin"] = True
        with self.assertRaises(PreCreateGateError):
            validate_permission_evidence_report(report, expected_target_url=DIRECTUS_URL)

    def test_approved_fresh_target_absence_report_passes(self) -> None:
        manifest = self.manifest()
        report = self.fresh_target_absence_report(manifest)
        validate_fresh_target_absence_report(
            report,
            manifest,
            expected_target_url=DIRECTUS_URL,
            expected_manifest_sha256=MANIFEST_SHA,
            expected_approval_sha256=APPROVAL_SHA,
            expected_operation_count=35,
        )

    def test_rejected_fresh_target_absence_report_fails(self) -> None:
        manifest = self.manifest()
        report = self.fresh_target_absence_report(manifest, status="rejected")
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(report, manifest)

    def test_missing_fresh_target_absence_report_fails(self) -> None:
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(None, self.manifest())  # type: ignore[arg-type]

    def test_malformed_fresh_target_absence_report_fails(self) -> None:
        with self.assertRaises(PreCreateGateError):
            self.validate_absence([], self.manifest())  # type: ignore[arg-type]

    def test_fresh_target_absence_hash_mismatch_fails(self) -> None:
        manifest = self.manifest()
        for field_name in ("manifest_sha256", "approval_sha256"):
            with self.subTest(field=field_name):
                report = self.fresh_target_absence_report(manifest)
                report[field_name] = "0" * 64
                with self.assertRaises(PreCreateGateError):
                    self.validate_absence(report, manifest)

    def test_fresh_target_absence_operation_count_mismatch_fails(self) -> None:
        manifest = self.manifest()
        report = self.fresh_target_absence_report(manifest)
        report["checked_operation_count"] = 34
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(report, manifest)

    def test_missing_original_uri_check_fails(self) -> None:
        manifest = self.manifest()
        report = self.fresh_target_absence_report(manifest)
        removed = report["checked_original_uris"].pop()
        report["absence_evidence"].pop(removed)
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(report, manifest)

    def test_extra_original_uri_check_fails(self) -> None:
        manifest = self.manifest()
        report = self.fresh_target_absence_report(manifest)
        report["checked_original_uris"].append("https://source.example.test/extra")
        report["absence_evidence"]["https://source.example.test/extra"] = {"status": "absent", "checked": True}
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(report, manifest)

    def test_duplicate_manifest_original_uri_fails(self) -> None:
        manifest = self.manifest()
        manifest["operations"][1]["original_uri"] = manifest["operations"][0]["original_uri"]
        report = self.fresh_target_absence_report(self.manifest())
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(report, manifest)

    def test_existing_target_match_fails(self) -> None:
        manifest = self.manifest()
        report = self.fresh_target_absence_report(manifest)
        original_uri = report["checked_original_uris"][0]
        report["absence_evidence"][original_uri]["existing_target_match"] = True
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(report, manifest)

    def test_fresh_target_collision_lists_fail(self) -> None:
        manifest = self.manifest()
        for field_name in (
            "route_collisions",
            "slug_collisions",
            "protected_collisions",
            "drift_protected_collisions",
            "ambiguous_matches",
            "skipped_checks",
        ):
            with self.subTest(field=field_name):
                report = self.fresh_target_absence_report(manifest)
                report[field_name] = [{"original_uri": "https://source.example.test/0"}]
                with self.assertRaises(PreCreateGateError):
                    self.validate_absence(report, manifest)

    def test_stale_baseline_indicator_fails(self) -> None:
        manifest = self.manifest()
        report = self.fresh_target_absence_report(manifest)
        report["stale_baseline"] = True
        with self.assertRaises(PreCreateGateError):
            self.validate_absence(report, manifest)

    def validate_absence(self, report, manifest) -> None:
        validate_fresh_target_absence_report(
            report,
            manifest,
            expected_target_url=DIRECTUS_URL,
            expected_manifest_sha256=MANIFEST_SHA,
            expected_approval_sha256=APPROVAL_SHA,
            expected_operation_count=35,
        )

    def permission_report(self, *, status: str = "approved") -> dict:
        return {
            "kind": "permission_evidence_create_only",
            "status": status,
            "target_url": DIRECTUS_URL,
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
                "policies": {"method": "GET", "resource": "/policies", "result": "denied", "success": False},
            },
        }

    def manifest(self) -> dict:
        return {
            "kind": "create_manifest_draft_only",
            "operations": [
                {
                    "operation_id": f"op-{index}",
                    "operation": "create_feed_draft" if index < 28 else "create_gallery_draft",
                    "original_uri": f"https://source.example.test/{index}",
                }
                for index in range(35)
            ],
        }

    def fresh_target_absence_report(self, manifest: dict, *, status: str = "approved") -> dict:
        original_uris = [operation["original_uri"] for operation in manifest["operations"]]
        return {
            "kind": "fresh_target_absence_before_create",
            "status": status,
            "target_url": DIRECTUS_URL,
            "observed_at": "2026-06-22T12:05:00Z",
            "approval_sha256": APPROVAL_SHA,
            "manifest_sha256": MANIFEST_SHA,
            "target_baseline_sha256": "7" * 64,
            "checked_operation_count": 35,
            "checked_original_uris": list(original_uris),
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


if __name__ == "__main__":
    unittest.main()
