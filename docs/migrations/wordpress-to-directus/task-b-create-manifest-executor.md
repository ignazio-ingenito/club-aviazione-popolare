# Task B slice 9.5 - Draft-only create-manifest executor

Status: implemented and ready for review

Date: 2026-06-22

## Scope

This slice adds a dry-run-first executor scaffold for the approved
`create-manifest-draft-only.json` artifact in
`/home/iingenito/cap-migration-runs/20260622T110402Z`.

Implemented:

- approved artifact hash checks for `migration-approval.json` and
  `create-manifest-draft-only.json`;
- count checks for 28 article drafts, 7 gallery drafts, and 35 operations;
- fail-closed validation for non-draft status, unknown operations, missing
  source records, source hash mismatch, and update/delete intent;
- local validation, request-plan, dry-run, and stop-condition reports;
- dry-run as the default mode;
- `--execute` fail-closed until a later gate supplies create-only permission
  evidence and fresh target absence validation.

## Safety properties

- Dry-run emits no POST requests.
- The request plan contains only `POST /items/feeds` draft creates.
- `PATCH`, `PUT`, and `DELETE` remain forbidden before transport use.
- The executor does not use `parser.yaml`, joblib cache, or the legacy mutable
  importer.
- The code does not upload media and does not execute a real Directus write in
  this slice.

## Future dry-run command

```bash
cd cms/utils/wordpress
uv run python create_manifest_executor.py \
  --manifest /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-draft-only.json \
  --approval /home/iingenito/cap-migration-runs/20260622T110402Z/migration-approval.json \
  --output-dir /home/iingenito/cap-migration-runs/20260622T110402Z/executor-dry-run
```

## Next gate

Real execution remains blocked in code until a Directus identity is proven
create-only, fresh target absence validation is bound to the run, and the
operator gives explicit approval for execution in the current session.

## Handoff

```yaml
files_inspected:
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/inventory/write_manifest.py
  - cms/utils/wordpress/inventory/permission_gate.py
  - docs/migrations/wordpress-to-directus/task-b-create-only-directus-client.md
  - docs/migrations/wordpress-to-directus/task-b-write-manifest.md
  - docs/migrations/wordpress-to-directus/task-b-permission-gate.md
files_changed:
  - cms/utils/wordpress/create_manifest_executor.py
  - cms/utils/wordpress/tests/test_create_manifest_executor.py
  - docs/migrations/wordpress-to-directus/task-b-create-manifest-executor.md
findings:
  - The approved manifest contains embedded source records but no media upload payloads.
  - The first safe executor slice can validate and plan draft feed creates without performing writes.
verification:
  - Pending full test run from cms/utils/wordpress.
production_artifact_impact: none
risks:
  - The execution path is intentionally blocked until create-only token evidence and fresh target absence validation are wired.
  - Media upload and ledger-backed idempotency remain separate future slices.
open_questions:
  - Which exact Directus permission report should be bound to the execution gate?
next_action: Run dry-run reporting, then stop at the create-only token and explicit execution approval gate.
```
