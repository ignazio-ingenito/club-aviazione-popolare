# Task B slice 9.5 - Draft-only create-manifest executor

Status: implemented; pre-create gate boundary wired in a follow-up slice

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
- `--execute` requires `--permission-evidence`, `--fresh-target-absence`,
  and `DIRECTUS_TOKEN`;
- execute-mode gate validation is wired before any transport client can be
  created or any POST can be emitted.

## Safety properties

- Dry-run emits no POST requests.
- The request plan contains only `POST /items/feeds` draft creates.
- `PATCH`, `PUT`, and `DELETE` remain forbidden before transport use.
- The executor does not use `parser.yaml`, joblib cache, or the legacy mutable
  importer.
- The code does not upload media and does not execute a real Directus write in
  this slice.
- Execute mode validates the permission and fresh-target-absence gate reports,
  then stops with `real writer is not implemented in this slice`.

## Future dry-run command

```bash
cd cms/utils/wordpress
uv run python create_manifest_executor.py \
  --manifest /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-draft-only.json \
  --approval /home/iingenito/cap-migration-runs/20260622T110402Z/migration-approval.json \
  --output-dir /home/iingenito/cap-migration-runs/20260622T110402Z/executor-dry-run
```

## Next gate

Real execution remains blocked in code after the pre-create safety gates pass.
The next approved slice must implement the serial writer, media handling, and
ledger-backed idempotency before any production POST is allowed.

## Fresh target absence run - 2026-06-23

Gate 2 was generated against the approved manifest hash
`902e118a73acad4aacd504f6076ef867c7693f2d16144a45cdd78014269c6e4d`
using only the create-only credential and live `GET` requests.

Result:

- status: `rejected`;
- checked operations: `35`;
- live requests: `71`, all `GET`;
- live status codes: `200`;
- route collisions: `0`;
- protected `original_uri` collisions: `0`;
- skipped checks: `0`;
- slug collision entries: `14`, representing `7` unique manifest slugs
  already present in the target baseline and current Directus view.

Artifact:

```text
/tmp/cap-migration-runs/20260622T110402Z/fresh-target-absence-before-create-20260623T155104Z/fresh-target-absence-before-create.json
```

SHA-256:

```text
addfd2adca5deb073e8aa4689acb76f704d0dafafd340223c9a7701c69e198e9
```

Because Gate 2 is rejected, `create_manifest_executor.py --execute` was not
run. The approved manifest must be regenerated or narrowed to exclude existing
target slugs before the execute boundary can be tested again.

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
  - cms/utils/wordpress/pre_create_gates.py
  - cms/utils/wordpress/tests/test_pre_create_gates.py
  - docs/migrations/wordpress-to-directus/task-b-create-manifest-executor.md
  - docs/migrations/wordpress-to-directus/task-b-pre-create-safety-gates.md
findings:
  - The approved manifest contains embedded source records but no media upload payloads.
  - The first safe executor slice can validate and plan draft feed creates without performing writes.
verification:
  - Focused executor and pre-create gate tests passed in the follow-up slice.
production_artifact_impact: none
risks:
  - The execution path is intentionally blocked until create-only token evidence and fresh target absence validation are wired.
  - Media upload and ledger-backed idempotency remain separate future slices.
open_questions:
  - Which exact Directus permission report should be bound to the execution gate?
next_action: Run dry-run reporting, then stop at the create-only token and explicit execution approval gate.
```
