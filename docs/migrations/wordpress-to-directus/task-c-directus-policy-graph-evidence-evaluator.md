# Task C - Directus policy graph evidence evaluator

Status: implemented; local evaluator plus synthetic raw normalizer only

Date: 2026-06-22

## Scope

This slice implements a pure local evaluator for sanitized Directus policy graph
evidence and a strict local normalizer for conservative raw policy graph
payloads.

Implemented:

- `cms/utils/wordpress/directus_policy_evidence.py`;
- `evaluate_policy_graph_evidence(payload)`;
- `normalize_directus_policy_graph_payload(raw)`;
- a no-network CLI for evaluating an existing JSON file;
- a no-network CLI mode for normalizing a raw JSON file and immediately
  evaluating the normalized output;
- synthetic unit tests for approved and rejected policy graphs;
- synthetic unit tests for strict normalizer failures and unsafe-but-valid
  normalized evidence;
- static-example compatibility for
  `docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json`.

Not implemented:

- live Directus collection;
- actual live Directus API response collection;
- Directus role, policy, user, token, schema, content, or media changes;
- production `POST`;
- migration execution with `--execute`.

## Evaluator contract

The public function is:

```python
evaluate_policy_graph_evidence(payload: Mapping[str, Any]) -> dict[str, Any]
```

It returns:

```json
{
  "kind": "directus_policy_graph_evidence_evaluation",
  "status": "approved",
  "reasons": [],
  "checks": {}
}
```

Rejected evidence returns `status = rejected` and stable reason strings instead
of raising for normal unsafe input.

## CLI

Evaluator mode:

```bash
cd cms/utils/wordpress

uv run python directus_policy_evidence.py \
  --input ../../../docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json \
  --output /tmp/directus-policy-graph-evidence-evaluation.json \
  --force
```

Raw normalization plus evaluation mode:

```bash
cd cms/utils/wordpress

uv run python directus_policy_evidence.py \
  --raw-input /path/to/raw-directus-policy-graph.json \
  --normalized-output /tmp/directus-policy-graph-evidence.normalized.json \
  --evaluation-output /tmp/directus-policy-graph-evidence-evaluation.json \
  --force
```

Exit codes:

- `0`: approved;
- `2`: rejected;
- `1`: malformed input, I/O failure, or overwrite refusal.

The CLI refuses to overwrite an existing output file unless `--force` is
provided.

## Normalizer contract

The public function is:

```python
normalize_directus_policy_graph_payload(raw: Mapping[str, Any]) -> dict[str, Any]
```

The normalizer supports only the conservative synthetic raw shape with:

- `target_url`;
- `observed_at`;
- optional `directus_version`;
- `identity.label` and `identity.role`;
- `roles[]` with `id` and/or `name`;
- `policies[]` with `id`, optional `name`, and `roles[]`;
- `permissions[]` with `policy`, `collection`, `action`, `permissions`,
  `validation`, `presets`, and `fields`.

It raises `DirectusPolicyEvidenceError` for malformed or ambiguous raw input,
including missing target URL, missing observation timestamp, missing identity,
missing or unknown role, policy not attached to the selected identity role,
permission references to unknown or unattached policies, malformed fields,
malformed validation, malformed presets, and multiple identity roles without an
explicit selected `identity.role`.

Wildcard collection/action and forbidden update/delete permissions are
structurally valid raw input. They survive normalization and are rejected by the
evaluator.

## Approval criteria

The evaluator approves only if:

- the payload kind is recognized;
- target URL, observed timestamp, identity, policies, and permissions are
  present;
- exactly one mutation permission exists;
- that mutation permission is `feeds.create`;
- `feeds.create.validation.status._eq = draft`;
- `feeds.create.presets.status = draft`;
- `feeds.create.fields` is present and is a subset of the approved allowlist;
- optional read access is limited to `feeds.read`;
- no update/delete/share permission exists;
- no wildcard collection or action exists;
- no schema/settings/users/roles/permissions/policies/system access exists;
- no file or folder access exists in this stage;
- no policy graph broadening or ambiguity is represented.

## Stable rejection reasons

The evaluator supports the prompt-required reasons:

- `missing_identity`;
- `missing_policies`;
- `missing_permissions`;
- `missing_feeds_create`;
- `missing_status_draft_validation`;
- `missing_status_draft_preset`;
- `unexpected_feeds_create_field`;
- `forbidden_update_permission`;
- `forbidden_delete_permission`;
- `forbidden_collection`;
- `forbidden_action`;
- `forbidden_system_access`;
- `forbidden_file_or_folder_access`;
- `wildcard_collection`;
- `wildcard_action`;
- `malformed_payload`;
- `ambiguous_policy_graph`.

It also emits narrower diagnostic reasons when useful, such as
`missing_target_url`, `missing_observed_at`, `missing_feeds_create_fields`, and
`wildcard_field`.

## Verification

Run from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall .
uv run python directus_policy_evidence.py \
  --input ../../../docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json \
  --output /tmp/directus-policy-graph-evidence-evaluation.json \
  --force
uv run python directus_policy_evidence.py \
  --raw-input /path/to/raw-directus-policy-graph.json \
  --normalized-output /tmp/directus-policy-graph-evidence.normalized.json \
  --evaluation-output /tmp/directus-policy-graph-evidence-evaluation.json \
  --force
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
  - docs/migrations/wordpress-to-directus/task-b-pre-create-safety-gates.md
  - docs/migrations/wordpress-to-directus/task-b-live-pre-create-gate-artifacts.md
  - docs/migrations/wordpress-to-directus/task-b-directus-migration-identities.md
  - docs/migrations/wordpress-to-directus/task-b-directus-permission-implementation-plan.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-plan.md
  - cms/utils/wordpress/pre_create_gates.py
  - cms/utils/wordpress/create_manifest_executor.py
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/inventory/permission_gate.py
  - cms/utils/wordpress/tests/test_pre_create_gates.py
  - cms/utils/wordpress/tests/test_create_manifest_executor.py
files_changed:
  - cms/utils/wordpress/directus_policy_evidence.py
  - cms/utils/wordpress/tests/test_directus_policy_evidence.py
  - docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-plan.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-evaluator.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
findings:
  - The evaluator is pure and deterministic.
  - Rejected evidence is returned as machine-readable `status = rejected`, not raised as an exception.
  - The static JSON example now includes `target_url` so it can be evaluated by the same contract.
verification:
  - Run the command block in the Verification section.
production_artifact_impact: none
risks:
  - Raw Directus policy export normalization is still a future task.
  - Live evidence collection remains approval-gated and unimplemented.
open_questions:
  - None for this local evaluator slice.
next_action: Use the evaluator on a future sanitized live evidence artifact after explicit approval to collect that artifact.
```
