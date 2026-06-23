# Task E - Append-only migration ledger design

Status: proposed for review; not applied

Date: 2026-06-22

## Scope

This slice designs the migration ledger required by ADR 0001 and the migration
specification.

It does not authorize or perform:

- Directus schema changes;
- Directus role, policy, permission, user, or token changes;
- production `POST`;
- content import;
- media upload;
- backfill into protected `feeds`, `directus_files`, `directus_folders`, or
  relation rows;
- mutation or cleanup of existing Directus artifacts.

The ledger is a separate append-only provenance model. Existing production
content remains authoritative and immutable.

## Design Goals

- Record why a source identity maps to a target object.
- Record every object created by a migration run.
- Support idempotency without updating protected target rows.
- Support corrections through superseding entries, never in-place edits.
- Keep production run artifacts outside Git while storing non-secret hashes and
  stable identifiers in Directus.
- Let read-only verification prove every created object belongs to a run ledger.

## Proposed Collections

### `migration_runs`

Purpose: one row per migration run or rehearsal run.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `run_id` | string | yes | Unique operator-provided run identity, e.g. `wp-public-20260622T120000Z`. |
| `environment` | string | yes | `local`, `staging`, or `production`. |
| `status` | string | yes | `planned`, `running`, `completed`, `failed`, `accepted`, or `superseded`. |
| `source_inventory_sha256` | string | yes | Hash of the accepted source inventory artifact. |
| `target_baseline_sha256` | string | yes | Hash of the accepted target baseline artifact. |
| `reconciliation_sha256` | string | yes | Hash of the accepted reconciliation artifact. |
| `write_manifest_sha256` | string | yes | Hash of the exact write manifest. |
| `code_commit` | string | yes | Git commit used for the run. |
| `operator` | string | yes | Recorded operator identifier, not a secret. |
| `reviewer` | string | no | Reviewer identifier when available. |
| `started_at` | datetime | yes | UTC run start. |
| `completed_at` | datetime | no | UTC completion timestamp. |
| `approval_timestamp` | datetime | no | Reviewer approval timestamp for accepted runs. |
| `notes` | text | no | Non-secret operational notes. |

Constraints:

- `run_id` unique.
- No update/delete permission for migration execution identities.
- Status corrections are new run rows or reviewer notes outside production
  writes unless a separate schema/admin procedure is approved.

### `migration_ledger`

Purpose: append-only entries for source-to-target provenance and run-owned
object creation.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `entry_id` | string | yes | Unique deterministic ledger entry identity. |
| `run` | many-to-one | yes | Relation to `migration_runs`. |
| `run_id` | string | yes | Denormalized run identity for request logs and recovery. |
| `entry_type` | string | yes | `pre_existing_match`, `migration_created`, `verification`, or `supersession`. |
| `source_system` | string | yes | Usually `wordpress`. |
| `source_type` | string | yes | `post`, `media`, `gallery`, `category`, `member_post`, etc. |
| `source_identity` | string | yes | Stable identity such as `wordpress:post:<id>`. |
| `source_url` | string | no | Canonical source URL when available. |
| `source_hash` | string | no | Deterministic source inventory hash. |
| `target_collection` | string | yes | Target collection, e.g. `feeds`, `directus_files`, `member_feeds`. |
| `target_id` | string | yes | Directus target id serialized as text. |
| `target_status` | string | yes | `pre_existing_protected`, `migration_created`, `quarantined`, or `verification_only`. |
| `target_hash` | string | no | Target row/file/relation fingerprint when available. |
| `artifact_kind` | string | yes | `feed`, `file`, `folder`, `relation`, `gallery`, `category`, `credential`, etc. |
| `match_state` | string | yes | Reconciliation state that authorized the entry. |
| `evidence_kind` | string | yes | `ledger_match`, `exact_existing`, `validated_historical_mapping`, `approved_create_candidate`, or `post_run_verification`. |
| `evidence` | json | yes | Redacted machine-readable evidence, no body content or secrets. |
| `approval` | json | no | Reviewer, timestamp, manifest hash, and approval note for create entries. |
| `verification` | json | no | Post-create or post-run verification result. |
| `request_audit_ref` | string | no | Path or hash reference to external request audit artifact. |
| `supersedes_entry` | many-to-one | no | Prior ledger entry superseded by this entry. |
| `supersession_reason` | string | no | Required when `supersedes_entry` is set. |
| `created_at` | datetime | yes | Directus/system creation timestamp. |
| `created_by` | uuid | no | Directus user when available. |

Constraints:

- `entry_id` unique.
- `run_id + source_identity + target_collection + target_id + artifact_kind`
  should be unique for non-supersession entries in one run.
- `supersedes_entry` may point only to an existing ledger entry.
- `supersession_reason` is required when `supersedes_entry` is populated.
- No update/delete permission for migration execution identities.

## Entry Types

### `pre_existing_match`

Records that a source identity maps to an already protected Directus object.

Use when reconciliation classified the source as:

- `ledger_match`;
- `exact_existing`;
- `validated_historical_mapping`;
- `protected_existing_drift`.

This entry never authorizes mutation of the target object. It only prevents a
future run from proposing a duplicate create candidate.

### `migration_created`

Records a new object created by the current run.

Use for:

- feeds;
- media files;
- folders;
- gallery relation rows;
- members-only records;
- account-bootstrap records when later approved.

The target object remains draft or non-published until the separate editorial
workflow publishes it.

### `verification`

Records post-run verification evidence, such as protected-object unchanged
checks or created-object reachability checks.

This is optional for small runs but recommended for production because it keeps
the invariant proof close to the run identity.

### `supersession`

Records a correction to a previous ledger entry.

Examples:

- a prior manual match is later proven stale;
- a source identity was classified with stronger evidence;
- a failed run created an object whose outcome was initially ambiguous and
  later resolved.

The superseded row remains unchanged. Consumers must compute the effective
ledger by following supersession entries and ignoring superseded entries for
future matching decisions.

## Supersession Model

Corrections are append-only.

Rules:

1. Never update the old ledger entry.
2. Never delete the old ledger entry.
3. Create a new row with `entry_type = supersession`.
4. Set `supersedes_entry` to the old row.
5. Put the corrected target/source/evidence fields in the new row.
6. Set `supersession_reason`.
7. Require reviewer approval in `approval` for production corrections.

Effective-ledger consumers must:

1. load all ledger entries for the source identity;
2. build the set of entries referenced by `supersedes_entry`;
3. ignore those superseded entries for automatic matching;
4. fail closed if two non-superseded entries still claim incompatible targets.

## Run Identity

`run_id` is operator-provided and must be unique.

Recommended format:

```text
<scope>-<environment>-<YYYYMMDDTHHMMSSZ>
```

Examples:

```text
wp-public-staging-20260622T120000Z
wp-public-production-20260622T130000Z
wp-soci-staging-20260622T140000Z
```

The run ID must appear in:

- `migration_runs.run_id`;
- every `migration_ledger.run_id`;
- external run artifact directory names;
- request audit logs;
- dry-run and execution reports.

## Mapping Rules

### Pre-existing Protected Objects

For protected existing Directus objects, ledger entries are diagnostic and
idempotency evidence only.

They must not:

- backfill source identity into protected `feeds` or file rows;
- update `original_uri`;
- replace cover, category, folder, or gallery relations;
- change status or publication data.

### Migration-Created Objects

For migration-created objects, ledger entries are mandatory before the run can
be accepted.

If an object is created but its ledger entry cannot be written, stop the run.
Record the object in the external request audit and treat the run as failed
until manual recovery proves the final state.

## Permission Model

### Read-only Identity

May read:

- `migration_runs`;
- `migration_ledger`;
- target collections required for invariant checks.

Must not create, update, or delete ledger rows.

### Create-only Execution Identity

Current draft-feed-only stage remains narrower and has no ledger write access.

When the real writer is extended to ledger-backed idempotency, it may be granted:

- `migration_runs.read`;
- `migration_ledger.read`;
- `migration_ledger.create`;
- `migration_runs.create` only if run creation is performed by the executor.

It must not have:

- `migration_runs.update`;
- `migration_runs.delete`;
- `migration_ledger.update`;
- `migration_ledger.delete`;
- schema, settings, users, roles, policies, or permission-management access.

### Operator/Admin Procedure

If an accepted production run needs a status correction, use a separate
operator-admin procedure with explicit approval. Do not broaden the migration
execution identity to update ledger rows.

## Request Audit Interaction

The request audit log remains outside Git and is the source of truth for HTTP
method verification.

Ledger rows should reference the request audit by hash or stable path, but must
not store:

- bearer tokens;
- request headers containing credentials;
- article bodies;
- binary media;
- private member metadata;
- WordPress password hashes.

## Proposed Apply Sequence

This is a future schema task and requires explicit approval before execution.

1. Generate a schema-plan artifact for `migration_runs` and `migration_ledger`.
2. Verify target baseline and backup evidence.
3. Apply schema in staging.
4. Verify append-only permission behavior in staging.
5. Add ledger-backed idempotency tests.
6. Add real writer integration against disposable staging data.
7. Request explicit production approval for schema apply.
8. Apply production schema.
9. Regenerate permission evidence for the final execution identity.

## Stop Conditions

Stop before implementation or apply if:

- the design would require updating protected `feeds`, `directus_files`,
  folders, or relations;
- append-only cannot be enforced with the planned Directus role/policy model;
- the migration identity would need update or delete permissions on ledger rows;
- a correction requires mutating an existing ledger row instead of appending a
  supersession entry;
- live schema, permission, or production action has not been explicitly
  approved;
- request audit and ledger disagree on created object IDs.

## Handoff

```yaml
files_inspected:
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/migrations/wordpress-to-directus/specification.md
  - docs/migrations/wordpress-to-directus/runbook.md
  - docs/migrations/wordpress-to-directus/agent-loop.md
  - docs/migrations/wordpress-to-directus/task-b-directus-migration-identities.md
  - docs/migrations/wordpress-to-directus/task-b-directus-permission-implementation-plan.md
  - docs/migrations/wordpress-to-directus/task-b-create-manifest-executor.md
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/tests/test_directus_create_only.py
files_changed:
  - docs/migrations/wordpress-to-directus/task-e-append-only-ledger-design.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
findings:
  - The ledger should be separate from protected content rows.
  - Two collections are sufficient for the first design: `migration_runs` and
    `migration_ledger`.
  - Supersession is append-only and must not mutate older ledger rows.
verification:
  - Documentation diff review.
production_artifact_impact: none
risks:
  - Directus schema and permission details still need a future schema-plan
    artifact and staging verification.
open_questions:
  - Whether run creation should be operator-created before execution or
    executor-created with `migration_runs.create`; operator-created is safer for
    first production run.
next_action: Review this design, then create a schema-plan generator and tests in a later approved implementation slice.
```
