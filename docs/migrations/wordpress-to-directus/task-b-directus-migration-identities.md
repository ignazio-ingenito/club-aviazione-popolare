# Task B slice 9.8 - Directus migration identities and SOPS plan

Status: design/scaffold only; no production action performed

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
