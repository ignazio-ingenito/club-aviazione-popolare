# Task B slice 9.8 - Directus migration identities and SOPS plan

Status: create-only execution identity created; permission evidence ready

Date: 2026-06-22

## Scope

This slice defines the Directus identities and encrypted secret layout needed to
replace the rejected live pre-create gate artifacts recorded in
`task-b-live-pre-create-gate-artifacts.md`.

It does not authorize or perform:

- Directus role creation;
- Directus user creation;
- token creation;
- permission or access-policy changes;
- schema changes;
- content import;
- media upload;
- `--execute`;
- production `POST`.

The current committed SOPS migration secrets contain one Directus token secret:
`secrets/migration/directus-schema-token.20260622.sops.yaml`. Its non-secret
metadata identifies it as a temporary schema-capable token for the approved
`member_*` schema apply. It must not be used for WordPress content migration
gates or imports.

As of 2026-06-23, the dedicated create-only content-migration secret exists and
is SOPS-encrypted:

```text
secrets/migration/directus-createonly-content-migration.20260622.sops.yaml
```

It contains the create-only role id, static token, service email, target URL,
creation timestamp, identity name, and purpose. Do not print decrypted values
or use this credential for permission-management actions.

## Identity model

Use two separate Directus identities. Do not reuse an admin user, personal user,
schema-capable token, or frontend user token.

| Identity | Purpose | Directus UI objects | Secret file |
| --- | --- | --- | --- |
| `directus-readonly-content-migration` | Target baseline, fresh target absence, preflight reads, post-run invariant reads, route/original_uri collision checks. | Dedicated user plus role/access policy with read-only permissions. | `secrets/migration/directus-readonly-content-migration.20260622.sops.yaml` |
| `directus-createonly-content-migration` | Approved draft feed creation after all gates pass. For the current approved manifest, only `POST /items/feeds` is in scope. | Dedicated user plus role/access policy with read plus feed-create permissions only. | `secrets/migration/directus-createonly-content-migration.20260622.sops.yaml` |

For Directus 11.13.2, the operator should use the UI sections currently visible
as `Users`, `Roles`, and `Access Policies`. The durable requirement is the
effective permission result, not the exact UI label.

## Read-only migration identity

### Allowed permissions

Grant only read access required for target inventory and verification:

| Resource | Operation | Required scope |
| --- | --- | --- |
| `feeds` | `read` | All statuses in migration scope. Fields: `id`, `status`, `slug`, `title`, `date`, `original_uri`, `gallery`, `category`, `cover`, route-relevant fields, and relation keys required by baseline checks. |
| `categories` | `read` | Fields required to resolve category identity and route/category mapping. |
| `directus_files` | `read` | File metadata required by baseline/media checks: `id`, filenames, folder, title, type, filesize, uploaded/modified timestamps, storage metadata, and checksum metadata if exposed. |
| `directus_folders` | `read` | Folder identity, name, parent, and timestamps required by baseline/gallery checks. |
| `directus_relations`, `directus_collections`, `directus_fields` | `read` | Schema metadata required by the existing inventory client to interpret application collections and relations. |
| server/version metadata | `read` | Only if needed by existing inventory tooling. |

If Directus cannot expose one of the metadata resources without broader system
access, do not broaden the role silently. Record the missing endpoint as a
blocking issue and either reduce the inventory scope or request a separately
approved read-only metadata grant.

### Denied permissions

The read-only identity must deny:

- `create`, `update`, `delete`, and `share` on every application collection;
- `create`, `update`, and `delete` on `feeds`;
- `create`, `update`, and `delete` on `categories`;
- `create`, `update`, and `delete` on `directus_files`;
- `create`, `update`, and `delete` on `directus_folders`;
- relation mutation;
- schema mutation;
- settings access;
- users access;
- roles access;
- access-policy access;
- permission-management access;
- flows and automations access;
- admin/system wildcard capabilities.

This identity must not be able to mutate content or system configuration.

## Create-only content migration identity

### Allowed permissions for the current stage

For the current approved draft-only manifest, grant only:

| Resource | Operation | Required scope |
| --- | --- | --- |
| `feeds` | `read` | Enough fields to verify created drafts and to re-check collisions: `id`, `status`, `slug`, `title`, `date`, `original_uri`, `gallery`, `category`, `cover`, and route-relevant fields. |
| `feeds` | `create` | Only records from the approved manifest, targeting `status = draft`. |

Current executor scope is intentionally narrower than the full migration
specification: no media upload, folder creation, category creation, relation
mutation, or ledger write is enabled in this stage.

If a later slice adds media upload or ledger writes, this document must be
updated and reviewed before changing the role. Do not broaden this identity just
to make a gate pass.

### Draft-only constraint

Prefer enforcing `status = draft` at the Directus permission/access-policy
layer with a field preset or validation rule if Directus 11.13.2 can express it
cleanly for this collection.

If Directus cannot enforce `status = draft` at permission level, the executor
remains the authoritative control. In that case:

- permission evidence must explicitly record that the Directus permission model
  cannot express the field-level draft-only constraint;
- the executor must keep validating every manifest operation has
  `target_status = draft`;
- the request plan must contain no non-draft payload;
- publication remains a separate editorial action.

### Denied permissions

The create-only identity must deny:

- `update`, `delete`, and `share` on `feeds`;
- create/update/delete on `categories`;
- create/update/delete on `directus_files` for this stage;
- create/update/delete on `directus_folders` for this stage;
- relation update/delete;
- schema access and schema mutation;
- settings access;
- users access;
- roles access;
- access-policy access;
- permission-management access;
- flows and automations access;
- admin/system wildcard capabilities.

The pre-create gate currently requires these live probes to be conclusive:

| Probe | Method | Resource | Expected result |
| --- | --- | --- | --- |
| `create` | `POST` | `/items/feeds` | `allowed` |
| `patch` | `PATCH` | `/items/feeds` | `denied` |
| `put` | `PUT` | `/items/feeds` | `denied` |
| `delete` | `DELETE` | `/items/feeds` | `denied` |
| `schema` | `GET` | `/schema` | `denied` |
| `settings` | `GET` | `/settings` | `denied` |
| `users` | `GET` | `/users` | `denied` |
| `roles` | `GET` | `/roles` | `denied` |
| `permissions` | `GET` | `/permissions` | `denied` |
| `policies` | `GET` | `/policies` | `denied` if probed |

Any successful forbidden probe fails the gate.

## SOPS secret naming convention

Create no plaintext secret in the repository. Store only SOPS-encrypted files
under `secrets/migration/`.

Required filenames:

```text
secrets/migration/directus-readonly-content-migration.20260622.sops.yaml
secrets/migration/directus-createonly-content-migration.20260622.sops.yaml
```

Filename convention:

```text
secrets/migration/directus-<capability>-content-migration.<YYYYMMDD>.sops.yaml
```

Where `<capability>` is one of:

- `readonly`;
- `createonly`.

Do not reuse `directus-schema-token.*.sops.yaml` for content migration.

## Dry-run create-only identity discovery

On 2026-06-23, a permission-management dry-run prepared the
`directus-createonly-content-migration` identity plan and performed GET-only
discovery against the live Directus target using the admin/schema credential
only for this permission-management check.

No Directus mutation was performed because the explicit apply approval
environment flag was absent.

Sanitized discovery results:

- `GET /server/info`: 200;
- `GET /roles?filter[name][_eq]=directus-createonly-content-migration`: 200,
  zero matching roles;
- `GET /policies?filter[name][_eq]=directus-createonly-content-migration`:
  200, zero matching policies;
- `GET /users?filter[email][_eq]=directus-createonly-content-migration@example.invalid`:
  200, zero matching users;
- `GET /permissions?limit=1`: 200, permission rows readable.

The dry-run artifact is outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-20260623T100342Z/directus-createonly-identity.plan.json
```

Artifact SHA-256:

```text
b651cdef0a7ff916081b58634c3587e89c2ec436819241837a66d3e04dc3813c
```

The next approved apply must create new dedicated resources instead of updating
an existing migration-owned role/policy/user. The current planned execution
scope remains narrower than the full future migration scope: `feeds.read` and
draft-only `feeds.create` only. Media, folder, ledger, and relation creation
remain deferred until separate approval updates this plan.

## Partial create-only identity apply

On 2026-06-23, the permission-management task was rerun with explicit apply
approval:

```text
APPLY_DIRECTUS_CREATEONLY_IDENTITY=true
```

The run used the admin/schema credential only for this permission-management
task and did not use it as a migration execution token.

The run performed only these Directus mutation endpoint families:

| Method | Endpoint | Result |
| --- | --- | --- |
| `POST` | `/roles` | created the dedicated migration role |
| `POST` | `/policies` | created the dedicated migration policy with `admin_access = false` and `app_access = false` |
| `POST` | `/permissions` | created `feeds.read` for the policy |
| `POST` | `/permissions` | created draft-constrained `feeds.create` for the policy |
| `POST` | `/users` | failed with HTTP 400 because the placeholder service email was rejected by Directus validation |

No `PATCH`, `PUT`, or `DELETE` was performed. No content, media, feed, gallery,
schema, folder, or relation endpoint was mutated.

Because user/token creation failed:

- no dedicated execution user is available;
- no create-only token is available;
- no create-only SOPS secret was written;
- no live policy graph evidence was collected with the intended identity;
- production readiness remains blocked.

The apply audit is outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-apply-20260623T102813Z/directus-createonly-identity.apply.json
```

Artifact SHA-256:

```text
0391dbcf3f7aabc49e1bef2d91536c6835a285a17bb98ad472953ae008e71247
```

A follow-up GET-only partial-state check with the admin/schema credential
returned HTTP 403 for the role, policy, and user list endpoints, so it was not
usable as positive proof of the current live state. The partial-state check
artifact is also outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-apply-20260623T102813Z/directus-createonly-identity.partial-state.json
```

Artifact SHA-256:

```text
450fd3e32a9a529f61709c31d301cd0001958094ea3005aa9255bbf3fdaa90d0
```

The next task must treat the migration-owned role, policy, and permissions as
possibly existing. It must read and compare them before any further apply. Do
not delete them and do not blindly update them. The narrowest expected recovery
is to create a valid dedicated service user/static token associated with the
existing migration-owned role, then encrypt the resulting credential with SOPS
and run policy graph evidence collection. If that requires `PATCH`, `PUT`, or
broader permissions, stop for a separate approval.

## Recovery attempt status

On 2026-06-23, the recovery task was rerun with:

```text
APPLY_DIRECTUS_CREATEONLY_IDENTITY=true
```

The fresh GET-only comparison first hit an edge/WAF 403 with `error code: 1010`
when using the default Python urllib client. A GET-only retry with an explicit
User-Agent reached Directus successfully. A role query that requested
`directus_roles.admin_access` and `directus_roles.app_access` returned 403
because those fields were not readable or exposed on `directus_roles`; the
final comparison therefore used readable role fields and verified admin/app
flags on the attached policy.

Final live comparison classification:

```text
partial_state_matches_expected
```

Sanitized comparison result:

- one role named `directus-createonly-content-migration`;
- one policy named `directus-createonly-content-migration`;
- the policy is attached to the role;
- policy `admin_access = false`;
- policy `app_access = false`;
- exactly one `feeds.read` permission;
- exactly one draft-constrained `feeds.create` permission;
- no detected `feeds.update`, `feeds.delete`, `share`, wildcard, or Directus
  system-resource permission in the migration-owned policy;
- zero users for `directus-createonly-content-migration@cap-migration.local`;
- zero users for `directus-createonly-content-migration@example.invalid`.

Because the partial state matched, the recovery attempted only the approved
`POST /users` path. Directus rejected both allowed service emails:

| Email | Result |
| --- | --- |
| `directus-createonly-content-migration@cap-migration.local` | HTTP 400 `FAILED_VALIDATION` for `email` |
| `directus-createonly-content-migration@example.invalid` | HTTP 400 `FAILED_VALIDATION` for `email` |

No service user was created. No token was created. No create-only SOPS secret
was written. No policy graph evidence was collected.

Recovery artifacts are outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-recovery-20260623T122732Z/directus-createonly-identity-recovery-comparison-final.probe.json
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-recovery-20260623T122732Z/directus-createonly-identity-recovery-apply.json
```

Artifact SHA-256:

```text
directus-createonly-identity-recovery-comparison-final.probe.json:
fb13d88d6bea681b58829ad0d33ba3b727b52a9270a14052599f4da0c0128548

directus-createonly-identity-recovery-apply.json:
4a6cf757ac822e91991e1a6204782477c560736daf8f562336fce3f06dc56ffa
```

This initial recovery attempt was superseded by the valid-email recovery below.

## Valid-email recovery and create-only secret

On 2026-06-23, the recovery task was rerun with explicit apply approval and the
Directus-accepted service email:

```text
cap-migration@skunklabs.uk
```

The task repeated fresh GET-only comparison before any mutation and classified
the live state as:

```text
partial_state_matches_expected
```

The only recovery mutation performed was:

| Method | Endpoint | Result |
| --- | --- | --- |
| `POST` | `/users` | created the dedicated service user and static token |

No role, policy, or permission rows were created, updated, or deleted during
this recovery. No `PATCH`, `PUT`, or `DELETE` was performed. No content, media,
feed, gallery, schema, folder, or relation endpoint was mutated.

The encrypted secret was created at:

```text
secrets/migration/directus-createonly-content-migration.20260622.sops.yaml
```

Verified decrypted key names only:

```text
target_url
identity_name
role_id
token
service_email
created_at
purpose
```

Encrypted secret SHA-256:

```text
6d2a03b1d6ae0ba5fc44574443d282093b24dfefaee9cc3f7bb50ae1ba9b51a1
```

Recovery artifacts are outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-recovery-20260623T124439Z/directus-createonly-identity-recovery-comparison.probe.json
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-recovery-20260623T124439Z/directus-createonly-identity-recovery-apply.json
/tmp/cap-migration-runs/20260622T110402Z/directus-createonly-identity-recovery-20260623T124439Z/directus-policy-graph-collection.status.json
```

Artifact SHA-256:

```text
directus-createonly-identity-recovery-comparison.probe.json:
1c8cfb27874458673d15e56b41583e0f4dda555c66a0bd606159eb163bc938de

directus-createonly-identity-recovery-apply.json:
3b4cc130f2426fb5c94a8c9b4e5eebf505b4d5f06822b3c23e6e8ebb7dd4e493

directus-policy-graph-collection.status.json:
ec6f7bf28e63e2169def7b61368d28d2539d02267de8c7adcbf2b6c67e476f33
```

The live policy graph collector was then run with the create-only token. It
failed closed at:

```text
GET /roles -> HTTP 403
```

No raw, normalized, or evaluation policy graph artifacts were created. This is
consistent with the denied-permission model for the execution identity, but it
means production readiness remains blocked until an approved operator/admin
redacted policy graph export or equivalent permission evidence is evaluated.
Do not broaden the execution identity just to make policy evidence collection
pass.

## Redacted admin/operator policy evidence

On 2026-06-23, the evidence task used the admin/schema token only for GET-only
policy graph export of the dedicated create-only identity. The create-only
token remained narrow and was not broadened.

Live requests performed:

- `GET /server/info`;
- `GET /roles?filter[name][_eq]=directus-createonly-content-migration`;
- `GET /roles/<role_id>`;
- `GET /policies?filter[roles][role][_eq]=<role_id>`;
- `GET /users?filter[email][_eq]=cap-migration@skunklabs.uk`;
- `GET /permissions?filter[policy][_eq]=<policy_id>`;
- `GET /permissions?filter[policy][id][_eq]=<policy_id>`.

No Directus mutation was performed.

The redacted export found exactly:

- one role named `directus-createonly-content-migration`;
- one policy named `directus-createonly-content-migration`;
- policy `admin_access = false`;
- policy `app_access = false`;
- one `feeds.read` permission;
- one draft-constrained `feeds.create` permission;
- no update, delete, share, wildcard, system, or permission-management
  permission in the policy graph.

The local normalizer and evaluator approved the redacted evidence:

```text
status: approved
```

Artifacts are outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.redacted.raw.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.normalized.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.evaluation.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.export-status.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/permission-evidence-create-only.json
```

Artifact SHA-256:

```text
directus-createonly-policy-graph.redacted.raw.json:
ded458fff8e011a7e94098ab8d432c0e273d10b053cd5c95d168f54ef6249035

directus-createonly-policy-graph.normalized.json:
38c29d010d7f139f5cf751d7c78d219143af3b99fb0991053bd96b80d269c935

directus-createonly-policy-graph.evaluation.json:
794246ab503bc950327c83b4b0336dbc3a474909c66db309309cee2996dcf43c

directus-createonly-policy-graph.export-status.json:
1fce3d58d39268c57636d3438c35357da4f1c6dadff50a1b2374a9f1b431feb6

permission-evidence-create-only.json:
7b7cbcc3878729b85430dea508c6e1c57744e56b0c251426ad917c1fae0ae9d6
```

`permission-evidence-create-only.json` is Gate 1 input only. Negative
permission results in that artifact are evidence-source marked as
`policy_graph`; no mutating negative probes were run. The next gate is fresh
target absence evidence before any production content `POST`.

### Redacted YAML structure

Read-only token:

```yaml
directus_readonly_content_migration:
  purpose: wordpress_to_directus_content_migration
  environment: bootstrap_validation
  base_url: https://cap-cms.skunklabs.uk
  directus_version: "11.13.2"
  user_identifier: directus-readonly-content-migration
  role_or_policy: directus-readonly-content-migration
  allowed_use:
    - read_target_baseline
    - read_fresh_target_absence
    - read_post_run_invariants
  forbidden_use:
    - content_create
    - content_update
    - content_delete
    - media_upload
    - schema_setup
    - permission_management
    - user_management
    - role_management
  token: "<redacted>"
```

Create-only token:

```yaml
directus_createonly_content_migration:
  purpose: wordpress_to_directus_content_migration
  environment: bootstrap_validation
  base_url: https://cap-cms.skunklabs.uk
  directus_version: "11.13.2"
  user_identifier: directus-createonly-content-migration
  role_or_policy: directus-createonly-content-migration
  allowed_use:
    - create_approved_draft_feeds_only
    - verify_own_created_drafts
  forbidden_use:
    - content_update
    - content_delete
    - media_upload_until_approved
    - schema_setup
    - permission_management
    - user_management
    - role_management
  token: "<redacted>"
```

## Operator procedure

Do this only after explicit approval to create Directus roles, users, tokens,
and permissions.

1. In Directus, create or verify the two dedicated roles/access policies:
   `directus-readonly-content-migration` and
   `directus-createonly-content-migration`.
2. Attach exactly the permissions defined above.
3. Create two dedicated non-admin users, one per identity.
4. Issue one static token per user.
5. On the operator machine, write plaintext YAML only under a private run
   directory outside Git, for example:
   `/tmp/cap-migration-runs/20260622-directus-identities/secrets/`.
6. Encrypt each plaintext file into the repository with SOPS, using the final
   repository filename as the filename override so `.sops.yaml` creation rules
   match.
7. Delete the plaintext token files from `/tmp` after encryption and local
   verification.
8. Commit only the encrypted SOPS files if and when the token creation itself
   has been explicitly approved.

Example encryption commands, shown with placeholder paths only:

```bash
set +x

sops --encrypt \
  --filename-override secrets/migration/directus-readonly-content-migration.20260622.sops.yaml \
  /tmp/cap-migration-runs/20260622-directus-identities/secrets/directus-readonly-content-migration.yaml \
  > secrets/migration/directus-readonly-content-migration.20260622.sops.yaml

sops --encrypt \
  --filename-override secrets/migration/directus-createonly-content-migration.20260622.sops.yaml \
  /tmp/cap-migration-runs/20260622-directus-identities/secrets/directus-createonly-content-migration.yaml \
  > secrets/migration/directus-createonly-content-migration.20260622.sops.yaml
```

Never print decrypted token values. Never paste tokens into chat, logs, shell
history, or committed docs.

## Gate artifact regeneration procedure

This procedure is for a future approved run after the two correct encrypted
identities exist. It must not use the schema-capable token.

Expected artifacts:

```text
permission-evidence-create-only.json
fresh-target-absence-before-create.json
```

### 1. Regenerate fresh target absence

Use `directus-readonly-content-migration` only.

Inputs:

- approved create manifest hash;
- approved migration approval hash;
- current target URL;
- current target baseline hash;
- exact `original_uri` set from the manifest.

The generated report must have:

- `kind = fresh_target_absence_before_create`;
- `status = approved`;
- `target_url = https://cap-cms.skunklabs.uk`;
- current `observed_at`;
- exact `manifest_sha256`;
- exact `approval_sha256`;
- `checked_operation_count = 35`;
- `checked_original_uris` equal to the manifest `original_uri` set;
- one `absence_evidence` entry per manifest `original_uri`;
- empty route, slug, protected, drift, ambiguous, and skipped lists;
- `stale_baseline = false`.

Any existing target match, route collision, slug collision, protected artifact,
drift match, ambiguity, skipped check, stale baseline, missing URI, extra URI,
or duplicate URI rejects the artifact.

### 2. Regenerate create-only permission evidence

Use `directus-createonly-content-migration` only.

The generated report must have:

- `kind = permission_evidence_create_only`;
- `status = approved`;
- `target_url = https://cap-cms.skunklabs.uk`;
- current `observed_at`;
- credential-free `execution_identity`;
- no `admin`, `system_wildcard`, `broad_token`, `role_admin`, or
  `permission_management` capability;
- the probe matrix listed in the create-only section above.

The report must not contain token, password, secret, or authorization header
values.

### 3. Validate locally without `--execute`

Run the existing test suite and compile check:

```bash
cd cms/utils/wordpress
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall .
```

Then run the gated dry-run without `--execute`:

```bash
cd cms/utils/wordpress

uv run python create_manifest_executor.py \
  --manifest /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-draft-only.json \
  --approval /home/iingenito/cap-migration-runs/20260622T110402Z/migration-approval.json \
  --permission-evidence /home/iingenito/cap-migration-runs/20260622T110402Z/permission-evidence-create-only.json \
  --fresh-target-absence /home/iingenito/cap-migration-runs/20260622T110402Z/fresh-target-absence-before-create.json \
  --output-dir /home/iingenito/cap-migration-runs/20260622T110402Z/executor-gated-dry-run
```

The dry-run must report zero sent requests. Do not run `--execute` until a
separate explicit production approval exists.

## Stop conditions

Stop immediately if:

- token creation requires an unapproved production Directus admin action;
- the only available Directus token is schema-capable, admin, or broader than
  the identity being tested;
- SOPS cannot decrypt metadata safely without printing secret values;
- a decrypted value appears in terminal output, logs, docs, or Git diff;
- the repo has unrelated dirty changes beyond known operator scratch files;
- any permission probe is inconclusive;
- any forbidden probe succeeds;
- the fresh target absence report finds an existing target, collision, drift,
  ambiguity, stale baseline, skipped check, missing URI, extra URI, or duplicate
  URI;
- documentation would imply production approval when only planning exists;
- a future step would require `POST`, `--execute`, media upload, import, schema
  apply, or permission mutation without explicit approval.

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
  - docs/migrations/wordpress-to-directus/task-b-pre-create-safety-gates.md
  - docs/migrations/wordpress-to-directus/task-b-live-pre-create-gate-artifacts.md
  - cms/utils/wordpress/pre_create_gates.py
  - cms/utils/wordpress/create_manifest_executor.py
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/inventory/__main__.py
  - cms/utils/wordpress/inventory/permission_gate.py
  - cms/utils/wordpress/tests/test_pre_create_gates.py
  - secrets/migration/
files_changed:
  - docs/migrations/wordpress-to-directus/task-b-directus-migration-identities.md
findings:
  - The content migration needs two dedicated Directus identities: read-only and create-only.
  - The existing schema-capable SOPS token is intentionally unusable for these gates.
  - The current approved create executor scope is draft feed creation only; media and folders remain out of scope.
verification:
  - Documentation-only design; run git diff checks and optional test suite before commit.
production_artifact_impact: none
risks:
  - The exact Directus UI implementation of draft-only create may need operator verification in Directus 11.13.2.
  - Gate artifact generation remains an operational step outside Git.
open_questions:
  - Will Directus 11.13.2 enforce `status = draft` at access-policy level for `feeds.create`, or must this remain executor-only?
next_action: After explicit approval, create the two dedicated Directus identities, store their tokens with SOPS, and regenerate the two live gate artifacts without using the schema token.
```

## Gallery-media identity discovery status

On 2026-06-27, the permission-management slice for a separate gallery-media
execution identity was checked with GET-only live discovery.

Planned identity:

```text
identity_name: directus-createonly-gallery-media-migration
service_email: cap-gallery-media-migration@skunklabs.uk
secret_path: secrets/migration/directus-createonly-gallery-media-migration.20260626.sops.yaml
```

Required capabilities:

```text
feeds.read
directus_folders.read
directus_folders.create
directus_files.read
directus_files.create
```

Fresh discovery using the schema/admin token found:

```text
classification: absent_safe_to_create
role_count: 0
policy_count: 0
user_count: 0
live_methods_used: GET only
apply_requested: false
apply_performed: false
```

No role, policy, permission, user, token, folder, file, feed, schema, or media
object was created. No existing `directus-createonly-content-migration` secret
or identity was modified.

Artifacts are outside Git:

```text
/home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-identity-20260627T055028Z/gallery-media-identity.discovery.json
sha256: 8c4158e37cdf1986d8c3179bf01d18626063e4e4eade0bb7f9217351f23c59c6

/home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-identity-20260627T055028Z/gallery-media-identity.blocked.json
sha256: e907e626c17f75605182aa3ef3d2f2c5f381661f9b53a7355c7f48673221024a
```

Production readiness remains blocked because the explicit apply gate was not
set. The next permission-management run may create this identity only after
`APPLY_DIRECTUS_GALLERY_MEDIA_IDENTITY=true` is intentionally present and fresh
GET-only comparison still classifies the state as safe.

## Gallery-media identity apply status

Later on 2026-06-27, the gallery-media permission-management slice was rerun
with:

```text
APPLY_DIRECTUS_GALLERY_MEDIA_IDENTITY=true
```

Fresh pre-apply discovery classified the state as:

```text
absent_safe_to_create
```

The apply created the dedicated gallery-media role, policy, five permission
rows, and service user with only these endpoint families:

```text
POST /roles
POST /policies
POST /permissions
POST /users
```

No `PATCH`, `PUT`, or `DELETE` was performed. No content, media, feed, gallery,
schema, folder-content, file upload, relation, or frontend object was changed.

Post-apply discovery classified the live state as:

```text
existing_matches_expected
```

The identity has the intended permission rows:

```text
feeds.read
directus_folders.read
directus_folders.create
directus_files.read
directus_files.create
```

However, the run is not production-ready. The static token could not be
validated: GET probes with the gallery-media token returned HTTP 401 for every
probe, including `/server/info`. The invalid SOPS secret was removed and no
gallery-media secret is committed.

Artifacts:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-identity-20260627T060034Z
gallery-media-identity.pre-apply-discovery.json: fd09ce7acc8ead6b03fc8f5ce306a5b1ad2644ae4f849014e1caa473c3d05d77
gallery-media-identity.apply.json: 9186fe6c7bbf3625a3d246409bff05ab771faf003dc897a17af20709afdb5688
gallery-media-identity.post-apply-discovery.json: 4f011bc3e44085786f3261f70da80ed9dc8239792ce30a3976dc79767c5f4fef
gallery-media-token-get-probes.json: 6655a6c2b5bda21559c91dd48d330beca36eb84ad32a74a5db210e5f550eda59
gallery-media-identity.final-blocked.json: 188e935adaf7d640613c464359f46e744848fcd880bdb98f87f3069b9ef6ddf5
```

Next action: resolve static token generation for the existing
`cap-gallery-media-migration@skunklabs.uk` service user through an approved
Directus token regeneration/update path, then write the encrypted SOPS secret
and rerun token probes plus policy evidence.
