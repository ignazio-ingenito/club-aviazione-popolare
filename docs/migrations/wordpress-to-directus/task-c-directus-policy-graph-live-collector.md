# Task C - Directus policy graph live collector scaffold

Status: implemented as mocked GET-only scaffold; live GET adapter
investigations performed; redacted admin evidence approved

Date: 2026-06-22

## Scope

This slice adds a Directus policy graph collector scaffold that can produce the
conservative raw shape accepted by the local normalizer.

Implemented:

- `cms/utils/wordpress/directus_policy_collector.py`;
- `collect_directus_policy_graph_raw(...)`;
- `directus_policy_evidence.py --collect-live`;
- mocked HTTP unit tests for the collector and CLI mode;
- Directus 11.13 policy-role filter adapter for the live `/policies` shape.

Not implemented or not performed:

- approved live policy graph evidence collection against
  `https://cap-cms.skunklabs.uk`;
- Directus role, policy, user, token, schema, content, or media changes;
- production `POST`, `PATCH`, `PUT`, or `DELETE`;
- migration execution with `--execute`;
- storage of live raw artifacts in Git.

## Collector Contract

The public function is:

```python
collect_directus_policy_graph_raw(
    *,
    directus_url: str,
    role_id: str,
    auth_token: str,
    http: httpx.Client | None = None,
) -> dict[str, Any]
```

It performs only these GET requests:

- `GET /server/info`;
- `GET /roles/<role_id>`;
- `GET /policies?filter[roles][role][_eq]=<role_id>`;
- `GET /permissions?...`.

The function returns raw JSON with:

- `target_url`;
- `observed_at`;
- `directus_version`;
- `identity`;
- `roles`;
- `policies`;
- `permissions`.

The returned shape is intended to be passed directly to:

```python
normalize_directus_policy_graph_payload(raw)
evaluate_policy_graph_evidence(normalized)
```

The collector fails closed when:

- `directus_url` is not an absolute `http` or `https` URL;
- `role_id` is empty;
- `auth_token` is empty;
- the role response is missing or mismatched;
- policies are missing or not attached to the requested role;
- permissions are missing;
- policy or permission linkage is malformed;
- required fields are absent or ambiguous.

## Live Directus 11.13 adapter finding

On 2026-06-22, a GET-only investigation of the previous
`policies GET failed with status 400` failure confirmed that the original
collector query:

```text
GET /policies?filter[roles][_contains]=<role_id>
```

is incompatible with the live Directus 11.13.2 API. Directus returned
`INVALID_QUERY` because `_contains` is not valid for the UUID field reached by
that relation filter.

The accepted GET-only query shape is:

```text
GET /policies?filter[roles][role][_eq]=<role_id>
```

The collector now uses that relation traversal and includes mocked tests for:

- the exact Directus 11.13 filter shape;
- Directus access-link rows where policy `roles` contain objects with a
  `role` field.

No Directus roles, policies, permissions, users, tokens, schema, content, media,
feeds, or galleries were changed during the investigation.

After this adapter change, the live collector progressed past `/policies` and
then stopped fail-closed with:

```text
permissions response is empty
```

No raw, normalized, or evaluation evidence artifact was created by that live
collection attempt. The production identity is therefore still not proven safe
for create execution.

## Live permissions lookup finding

On 2026-06-22, a GET-only investigation of the subsequent
`permissions response is empty` failure checked the live Directus 11.13.2
permission lookup shape without printing tokens, headers, role IDs, policy IDs,
or full permission payloads.

The collector query at the time was:

```text
GET /permissions?filter[policy][_in]=<policy_id>
```

The investigation found:

- `/permissions` is readable by the token and returns permission rows;
- the selected role has one attached policy;
- the selected policy relation reports zero `permissions` rows;
- `GET /permissions?filter[policy][_eq]=<policy_id>` also returns zero rows;
- `GET /permissions?filter[policy][id][_eq]=<policy_id>` returns zero rows;
- indexed and bracket-array `_in` variants return zero rows;
- a JSON-string `_in` variant is not accepted safely by Directus and was not
  used further.

Therefore the live failure is not currently proven to be a collector adapter
mismatch. The selected role's attached policy has no readable permission rows to
collect. The collector correctly fails closed rather than accepting missing
permission evidence.

No Directus roles, policies, permissions, users, tokens, schema, content, media,
feeds, or galleries were changed during this investigation.

No raw, normalized, or evaluation policy graph evidence artifact was created.
The production identity is still not proven safe for create execution. The next
safe path is to provide a Directus migration identity or an operator-generated,
redacted policy export with complete permission rows, then rerun evidence
collection without enabling production `POST`.

## Live role identity finding

On 2026-06-23, a GET-only identity verification checked the
`DIRECTUS_ROLE_ID` currently stored in:

```text
secrets/migration/directus-schema-token.20260622.sops.yaml
```

Only SOPS key names were printed. Secret values, headers, role IDs, and policy
IDs were not written to Git or included in documentation.

The sanitized live evidence showed:

- the configured role is named `Administrator`;
- the attached policy is named `Administrator`;
- the selected policy reports `admin_access = true` and `app_access = true`;
- the selected policy still reports zero permission rows;
- `/permissions?limit=1` is readable and returns permission rows globally;
- candidate permission filters for the selected policy return zero rows.

This classifies the stored role id as `wrong_role_id` for the
WordPress-to-Directus content migration. The documented target identity remains
`directus-createonly-content-migration`, now stored in a distinct encrypted secret:

```text
secrets/migration/directus-createonly-content-migration.20260622.sops.yaml
```

No Directus roles, policies, permissions, users, tokens, schema, content, media,
feeds, or galleries were changed during the verification. Production readiness
remains blocked until a dedicated create-only migration identity or an
operator-generated redacted policy export with complete permission rows is
provided and evaluated.

## Create-only identity setup dry-run

On 2026-06-23, a permission-management dry-run prepared the intended
`directus-createonly-content-migration` role/policy/user plan and performed
GET-only discovery before any apply.

The dry-run found:

- no existing role named `directus-createonly-content-migration`;
- no existing policy named `directus-createonly-content-migration`;
- no existing user matching the planned service email;
- `/permissions?limit=1` remains readable to the admin/schema credential.

No Directus mutation was performed. No create-only encrypted secret was created.
No live policy graph evidence was collected for the intended identity because
the identity does not yet exist and no execution credential exists.

Production readiness remains blocked. The next safe step is to rerun the
permission-management task with explicit apply approval, create the dedicated
identity, encrypt its credential with SOPS, and then run the GET-only policy
graph collector using the new create-only credential.

## Create-only identity partial apply

On 2026-06-23, the permission-management task was rerun with
`APPLY_DIRECTUS_CREATEONLY_IDENTITY=true`.

The apply created permission-management resources for the intended
`directus-createonly-content-migration` identity, but stopped before producing a
usable execution credential:

- dedicated role created;
- dedicated policy created with `admin_access = false` and `app_access = false`;
- `feeds.read` permission created;
- draft-constrained `feeds.create` permission created;
- service user/static token creation failed with HTTP 400 because Directus
  rejected the placeholder service email.

No raw, normalized, or evaluation policy graph artifacts were created because
there is still no create-only token. The create-only SOPS secret does not
exist. Production readiness remains blocked.

The next collector run must use only the final
`directus-createonly-content-migration` token, not the admin/schema token. If
the execution token intentionally cannot read roles, policies, or permissions,
the policy graph evidence must be produced by a separately approved
operator/admin read of the effective graph and then evaluated without
broadening the execution identity.

## Create-only identity recovery attempt

On 2026-06-23, the recovery task proved with GET-only comparison that the
partial migration-owned role, policy, and permission rows match the approved
narrow plan. It then attempted only `POST /users` to create the missing
service user/static token.

Directus rejected both planned service emails as invalid:

```text
directus-createonly-content-migration@cap-migration.local
directus-createonly-content-migration@example.invalid
```

No create-only token exists yet, so the live policy graph collector was not run
with the final execution identity. No raw, normalized, or evaluation artifacts
exist for the create-only identity. Production readiness remains blocked.

## Create-only token collector attempt

On 2026-06-23, the recovery task was rerun with the valid service email:

```text
cap-migration@skunklabs.uk
```

After fresh GET-only comparison again classified the partial state as
`partial_state_matches_expected`, recovery created the dedicated service user
and static token with only:

```text
POST /users
```

The create-only credential was stored in:

```text
secrets/migration/directus-createonly-content-migration.20260622.sops.yaml
```

The collector was then run with the create-only token, not the admin/schema
token. It failed closed before artifact generation:

```text
GET /roles -> HTTP 403
```

No raw, normalized, or evaluation policy graph artifacts were created. This is
consistent with the execution identity being denied roles, policies, and
permissions access, but it means the collector cannot prove the effective
policy graph using that token alone.

Production readiness remains blocked. The next safe evidence path is a
separately approved operator/admin redacted policy graph export or equivalent
permission proof for the dedicated create-only identity. Do not broaden the
execution identity just to make the collector pass.

## Redacted admin/operator evidence approval

On 2026-06-23, a GET-only admin/operator export collected redacted policy graph
evidence for `directus-createonly-content-migration`. This was intentionally
separate from the create-only token, which remains unable to read `/roles`,
`/policies`, and `/permissions`.

The export used only these live GET request families:

- `/server/info`;
- `/roles`;
- `/policies`;
- `/users`;
- `/permissions`.

No `POST`, `PATCH`, `PUT`, or `DELETE` was performed. No Directus role, policy,
permission, user, token, schema, content, media, feed, gallery, folder, or
relation was changed.

The redacted raw artifact was adapted to the existing conservative raw shape
accepted by `normalize_directus_policy_graph_payload`. The existing local
normalizer/evaluator produced:

```json
{"status": "approved"}
```

Evidence artifacts are outside Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.redacted.raw.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.normalized.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.evaluation.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/directus-createonly-policy-graph.export-status.json
/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/permission-evidence-create-only.json
```

Hashes:

```text
directus-createonly-policy-graph.redacted.raw.json: ded458fff8e011a7e94098ab8d432c0e273d10b053cd5c95d168f54ef6249035
directus-createonly-policy-graph.normalized.json: 38c29d010d7f139f5cf751d7c78d219143af3b99fb0991053bd96b80d269c935
directus-createonly-policy-graph.evaluation.json: 794246ab503bc950327c83b4b0336dbc3a474909c66db309309cee2996dcf43c
directus-createonly-policy-graph.export-status.json: 1fce3d58d39268c57636d3438c35357da4f1c6dadff50a1b2374a9f1b431feb6
permission-evidence-create-only.json: 7b7cbcc3878729b85430dea508c6e1c57744e56b0c251426ad917c1fae0ae9d6
```

This satisfies the permission evidence gate only. The next gate is fresh target
absence validation before any production content creation.

## Token Handling

The token is accepted only as a function argument or through `DIRECTUS_TOKEN` in
CLI mode.

The collector:

- adds `Authorization: Bearer <token>` to HTTP requests;
- does not include headers in returned raw output;
- does not write the token to raw, normalized, or evaluation artifacts;
- does not print the token.

Unit tests assert that the token is present in mocked request headers but absent
from JSON outputs and CLI stdout.

## CLI

The live collector mode is explicit:

```bash
cd cms/utils/wordpress

DIRECTUS_TOKEN=... uv run python directus_policy_evidence.py \
  --collect-live \
  --directus-url https://cap-cms.skunklabs.uk \
  --role-id <role-id> \
  --raw-output /tmp/directus-policy-graph.raw.json \
  --normalized-output /tmp/directus-policy-graph.normalized.json \
  --evaluation-output /tmp/directus-policy-graph.evaluation.json
```

CLI behavior:

- if `--collect-live` is omitted, no network collection path runs;
- if `DIRECTUS_TOKEN` is missing, exit `1`;
- existing output files are refused unless `--force` is set;
- collect-live outputs inside the Git repository are refused;
- exit `0` when normalized evidence is approved;
- exit `2` when normalized evidence is rejected;
- exit `1` for malformed input, I/O, network, or configuration errors.

## Verification

Run from `cms/utils/wordpress`:

```bash
uv run python -m unittest tests/test_directus_policy_collector.py -v
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall .
```

Repository-level checks:

```bash
git diff --check
git diff --cached --check
```

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
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-plan.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-evaluator.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-normalizer.md
  - docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json
  - cms/utils/wordpress/directus_policy_evidence.py
  - cms/utils/wordpress/tests/test_directus_policy_evidence.py
  - cms/utils/wordpress/tests/test_directus_policy_normalization.py
  - cms/utils/wordpress/directus_create_only.py
files_changed:
  - cms/utils/wordpress/directus_policy_collector.py
  - cms/utils/wordpress/directus_policy_evidence.py
  - cms/utils/wordpress/tests/test_directus_policy_collector.py
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-live-collector.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-normalizer.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-plan.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
findings:
  - The collector scaffold is GET-only and mock-tested.
  - The CLI refuses collect-live outputs inside the repository.
  - The token is required for collect-live mode but is not serialized.
verification:
  - Run the command block in the Verification section.
production_artifact_impact: none
risks:
  - Actual Directus 11.13.2 policy response shapes may require a follow-up adapter refinement after explicit live read-only collection approval.
  - This scaffold does not prove the production identity is create-only until live evidence is collected outside Git and evaluated.
open_questions:
  - None for the mocked scaffold slice.
next_action: After operator approval, run collect-live outside Git and review the normalized/evaluation artifacts before any production write gate.
```
