from __future__ import annotations

import unittest

from inventory import ManifestRecord, InventoryScope
from inventory.permission_gate import (
    PermissionExpectation,
    PermissionGateError,
    validate_permission_evidence,
)


class PermissionGateTests(unittest.TestCase):
    def permissions_record(self, payload: dict[str, object]) -> ManifestRecord:
        return ManifestRecord(
            scope=InventoryScope.TARGET,
            entity_type="directus_permissions",
            identity="directus:permissions:me",
            data=payload,
        )

    def test_validate_permission_evidence_accepts_approved_matrix(self) -> None:
        record = self.permissions_record(
            {
                "feeds": {
                    "create": {"access": "full"},
                    "read": {"access": "full", "fields": ["*"]},
                    "update": {"access": "none"},
                    "delete": {"access": "none"},
                    "share": {"access": "none"},
                },
                "directus_files": {
                    "create": {"access": "none"},
                    "read": {"access": "full", "fields": ["*"]},
                    "update": {"access": "none"},
                    "delete": {"access": "none"},
                    "share": {"access": "none"},
                },
            }
        )

        validate_permission_evidence(
            record,
            expected_access={
                "feeds": PermissionExpectation(
                    create="full",
                    read="full",
                    update="none",
                    delete="none",
                    share="none",
                ),
                "directus_files": PermissionExpectation(
                    create="none",
                    read="full",
                    update="none",
                    delete="none",
                    share="none",
                ),
            },
        )

    def test_validate_permission_evidence_rejects_missing_collection(self) -> None:
        record = self.permissions_record(
            {
                "feeds": {
                    "create": {"access": "full"},
                    "read": {"access": "full", "fields": ["*"]},
                    "update": {"access": "none"},
                    "delete": {"access": "none"},
                    "share": {"access": "none"},
                }
            }
        )

        with self.assertRaises(PermissionGateError) as captured:
            validate_permission_evidence(
                record,
                expected_access={
                    "feeds": PermissionExpectation(
                        create="full",
                        read="full",
                        update="none",
                        delete="none",
                        share="none",
                    ),
                    "directus_files": PermissionExpectation(
                        create="none",
                        read="full",
                        update="none",
                        delete="none",
                        share="none",
                    ),
                },
            )
        self.assertIn("directus_files", str(captured.exception))

    def test_validate_permission_evidence_rejects_broad_permission(self) -> None:
        record = self.permissions_record(
            {
                "feeds": {
                    "create": {"access": "full"},
                    "read": {"access": "full", "fields": ["*"]},
                    "update": {"access": "none"},
                    "delete": {"access": "none"},
                    "share": {"access": "none"},
                },
                "directus_files": {
                    "create": {"access": "full"},
                    "read": {"access": "full", "fields": ["*"]},
                    "update": {"access": "none"},
                    "delete": {"access": "none"},
                    "share": {"access": "none"},
                },
            }
        )

        with self.assertRaises(PermissionGateError) as captured:
            validate_permission_evidence(
                record,
                expected_access={
                    "feeds": PermissionExpectation(
                        create="full",
                        read="full",
                        update="none",
                        delete="none",
                        share="none",
                    ),
                },
            )
        self.assertIn("directus_files.create", str(captured.exception))


if __name__ == "__main__":
    unittest.main()
