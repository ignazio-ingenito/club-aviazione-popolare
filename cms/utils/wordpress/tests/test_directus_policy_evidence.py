from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from directus_policy_evidence import evaluate_policy_graph_evidence, main


class DirectusPolicyEvidenceTests(unittest.TestCase):
    def test_approved_graph_passes(self) -> None:
        result = evaluate_policy_graph_evidence(self.approved_payload())

        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["reasons"], [])

    def test_missing_identity_rejects(self) -> None:
        payload = self.approved_payload()
        payload.pop("identity")

        self.assert_rejected(payload, "missing_identity")

    def test_missing_policies_rejects(self) -> None:
        payload = self.approved_payload()
        payload["policies"] = []

        self.assert_rejected(payload, "missing_policies")

    def test_missing_permissions_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"] = []

        self.assert_rejected(payload, "missing_permissions")

    def test_missing_feeds_create_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"] = [self.feeds_read_permission()]

        self.assert_rejected(payload, "missing_feeds_create")

    def test_missing_status_validation_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"][0]["validation"] = {}

        self.assert_rejected(payload, "missing_status_draft_validation")

    def test_wrong_status_validation_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"][0]["validation"]["status"]["_eq"] = "published"

        self.assert_rejected(payload, "missing_status_draft_validation")

    def test_missing_status_preset_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"][0]["presets"] = {}

        self.assert_rejected(payload, "missing_status_draft_preset")

    def test_wrong_status_preset_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"][0]["presets"]["status"] = "published"

        self.assert_rejected(payload, "missing_status_draft_preset")

    def test_unexpected_field_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"][0]["fields"].append("cover")

        self.assert_rejected(payload, "unexpected_feeds_create_field")

    def test_update_permission_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"].append({"collection": "feeds", "action": "update", "fields": ["title"]})

        self.assert_rejected(payload, "forbidden_update_permission")

    def test_delete_permission_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"].append({"collection": "feeds", "action": "delete", "fields": ["id"]})

        self.assert_rejected(payload, "forbidden_delete_permission")

    def test_wildcard_collection_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"][0]["collection"] = "*"

        self.assert_rejected(payload, "wildcard_collection")

    def test_wildcard_action_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"][0]["action"] = "*"

        self.assert_rejected(payload, "wildcard_action")

    def test_system_access_rejects(self) -> None:
        for collection in ("schema", "settings", "users", "roles", "permissions", "policies"):
            with self.subTest(collection=collection):
                payload = self.approved_payload()
                payload["permissions"].append({"collection": collection, "action": "read", "fields": ["*"]})

                self.assert_rejected(payload, "forbidden_system_access")

    def test_file_create_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"].append({"collection": "directus_files", "action": "create", "fields": ["id"]})

        self.assert_rejected(payload, "forbidden_file_or_folder_access")

    def test_folder_create_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"].append({"collection": "directus_folders", "action": "create", "fields": ["id"]})

        self.assert_rejected(payload, "forbidden_file_or_folder_access")

    def test_malformed_payload_rejects(self) -> None:
        result = evaluate_policy_graph_evidence([])  # type: ignore[arg-type]

        self.assertEqual(result["status"], "rejected")
        self.assertIn("malformed_payload", result["reasons"])

    def test_ambiguous_broad_policy_graph_rejects(self) -> None:
        payload = self.approved_payload()
        payload["permissions"].append(dict(payload["permissions"][0]))

        self.assert_rejected(payload, "ambiguous_policy_graph")

    def test_existing_static_example_passes_after_normalization(self) -> None:
        path = Path(__file__).parents[4] / "docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json"
        payload = json.loads(path.read_text(encoding="utf-8"))

        result = evaluate_policy_graph_evidence(payload)

        self.assertEqual(result["status"], "approved")

    def test_cli_writes_approved_result(self) -> None:
        with TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "evidence.json"
            output_path = Path(tmp) / "evaluation.json"
            input_path.write_text(json.dumps(self.approved_payload()), encoding="utf-8")

            exit_code = main(["--input", str(input_path), "--output", str(output_path)])

            self.assertEqual(exit_code, 0)
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(written["status"], "approved")

    def test_cli_refuses_to_overwrite_without_force(self) -> None:
        with TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "evidence.json"
            output_path = Path(tmp) / "evaluation.json"
            input_path.write_text(json.dumps(self.approved_payload()), encoding="utf-8")
            output_path.write_text("{}", encoding="utf-8")

            exit_code = main(["--input", str(input_path), "--output", str(output_path)])

            self.assertEqual(exit_code, 1)

    def assert_rejected(self, payload: dict, reason: str) -> None:
        result = evaluate_policy_graph_evidence(payload)
        self.assertEqual(result["status"], "rejected")
        self.assertIn(reason, result["reasons"])

    def approved_payload(self) -> dict:
        return {
            "kind": "directus_policy_graph_evidence",
            "target_url": "https://cap-cms.skunklabs.uk",
            "observed_at": "2026-06-22T12:00:00Z",
            "identity": {
                "label": "cap-wordpress-create-only",
                "role": "cap-wordpress-create-only",
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

    def feeds_read_permission(self) -> dict:
        return {
            "collection": "feeds",
            "action": "read",
            "permissions": {},
            "validation": {},
            "presets": None,
            "fields": ["id", "status", "slug"],
        }


if __name__ == "__main__":
    unittest.main()
