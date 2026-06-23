# Task B slice 9.6 - Pre-create safety gates

Status: implemented and ready for review

Date: 2026-06-22

## Scope

This slice replaces the unconditional `--execute` block in
`cms/utils/wordpress/create_manifest_executor.py` with a fail-closed
two-gate boundary.

Implemented:

- `permission-evidence-create-only.json` validation through
  `validate_permission_evidence_report`;
- `fresh-target-absence-before-create.json` validation through
  `validate_fresh_target_absence_report`;
- execute-mode CLI flags `--permission-evidence` and
  `--fresh-target-absence`;
- execute-mode requirement for `DIRECTUS_TOKEN`;
- dry-run behavior unchanged: no gate files required and zero POST requests;
- execute-mode gate validation before any client construction or POST emission;
- safe create-only client construction after both gates pass when no test client
  is supplied;
- real POST emission still intentionally blocked after the gate boundary.

## Required gate artifacts

`permission-evidence-create-only.json` must be an approved report for the exact
target URL, observed timestamp, credential-free execution identity, explicit
create probe, and explicit denied probes for `PATCH`, `PUT`, `DELETE`, schema,
settings, users, roles, and permissions. Optional policies evidence is rejected
if it reports success.

`fresh-target-absence-before-create.json` must be an approved report for the
exact approved manifest and approval hashes, operation count 35, exact
manifest `original_uri` set, current target URL, target baseline hash, and
per-URI absence evidence. Any route, slug, protected artifact, drift,
ambiguous, skipped, stale, missing, or extra evidence fails closed.

## Safety properties

- Dry-run sends no POST requests and does not require live probes.
- Execute mode fails closed when either gate path is missing, malformed,
  rejected, stale, ambiguous, or inconsistent with the manifest.
- `PATCH`, `PUT`, and `DELETE` remain blocked before transport use.
- No media upload, schema apply, permission mutation, or production write is
  performed by this slice.
- A successful gate boundary ends with `real writer is not implemented in this
  slice`.

## Verification

Executed from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_pre_create_gates.py' -v
uv run python -m unittest discover -s tests -p 'test_create_manifest_executor.py' -v
```

Result:

- 21 pre-create gate tests passed;
- 15 create-manifest executor tests passed;
- no synthetic test emitted a network request or production POST.

## Gate 2 live result - 2026-06-23

Fresh target absence evidence was generated outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/fresh-target-absence-before-create-20260623T155104Z/fresh-target-absence-before-create.json
```

The report is intentionally `rejected`, not approved.

Findings:

- the approved source artifacts matched the expected hashes;
- the manifest contained 35 operations, all `draft` and `create_only`;
- the create-only token could perform the required read-only checks;
- live Directus checks used only `GET /server/info` and `GET /items/feeds`;
- `71` live GET requests returned HTTP `200`;
- no route collision, protected `original_uri` collision, ambiguous match, or
  skipped check was found;
- `14` slug collision entries were found, representing `7` unique manifest
  slugs already present in both the target baseline and current live Directus
  view.

Artifact hashes:

```text
73f7cdb06cae1fc4080a7bde5a6518f0e06daf59640cd630b0819f1f2f50e308  fresh-target-absence-input-validation.json
e42a1daa96efd1a95c35810c3dbe735a8d7880666779380e08c04b66cd173d8e  fresh-target-absence-live-requests.json
addfd2adca5deb073e8aa4689acb76f704d0dafafd340223c9a7701c69e198e9  fresh-target-absence-before-create.json
```

The validator correctly rejects this Gate 2 artifact with:

```text
fresh target absence status mismatch: expected 'approved', got 'rejected'
```

No `--execute` run was performed because a rejected absence gate is a stop
condition.

## Narrowed Gate 2 result - 2026-06-23

The rejected manifest was narrowed outside Git to remove the 7 colliding article
operations. Artifact directory:

```text
/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z
```

Narrowed counts:

```text
create_feed_draft: 21
create_gallery_draft: 7
total_operations: 28
```

The narrowed Gate 2 report is approved:

```text
/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z/fresh-target-absence-before-create-narrowed.json
```

SHA-256:

```text
bbf399f35c138396dc3240c5198c05ef8d45f7d7f95296f087bc377ab39a8a55
```

Verification:

- `57` live Directus requests;
- methods: `GET` only;
- status codes: `200`;
- route collisions: `0`;
- slug collisions: `0`;
- protected/original URI collisions: `0`;
- ambiguous matches: `0`;
- skipped checks: `0`;
- local `validate_fresh_target_absence_report` accepted the narrowed report
  with `expected_operation_count=28`.

No executor `--execute` run was performed. The executor currently binds to the
original 35-operation hash and count, so narrowed Gate 2 is evidence only until
a separate executor wiring slice updates that contract.

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/specification.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/runbook.md
  - docs/migrations/wordpress-to-directus/agent-loop.md
  - docs/migrations/wordpress-to-directus/task-b-inventory-contracts.md
  - docs/migrations/wordpress-to-directus/task-b-cli-integration.md
  - docs/migrations/wordpress-to-directus/task-b-create-manifest-executor.md
  - docs/migrations/wordpress-to-directus/task-b-create-only-directus-client.md
  - docs/migrations/wordpress-to-directus/task-b-permission-gate.md
  - cms/utils/wordpress/create_manifest_executor.py
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/inventory/permission_gate.py
  - cms/utils/wordpress/inventory/canonical.py
  - cms/utils/wordpress/tests/test_create_manifest_executor.py
files_changed:
  - cms/utils/wordpress/pre_create_gates.py
  - cms/utils/wordpress/create_manifest_executor.py
  - cms/utils/wordpress/tests/test_pre_create_gates.py
  - cms/utils/wordpress/tests/test_create_manifest_executor.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-create-manifest-executor.md
  - docs/migrations/wordpress-to-directus/task-b-pre-create-safety-gates.md
findings:
  - The executor can validate gate reports without performing live permission probes.
  - The fresh absence validator binds the gate to the approved manifest hash, approval hash, operation count, target URL, and exact original_uri set.
  - Real writer implementation remains a separate slice to avoid mixing gate validation with production mutation.
verification:
  - uv run python -m unittest discover -s tests -p 'test_pre_create_gates.py' -v
  - uv run python -m unittest discover -s tests -p 'test_create_manifest_executor.py' -v
production_artifact_impact: none
risks:
  - Gate report generation is not implemented here; operators must create approved run artifacts outside Git.
  - Media upload, ledger-backed idempotency, and serial POST execution remain unimplemented.
open_questions:
  - Which exact live permission and fresh absence artifacts will be approved for the production run?
next_action: Implement the serial real writer only after the live gate artifacts, staging rehearsal, ledger path, and explicit production approval are available.
```
