# Task C - Directus policy graph live collector scaffold

Status: implemented as mocked GET-only scaffold; live GET adapter investigation
performed; live policy evidence still not collected

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
