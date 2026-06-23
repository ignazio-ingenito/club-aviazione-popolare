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

## Narrowed manifest after Gate 2 - 2026-06-23

A narrowed artifact set was generated outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z
```

The narrowing removed 7 manifest operations whose slugs already exist in both
the target baseline and current live Directus view:

- `2015-revisione-l2000`;
- `2016-04-corso-compositi-toscana`;
- `2017-03-ist-serristori`;
- `2017-corso-intelggio`;
- `diario-di-un-volo-bellissimo`;
- `mai-perdere-la-speranza`;
- `trofeo-damiani-2025-il-volo-di-lucio-castrogiovanni`.

Counts after narrowing:

```text
create_feed_draft: 21
create_gallery_draft: 7
total_operations: 28
```

Artifact hashes:

```text
gate2-slug-collisions.json: 92228cd8642c994baca96b49c6337f970c7cb16c1b65b3e10414824e1efda631
migration-approval-narrowed.json: 6b4093177cf4156084292add1bb1e7adac802d9f8c60e1633b5fc68621d98994
create-manifest-draft-only-narrowed.json: 9dd3289b2db550dc329032e7e825e74a48449a07ff69547ee455c3f4d9dbc0f9
narrowing-report.json: cd4466278621a56652158deb9b94a658acba9fc8868631b10b0ff744d44a4c38
narrowed-manifest-validation.json: 4659fb75dd23074a39da69eb3e47626f923ace60970610ff7aca2ea954ac49cc
fresh-target-absence-live-requests-narrowed.json: 642b4bbf225fa9b6935ea5e1f2b82369e5b7f2430abb4afebeb97af747da6f32
fresh-target-absence-before-create-narrowed.json: bbf399f35c138396dc3240c5198c05ef8d45f7d7f95296f087bc377ab39a8a55
```

The narrowed fresh target absence report is `approved` for 28 operations. The
live check used only `GET /server/info` and `GET /items/feeds`, with 57 GET
requests returning HTTP 200 and zero route, slug, original URI, protected,
ambiguous, or skipped collisions.

The executor was not run. The current executor still hardcodes the original
manifest hash and expected count of 35 operations; it must be explicitly wired
or parameterized for the narrowed manifest in a separate reviewed slice before
any dry-run or execution gate validation uses these artifacts.

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
