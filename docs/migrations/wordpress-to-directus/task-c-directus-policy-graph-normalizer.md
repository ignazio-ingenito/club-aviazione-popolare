# Task C - Directus policy graph normalizer

Status: implemented; local synthetic raw normalizer plus mocked collector scaffold

Date: 2026-06-22

## Scope

This slice implements a pure local normalizer that converts a conservative raw
Directus policy graph payload into the normalized evidence shape consumed by the
existing local evaluator.

Implemented:

- `cms/utils/wordpress/directus_policy_evidence.py`;
- `DirectusPolicyEvidenceError`;
- `normalize_directus_policy_graph_payload(raw)`;
- CLI raw mode with normalized output and evaluation output;
- synthetic unit tests for strict malformed-input failures;
- synthetic unit tests proving unsafe update/delete/wildcard permissions survive
  normalization and are rejected by the evaluator.
- a separate mocked GET-only collector scaffold that returns this raw shape.

Not implemented:

- production live Directus collection;
- Directus role, policy, user, token, schema, content, or media changes;
- production `POST`;
- migration execution with `--execute`;
- support for undocumented Directus API response shapes.

The collector scaffold is documented separately in
[Task C Directus policy graph live collector scaffold](task-c-directus-policy-graph-live-collector.md).
It does not change the normalizer contract and does not prove any production
identity until live artifacts are collected outside Git and evaluated.

## Contract

The public function is:

```python
normalize_directus_policy_graph_payload(raw: Mapping[str, Any]) -> dict[str, Any]
```

The output has this shape:

```json
{
  "kind": "directus_policy_graph_evidence",
  "target_url": "...",
  "observed_at": "...",
  "directus_version": "...",
  "identity": {
    "label": "...",
    "role": "..."
  },
  "policies": [],
  "permissions": []
}
```

The result is intended to be passed directly to:

```python
evaluate_policy_graph_evidence(normalized)
```

## Fail-Closed Rules

The normalizer raises `DirectusPolicyEvidenceError` when raw input is malformed
or ambiguous:

- missing `target_url`;
- missing `observed_at`;
- missing `identity`;
- missing `identity.role`;
- selected identity role not found in `roles`;
- missing `roles`, `policies`, or `permissions` list;
- multiple raw roles matching the selected identity role;
- no policy attached to the selected identity role;
- any policy in the raw payload not attached to the selected identity role;
- malformed policy role linkage;
- permission referencing an unknown or unattached policy;
- missing permission collection or action;
- malformed `fields`;
- malformed `validation`;
- malformed `presets`;
- missing action or collection;
- multiple identity roles without an explicit selected `identity.role`.

The normalizer does not decide whether a structurally valid policy is safe.
Wildcard collection/action, `feeds.update`, `feeds.delete`, and system-resource
access are preserved in the normalized artifact when graph linkage is otherwise
clear, so the evaluator can reject them with stable reasons.

## CLI

```bash
cd cms/utils/wordpress

uv run python directus_policy_evidence.py \
  --raw-input /path/to/raw-directus-policy-graph.json \
  --normalized-output /tmp/directus-policy-graph-evidence.normalized.json \
  --evaluation-output /tmp/directus-policy-graph-evidence-evaluation.json \
  --force
```

Exit codes:

- `0`: normalized successfully and evaluator approved;
- `2`: normalized successfully and evaluator rejected;
- `1`: raw payload malformed, I/O failure, mode error, or overwrite refusal.

The CLI refuses to overwrite either output file unless `--force` is provided.

## Verification

Run from `cms/utils/wordpress`:

```bash
uv run python -m unittest tests/test_directus_policy_normalization.py -v
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
  - docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json
  - cms/utils/wordpress/directus_policy_evidence.py
  - cms/utils/wordpress/tests/test_directus_policy_evidence.py
files_changed:
  - cms/utils/wordpress/directus_policy_evidence.py
  - cms/utils/wordpress/tests/test_directus_policy_normalization.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-plan.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-evaluator.md
  - docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-normalizer.md
findings:
  - Normalization is strict and local-only.
  - Malformed raw input raises `DirectusPolicyEvidenceError`.
  - Valid but unsafe permissions are normalized and rejected by the evaluator.
verification:
  - Run the command block in the Verification section.
production_artifact_impact: none
risks:
  - Actual live Directus response shape is still not collected or supported
    beyond the documented synthetic raw shape.
  - Live evidence collection remains approval-gated and unimplemented.
open_questions:
  - None for this local normalizer slice.
next_action: Use an operator-provided sanitized raw artifact outside Git, or implement the separate approval-gated live collector later.
```
