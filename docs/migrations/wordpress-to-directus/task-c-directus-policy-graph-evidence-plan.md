# Task C - Directus policy graph evidence plan

Status: credential-free evidence plan only; not applied

Date: 2026-06-22

## Scope

This slice defines the evidence needed to prove that the future
`directus-createonly-content-migration` identity is effectively create-only for
draft `feeds` records.

It does not authorize or perform:

- Directus role creation;
- Directus access-policy creation;
- Directus permission creation;
- Directus user creation;
- token creation;
- schema changes;
- content import;
- media upload;
- production `POST`;
- migration execution with `--execute`;
- live credential collection into Git.

The companion static example is:

```text
docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json
```

That JSON is synthetic. It is not a production Directus export and must not be
treated as live permission evidence.

## Required evidence

Future live evidence must describe the whole effective access path for the
planned create-only identity, not only the intended permission object.

The sanitized evidence artifact must include:

- Directus base URL fingerprint, environment label, Directus version, collection
  timestamp, and collection command version;
- subject identity name, expected purpose, and a redacted stable user
  fingerprint;
- every role, access policy, or equivalent Directus policy source attached to
  the subject, directly or through role membership;
- every permission object contributed by those roles or policies for:
  - `feeds`;
  - `categories`;
  - `directus_files`;
  - `directus_folders`;
  - Directus schema resources;
  - Directus settings resources;
  - Directus users, roles, permissions, policies, access, flows, automations,
    and admin/app capabilities;
- all `feeds.create` permission objects after normalization, including
  collection, action, fields, validation, presets, permissions filter, policy
  source, and whether each object is exact, narrower, broader, or ambiguous
  against the plan;
- effective permission summary after additive composition;
- forbidden-access summary for every denied action required by the Task B plan;
- proof that the evidence token is not the schema-capable migration token,
  represented as a non-secret secret-name hint or stable credential
  fingerprint;
- redaction report listing every field removed or hashed.

The planned `feeds.create` contract remains:

```json
{
  "collection": "feeds",
  "action": "create",
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

Executor-side `status = draft` enforcement remains mandatory. Directus
permissions are a defense layer, not the source of business logic.

## Safe command shape

The future command should be implemented as a local script with two modes:

```text
cms/utils/wordpress/directus_policy_graph_evidence.py render-example
cms/utils/wordpress/directus_policy_graph_evidence.py collect-live
```

`render-example` must:

- use no credentials;
- make no network requests;
- write only a synthetic JSON example;
- be safe to run in CI.

`collect-live` must:

- require explicit operator approval before use;
- read `DIRECTUS_URL`, `DIRECTUS_TOKEN`, `EXPECTED_DIRECTUS_IDENTITY`, and
  `OUTPUT_DIR` from the environment;
- never print `DIRECTUS_TOKEN`;
- write raw live artifacts only outside Git;
- write a sanitized report only after redaction checks pass;
- use GET-only Directus inspection calls for the policy graph;
- perform no `POST`, `PATCH`, `PUT`, or `DELETE`.

If Directus 11.13.2 cannot expose the complete policy graph to the create-only
identity without granting broader management access, the safe collection model
must split evidence into two inputs:

- an operator-generated, redacted policy graph export collected with an
  administrative identity and stored outside Git;
- a create-only identity probe artifact proving the runtime token cannot access
  forbidden actions.

The two inputs must agree on the redacted subject fingerprint. If they do not
agree, the result is rejected.

## Expected sanitized output format

The sanitized artifact must be JSON with this top-level shape:

```text
kind
status
collected_at
target
subject
policy_graph
feeds_create_analysis
effective_access
forbidden_access
redaction
failure_conditions
approval_gate
```

`status` must be one of:

- `accepted_static_example`;
- `accepted_live_evidence`;
- `rejected`.

Only `accepted_live_evidence` can satisfy a future production gate. Static
examples are documentation aids only.

The output must not contain:

- bearer tokens;
- static tokens;
- passwords;
- cookies;
- authorization headers;
- session identifiers;
- raw secret file contents;
- unredacted personal email addresses.

## Additive-policy proof

Directus policy behavior is additive. Therefore the validator must prove that no
additional policy broadens `feeds.create`.

The future validator must:

1. Enumerate every policy source attached to the subject.
2. Normalize every permission into a comparable structure:
   `collection`, `action`, `fields`, `permissions`, `validation`, `presets`,
   and `policy_source`.
3. Select every permission where `collection = feeds` and `action = create`.
4. Reject if any selected permission uses collection wildcard, action wildcard,
   field wildcard, empty fields with wildcard semantics, admin bypass, or an
   unknown Directus permission shape.
5. Reject if any selected permission has no `validation.status._eq = draft`.
6. Reject if any selected permission has no `presets.status = draft`.
7. Reject if the union of all effective create fields is not exactly the planned
   allowlist or a strict subset approved by the operator for the same run.
8. Reject if any selected permission allows non-draft status through another
   validation branch, missing validation branch, or ambiguous logical operator.
9. Reject if any policy grants `feeds.update`, `feeds.delete`, `feeds.share`, or
   create/update/delete on categories, files, folders, relations, schema,
   settings, users, roles, permissions, policies, flows, automations, or admin
   resources.
10. Reject if the policy graph is incomplete, inaccessible, stale, or collected
    for a different subject.

Only an exact or narrower `feeds.create` grant with draft validation and draft
preset is acceptable.

## Redaction rules

The collector must redact before writing any artifact intended for review or
commit.

Required redactions:

- replace tokens, cookies, authorization headers, passwords, and secret values
  with `REDACTED`;
- hash user IDs, role IDs, policy IDs, and credential fingerprints with a
  per-run salt stored only outside Git;
- replace email addresses with stable labels such as
  `directus-createonly-content-migration@example.invalid`;
- keep non-secret role and policy names only when they are needed to review the
  permission graph;
- fail if the sanitized output still matches common token or authorization
  patterns.

Raw live exports must remain outside Git in the approved run directory.

## Failure conditions

The evidence is rejected if:

- any required policy graph input is missing;
- the Directus version differs from the reviewed version and the permission
  shape has not been re-reviewed;
- the subject identity name or fingerprint does not match the expected
  `directus-createonly-content-migration` identity;
- the collector needs production `POST`, `PATCH`, `PUT`, or `DELETE`;
- the create-only identity has or inherits update/delete/share access;
- any policy grants broader `feeds.create` than the planned field allowlist;
- `feeds.create.validation.status._eq = draft` is absent or ambiguous;
- `feeds.create.presets.status = draft` is absent or ambiguous;
- system resources are readable or writable when the Task B plan says they must
  be denied;
- the evidence token appears to be the schema-capable token;
- a secret value appears in stdout, stderr, or the sanitized JSON;
- operator export and create-only probe artifacts do not refer to the same
  redacted subject;
- the graph is ambiguous or cannot be normalized deterministically.

## Approval gate before live use

Before `collect-live` can be run, an operator must explicitly approve:

- the exact repository commit containing the collector;
- the Directus environment and URL;
- the expected identity name;
- the run directory outside Git;
- whether an administrative policy export is needed because the create-only
  identity cannot read its own full policy graph;
- the redaction command and secret-pattern check;
- the fact that this evidence collection is read-only and performs no
  production `POST`.

This approval does not authorize role creation, permission changes, schema
changes, content import, media upload, or migration execution.

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-directus-permission-implementation-plan.md
  - docs/migrations/wordpress-to-directus/directus-content-migration-permission-plan.example.json
files_changed:
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-plan.md
  - docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
findings:
  - Future evidence must inspect the complete additive policy graph for the create-only migration identity.
  - A GET-only policy-graph collector may need an operator export plus create-only probe artifact if Directus hides policy internals from the migration identity.
  - Static examples are not acceptable live evidence.
verification:
  - Run json.tool on the static JSON example.
  - Run git diff --check before staging.
  - Run git diff --cached --check after staging.
production_artifact_impact: none
risks:
  - The exact Directus 11.13.2 policy API/UI export shape still requires live operator evidence.
  - A future collector must fail closed if Directus policy graph data is incomplete.
open_questions:
  - None for this documentation slice.
next_action: Implement or run the credential-free render-example path only, then request explicit approval before any live policy-graph collection.
```
