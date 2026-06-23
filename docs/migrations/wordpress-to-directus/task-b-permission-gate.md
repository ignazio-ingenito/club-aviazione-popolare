# Task B slice 9.4 - Permission evidence gate

Status: implemented and ready for review

Date: 2026-06-20

## Scope

This slice adds a pure permission gate for future Directus execution identities.
It validates a `permissions/me` payload against an approved matrix and fails
closed when evidence is missing or broader than expected.

Implemented:

- `validate_permission_evidence` for matrix-based permission checks;
- explicit `PermissionGateError` failures for missing collections, malformed
  payloads, and unexpected broad access;
- a reusable `PermissionExpectation` helper for approved access matrices;
- tests proving approved evidence passes and missing/broad evidence fails.

## Safety properties

- Missing permission evidence stops execution.
- Broader-than-approved access stops execution.
- The helper does not write to Directus.
- The helper does not assume a permissive fallback when the report is partial.

## Files changed

```text
cms/utils/wordpress/inventory/__init__.py
cms/utils/wordpress/inventory/permission_gate.py
cms/utils/wordpress/tests/test_permission_gate.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-permission-gate.md
```

## Verification

Required from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_permission_gate.py' -v
uv run python -m unittest discover -s tests -p 'test_*.py' -v
```

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It only validates permission evidence.
2. Could the validator write to Directus? **No.** It is pure in-memory validation.
3. Could missing permission evidence be treated as acceptable? **No.** It fails closed.
4. Could broader-than-approved access slip through? **No.** It is checked collection by collection.
5. Could malformed payloads be mistaken for valid evidence? **No.** They raise `PermissionGateError`.

## Handoff

```yaml
files_inspected:
  - cms/utils/wordpress/inventory/directus.py
  - cms/utils/wordpress/inventory/models.py
  - cms/utils/wordpress/inventory/reconciliation.py
  - cms/utils/wordpress/tests/test_directus_inventory.py
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-directus-inventory.md
files_changed:
  - cms/utils/wordpress/inventory/__init__.py
  - cms/utils/wordpress/inventory/permission_gate.py
  - cms/utils/wordpress/tests/test_permission_gate.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-permission-gate.md
findings:
  - The authenticated Directus `permissions/me` payload is structured as a collection-by-collection matrix.
  - A pure validator can fail closed without touching the write path.
  - Missing collections and broader-than-approved access are distinct failure modes.
verification:
  - Focused permission-gate tests passed.
  - Full wordpress package test suite passed.
production_artifact_impact: none
risks:
  - This helper still needs to be wired into the eventual production execution path.
open_questions:
  - Which exact approved access matrix should the production executor enforce?
next_action: Wire the approved permission matrix into the future create-only executor and keep closing the remaining Phase 6 checks.
```
