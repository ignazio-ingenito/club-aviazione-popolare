# Task B slice 9.7 - Live pre-create gate artifacts

Status: completed with rejected gates

Date: 2026-06-22

## Scope

This slice attempted to generate the two pre-create gate artifacts for the
approved draft-only manifest in:

```text
/home/iingenito/cap-migration-runs/20260622T110402Z
```

No production write was performed. No `--execute` run was performed.

## Artifact results

| Artifact | Status | SHA-256 | Reason |
| --- | --- | --- | --- |
| `/home/iingenito/cap-migration-runs/20260622T110402Z/permission-evidence-create-only.json` | `rejected` | `bd78a7b6ffcce97d45bc8d4667ccc0cab9fa181f097d60e27a30aec286ec3ba2` | `create_only_identity_unavailable` |
| `/home/iingenito/cap-migration-runs/20260622T110402Z/fresh-target-absence-before-create.json` | `rejected` | `4b855356f65db397850cf33eb4085547c3eb590920fa8f407105b3cd289e9c4b` | `target_read_unavailable` |

The approved input artifact hashes were verified:

- `migration-approval.json`: `566ca0d3026ca9035853f623fc1d83d6b8fd31dc54bced9bbdc077c82ea266ee`
- `create-manifest-draft-only.json`: `902e118a73acad4aacd504f6076ef867c7693f2d16144a45cdd78014269c6e4d`

## Secret review

`secrets/migration` was checked with SOPS without printing secret values.

The only Directus token found was:

```text
secrets/migration/directus-schema-token.20260622.sops.yaml
```

Its non-secret metadata identifies it as a temporary schema-capable token for
the approved `member_*` schema apply. Its allowed use is Directus schema setup
only, with no content import, media upload, or user migration.

Because this slice needs a content-migration create-only identity, the
schema-capable token was not used for permission evidence or target absence
reads.

## Validation

The pre-create gate validators were run against the generated artifacts. Both
failed closed as expected because the artifacts are intentionally `rejected`:

```text
permission: rejected_fail_closed
fresh_target_absence: rejected_fail_closed
```

The executor dry-run was run without `--execute` and generated reports in:

```text
/home/iingenito/cap-migration-runs/20260622T110402Z/executor-gated-dry-run
```

Result:

```text
execute=false
executed_operations=0
request_plan_sha256=142cc3a6820509c8f9faaba0cbe813af34b7e1fb54dbddc5e38594931cb64b90
```

The request-plan report file hash is:

```text
6b637759172e829ccf749e428bca4a1c21adf07ad0ff03783d079586ebb8ec17
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
  - docs/migrations/wordpress-to-directus/task-b-create-manifest-executor.md
  - docs/migrations/wordpress-to-directus/task-b-pre-create-safety-gates.md
  - cms/utils/wordpress/pre_create_gates.py
  - cms/utils/wordpress/create_manifest_executor.py
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/tests/test_pre_create_gates.py
  - cms/utils/wordpress/tests/test_create_manifest_executor.py
files_changed:
  - docs/migrations/wordpress-to-directus/task-b-live-pre-create-gate-artifacts.md
commands_run:
  - git status --short
  - git log --oneline -5
  - git show --stat --oneline 37a15c82735f886107da652957dd5b9b48335706
  - sha256sum migration-approval.json create-manifest-draft-only.json
  - sops -d secrets/migration/directus-schema-token.20260622.sops.yaml
  - uv run python create_manifest_executor.py --manifest ... --approval ... --permission-evidence ... --fresh-target-absence ... --output-dir ...
  - uv run python -m unittest discover -s tests -p 'test_*.py' -v
  - uv run python -m compileall .
production_artifact_impact: none
risks:
  - No create-only Directus execution identity is currently available in committed SOPS migration secrets.
  - The fresh target absence gate remains unproven because the schema-capable token was intentionally not used for content-import reads.
  - Production execution remains blocked.
open_questions:
  - Provide or create a SOPS-encrypted create-only Directus token for the WordPress content migration gate.
  - Decide whether a separate read-only token should be used for fresh target absence, or whether the create-only identity should also perform the read checks.
next_action: Add the correct create-only/read identity secret and rerun this slice without performing any POST.
```
