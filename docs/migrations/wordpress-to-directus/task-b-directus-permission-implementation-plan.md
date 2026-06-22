# Task B slice 9.9 - Directus permission implementation plan

Status: implementation plan only; not applied

Date: 2026-06-22

## Scope

This slice turns the Directus migration identity design into a concrete
permission implementation plan for Directus 11.13.2.

It does not authorize or perform:

- Directus role creation;
- Directus access-policy creation;
- Directus permission creation;
- Directus user creation;
- token creation;
- schema changes;
- production `POST`;
- `--execute`;
- content import;
- media upload;
- committing secrets or live run artifacts.

The companion static example is:

```text
docs/migrations/wordpress-to-directus/directus-content-migration-permission-plan.example.json
```

That JSON is a non-secret, non-applied plan artifact. It is not an export from
production Directus and must not be treated as proof that permissions exist.

## Required conclusion

Directus supports permission-level field validation and field presets for
create/update actions. Therefore the create-only `feeds.create` plan must set
both:

- `validation.status == draft`;
- `presets.status = draft`.

This remains insufficient by itself because Directus policy behavior is
additive. Another role/access policy attached to the same user can broaden
effective access. Future live evidence must verify the whole effective policy
graph, not only the single planned `feeds.create` permission.

The executor must also continue enforcing `status = draft`, even when Directus
validation and presets are configured. Directus permissions are a defense layer,
not a replacement for executor-side manifest and request-plan validation.

## Field contract

The current approved draft-only executor builds `POST /items/feeds` payloads
with these fields:

```text
status
slug
title
content
description
date
original_uri
gallery
```

These field names are corroborated by:

- `CONTEXT.md` feed field list;
- `cms/utils/wordpress/create_manifest_executor.py`;
- `cms/utils/wordpress/inventory/directus.py` `FEED_FIELDS`.

If a future live schema inventory shows different field names, stop. Do not
guess aliases or broaden the field allowlist to make the plan apply.

## Read-only content migration identity

### Purpose

Use `directus-readonly-content-migration` for:

- target baseline;
- fresh target absence;
- route collision checks;
- post-run invariant checks.

### Planned allowed permissions

Grant only the read permissions required by the approved inventory and baseline
checks.

| Collection/resource | Action | Fields |
| --- | --- | --- |
| `feeds` | `read` | `id`, `status`, `slug`, `title`, `date`, `original_uri`, `gallery`, `category`, `cover` |
| `categories` | `read` | `key`, `title`, `description`, `status`, `sort`, `date_created`, `date_updated` |
| `directus_files` | `read` | `id`, `filename_disk`, `filename_download`, `title`, `type`, `filesize`, `folder`, `uploaded_on`, `modified_on` |
| `directus_folders` | `read` | `id`, `name`, `parent` |
| `directus_collections` | `read` | only if required by the approved inventory command |
| `directus_fields` | `read` | only if required by the approved inventory command |
| `directus_relations` | `read` | only if required by the approved inventory command |
| `server/info` | `read` | only if required to record Directus version/runtime metadata |

If Directus cannot expose schema metadata read-only without broader access,
record that as a blocked metadata gap. Do not add create, update, delete, admin,
or permission-management capabilities.

### Planned denied permissions

The read-only identity must deny:

- create on all application collections;
- update on all application collections;
- delete on all application collections;
- share on all application collections;
- schema mutation;
- settings access;
- users access;
- roles access;
- permissions access;
- policies access;
- flows access;
- automations access;
- App/Admin access;
- wildcard/system capabilities.

## Create-only content migration identity

### Purpose

Use `directus-createonly-content-migration` only for future approved draft feed
creation after all runbook gates pass.

Current stage scope:

- read minimal target data needed to verify the created item;
- create `feeds` only;
- no media upload;
- no folder creation;
- no category creation;
- no relation mutation;
- no ledger write until a separate ledger schema and permission plan is
  approved.

### Planned `feeds.read` permission

Use this minimal read permission for post-create verification and collision
checks:

```json
{
  "collection": "feeds",
  "action": "read",
  "permissions": {},
  "validation": {},
  "presets": null,
  "fields": [
    "id",
    "status",
    "slug",
    "title",
    "date",
    "original_uri",
    "gallery"
  ]
}
```

### Planned `feeds.create` permission

The create permission must be limited to the executor payload fields and must
force draft status at the Directus permission layer:

```json
{
  "collection": "feeds",
  "action": "create",
  "permissions": {},
  "validation": {
    "status": {
      "_eq": "draft"
    }
  },
  "presets": {
    "status": "draft"
  },
  "fields": [
    "status",
    "slug",
    "title",
    "content",
    "description",
    "date",
    "original_uri",
    "gallery"
  ]
}
```

The executor must still enforce:

- every manifest operation has `target_status = draft`;
- every request-plan payload has `status = draft`;
- every request method is `POST`;
- every request endpoint is `/items/feeds`;
- `PATCH`, `PUT`, and `DELETE` are rejected before transport use.

### Planned denied permissions

The create-only identity must deny:

- `feeds.update`;
- `feeds.delete`;
- `feeds.share`;
- `categories.create`;
- `categories.update`;
- `categories.delete`;
- `directus_files.create`;
- `directus_files.update`;
- `directus_files.delete`;
- `directus_folders.create`;
- `directus_folders.update`;
- `directus_folders.delete`;
- relation create/update/delete;
- schema access and schema mutation;
- settings access;
- users access;
- roles access;
- permissions access;
- policies access;
- flows access;
- automations access;
- App/Admin access;
- wildcard/system capabilities.

## Future live verification gate

Before any approved staging or production execution, generate fresh permission
evidence using the actual `directus-createonly-content-migration` token.

The live permission evidence must prove:

- the create-only identity has exactly the expected `feeds.create` permission;
- `feeds.create.validation.status._eq == draft`;
- `feeds.create.presets.status == draft`;
- `feeds.create.fields` equals the planned allowlist;
- no additional policy broadens create access beyond the planned field list;
- no additional policy grants non-draft create;
- no update/delete/share access exists for `feeds`;
- no create/update/delete access exists for categories, files, folders, or
  relations in this stage;
- no schema/settings/users/roles/permissions/policies access exists;
- no flows or automations access exists;
- no App/Admin access exists;
- token is not `secrets/migration/directus-schema-token.20260622.sops.yaml`;
- token metadata/purpose matches WordPress-to-Directus content migration only;
- the policy graph is unambiguous.

The existing pre-create probe matrix still applies:

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

Any successful forbidden probe, inconclusive probe, ambiguous policy graph, or
unexpected broad permission fails closed.

## Operator implementation sequence

This is the future operator sequence after explicit approval. It is not
approved by this document.

1. Confirm the repository commit containing this plan.
2. Confirm Directus version is still `11.13.2`, or re-review the permission
   payload shape before continuing.
3. In Directus, create or verify dedicated roles/access policies for:
   `directus-readonly-content-migration` and
   `directus-createonly-content-migration`.
4. Attach only the planned permissions above.
5. Create dedicated non-admin users for those policies.
6. Issue one static token per user.
7. Store tokens only as SOPS-encrypted secrets following
   `task-b-directus-migration-identities.md`.
8. Generate fresh live permission evidence outside Git.
9. Generate fresh target absence outside Git using the read-only identity.
10. Run the local validators and dry-run without `--execute`.
11. Stop before staging or production execution until a separate explicit
    approval is recorded.

## Stop conditions

Stop immediately if:

- existing schema field names differ from this plan;
- Directus permission UI/API shape differs from the planned JSON and cannot be
  mapped safely;
- policy composition cannot be reasoned about from live evidence;
- another policy grants broader access to either migration user;
- `validation.status == draft` or `presets.status = draft` cannot be verified;
- any create/update/delete access exists outside the planned scope;
- any production mutation is required to complete this planning slice;
- any secret value would need to be printed;
- any live run artifact would need to be committed;
- the only available token is schema-capable or admin.

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
  - docs/migrations/wordpress-to-directus/task-b-pre-create-safety-gates.md
  - docs/migrations/wordpress-to-directus/task-b-live-pre-create-gate-artifacts.md
  - docs/migrations/wordpress-to-directus/task-b-directus-migration-identities.md
  - cms/utils/wordpress/pre_create_gates.py
  - cms/utils/wordpress/create_manifest_executor.py
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/inventory/directus.py
files_changed:
  - docs/migrations/wordpress-to-directus/task-b-directus-permission-implementation-plan.md
  - docs/migrations/wordpress-to-directus/directus-content-migration-permission-plan.example.json
findings:
  - Directus permission-level validation and presets should enforce draft-only creates as a second safety layer.
  - Directus policy behavior is additive, so future evidence must inspect the whole effective policy graph.
  - Executor-side draft enforcement remains mandatory and already exists in the create-manifest executor.
verification:
  - Documentation and static JSON plan only; run git diff checks and optional test suite before commit.
production_artifact_impact: none
risks:
  - The exact live policy graph still requires Directus admin/operator evidence outside Git.
  - The current pre-create gate validator checks probe outcomes, not the detailed Directus permission object shape.
open_questions:
  - Which future command or script will generate credential-free policy graph evidence for the detailed `feeds.create` permission object?
next_action: After explicit approval, create the two Directus migration identities, store tokens with SOPS, and regenerate live gate evidence without using the schema token.
```
