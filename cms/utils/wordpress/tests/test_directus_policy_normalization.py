from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from directus_policy_evidence import (
    DirectusPolicyEvidenceError,
    evaluate_policy_graph_evidence,
    main,
    normalize_directus_policy_graph_payload,
)


class DirectusPolicyNormalizationTests(unittest.TestCase):
    def test_raw_approved_graph_normalizes_and_evaluates_approved(self) -> None:
        normalized = normalize_directus_policy_graph_payload(self.raw_payload())
        evaluation = evaluate_policy_graph_evidence(normalized)

        self.assertEqual(normalized["kind"], "directus_policy_graph_evidence")
        self.assertEqual(evaluation["status"], "approved")

    def test_missing_target_url_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload.pop("target_url")

        self.assert_normalization_error(payload)

    def test_missing_observed_at_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload.pop("observed_at")

        self.assert_normalization_error(payload)

    def test_missing_identity_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload.pop("identity")

        self.assert_normalization_error(payload)

    def test_missing_identity_role_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["identity"].pop("role")

        self.assert_normalization_error(payload)

    def test_identity_role_not_found_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["identity"]["role"] = "role-other"

        self.assert_normalization_error(payload)

    def test_policy_not_attached_to_identity_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["policies"][0]["roles"] = ["role-other"]

        self.assert_normalization_error(payload)

    def test_permission_references_unknown_policy_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["permissions"][0]["policy"] = "policy-missing"

        self.assert_normalization_error(payload)

    def test_permission_attached_to_unrelated_policy_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["policies"].append(
            {
                "id": "policy-other",
                "name": "Unrelated policy",
                "roles": ["role-other"],
            },
        )
        payload["permissions"].append(
            {
                "id": "perm-other",
                "policy": "policy-other",
                "collection": "feeds",
                "action": "read",
                "permissions": {},
                "validation": {},
                "presets": None,
                "fields": ["id"],
            },
        )

        self.assert_normalization_error(payload)

    def test_multiple_identity_roles_without_explicit_selection_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["identity"].pop("role")
        payload["identity"]["roles"] = ["role-create-only", "role-other"]

        self.assert_normalization_error(payload)

    def test_wildcard_collection_survives_normalization_and_evaluator_rejects(self) -> None:
        payload = self.raw_payload()
        payload["permissions"][0]["collection"] = "*"

        self.assert_normalizes_then_rejects(payload, "wildcard_collection")

    def test_feeds_update_survives_normalization_and_evaluator_rejects(self) -> None:
        payload = self.raw_payload()
        payload["permissions"].append(self.permission(action="update", fields=["title"]))

        self.assert_normalizes_then_rejects(payload, "forbidden_update_permission")

    def test_feeds_delete_survives_normalization_and_evaluator_rejects(self) -> None:
        payload = self.raw_payload()
        payload["permissions"].append(self.permission(action="delete", fields=["id"]))

        self.assert_normalizes_then_rejects(payload, "forbidden_delete_permission")

    def test_malformed_fields_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["permissions"][0]["fields"] = "status"

        self.assert_normalization_error(payload)

    def test_malformed_validation_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["permissions"][0]["validation"] = []

        self.assert_normalization_error(payload)

    def test_malformed_presets_fails_normalization(self) -> None:
        payload = self.raw_payload()
        payload["permissions"][0]["presets"] = "draft"

        self.assert_normalization_error(payload)

    def test_normalized_output_matches_evaluator_input_contract(self) -> None:
        normalized = normalize_directus_policy_graph_payload(self.raw_payload())

        self.assertEqual(normalized["target_url"], "https://cap-cms.skunklabs.uk")
        self.assertEqual(normalized["observed_at"], "2026-06-22T12:00:00Z")
        self.assertEqual(normalized["directus_version"], "11.13.2")
        self.assertEqual(normalized["identity"]["role"], "role-create-only")
        self.assertEqual(normalized["policies"][0]["id"], "policy-create-only")
        self.assertEqual(normalized["permissions"][0]["policy"], "policy-create-only")
        self.assertEqual(evaluate_policy_graph_evidence(normalized)["status"], "approved")

    def test_cli_raw_mode_writes_normalized_and_evaluation_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "raw.json"
            normalized_path = Path(tmp) / "normalized.json"
            evaluation_path = Path(tmp) / "evaluation.json"
            raw_path.write_text(json.dumps(self.raw_payload()), encoding="utf-8")

            exit_code = main(
                [
                    "--raw-input",
                    str(raw_path),
                    "--normalized-output",
                    str(normalized_path),
                    "--evaluation-output",
                    str(evaluation_path),
                ],
            )

            self.assertEqual(exit_code, 0)
            normalized = json.loads(normalized_path.read_text(encoding="utf-8"))
            evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
            self.assertEqual(normalized["kind"], "directus_policy_graph_evidence")
            self.assertEqual(evaluation["status"], "approved")

    def test_cli_raw_mode_refuses_to_overwrite_without_force(self) -> None:
        with TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "raw.json"
            normalized_path = Path(tmp) / "normalized.json"
            evaluation_path = Path(tmp) / "evaluation.json"
            raw_path.write_text(json.dumps(self.raw_payload()), encoding="utf-8")
            normalized_path.write_text("{}", encoding="utf-8")

            exit_code = main(
                [
                    "--raw-input",
                    str(raw_path),
                    "--normalized-output",
                    str(normalized_path),
                    "--evaluation-output",
                    str(evaluation_path),
                ],
            )

            self.assertEqual(exit_code, 1)

    def assert_normalization_error(self, payload: dict) -> None:
        with self.assertRaises(DirectusPolicyEvidenceError):
            normalize_directus_policy_graph_payload(payload)

    def assert_normalizes_then_rejects(self, payload: dict, reason: str) -> None:
        normalized = normalize_directus_policy_graph_payload(payload)
        evaluation = evaluate_policy_graph_evidence(normalized)

        self.assertEqual(evaluation["status"], "rejected")
        self.assertIn(reason, evaluation["reasons"])

    def raw_payload(self) -> dict:
        return {
            "target_url": "https://cap-cms.skunklabs.uk",
            "observed_at": "2026-06-22T12:00:00Z",
            "directus_version": "11.13.2",
            "identity": {
                "label": "cap-wordpress-create-only",
                "role": "role-create-only",
            },
            "roles": [
                {
                    "id": "role-create-only",
                    "name": "CAP WordPress create-only",
                }
            ],
            "policies": [
                {
                    "id": "policy-create-only",
                    "name": "CAP WordPress create-only content migration",
                    "roles": ["role-create-only"],
                }
            ],
            "permissions": [self.permission()],
        }

    def permission(self, *, action: str = "create", fields: list[str] | None = None) -> dict:
        return {
            "id": f"perm-feeds-{action}",
            "policy": "policy-create-only",
            "collection": "feeds",
            "action": action,
            "permissions": {},
            "validation": {
                "status": {
                    "_eq": "draft",
                }
            },
            "presets": {
                "status": "draft",
            },
            "fields": fields
            or [
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
