# Task B slice 8 — Reconciliation workflow

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice documents the reconciliation workflow that now exists in code. It
connects the read-only source and target inventories to the approved write
boundary without changing production data.

Implemented:

- reconciliation states from the specification, surfaced in the current report as
  `already_imported`, `create_candidate`, `conflict`, and `manual_review`;
- accepted ledger-first matching;
- exact `original_uri` matching;
- validated historical mapping as corroboration only, never as authority;
- protected-existing-drift handling;
- manual-review, create-candidate, conflict, excluded, and source-error
  classification;
- target-only protected classification for unmatched target items;
- route and slug collision review before any write-manifest is built;
- immutable reconciliation report and write-manifest handoff expectations;
- reviewer traceability for why a candidate does not appear in the write
  manifest.

## Safety properties

- The workflow remains additive-only and target-authoritative.
- `parser.yaml` is historical corroboration only and cannot authorize a write.
- Existing Directus feeds, files, folders, and relations remain protected.
- A source-target drift is never reconciled by mutating the target.
- A write manifest may contain only approved `create_candidate` items.
- No production data is written by this documentation task.

## Files changed

```text
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/runbook.md
docs/migrations/wordpress-to-directus/task-b-reconciliation.md
```

## Verification

Required from the documentation review path:

```bash
sed -n '1,220p' docs/migrations/wordpress-to-directus/README.md
sed -n '1,240p' docs/migrations/wordpress-to-directus/plan.md
sed -n '1,220p' docs/migrations/wordpress-to-directus/runbook.md
```

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It only updates documentation.
2. Could any runtime path emit `POST`, `PATCH`, `PUT`, or `DELETE`? **No.** No code path changed.
3. Could `parser.yaml` become authoritative by wording drift? **No.** The handoff says corroboration only.
4. Could reconciliation happen after write-manifest construction? **No.** The runbook now places reconciliation approval before manifest building.
5. Could this approve a production write? **No.** It is documentation only.

## Handoff

```yaml
files_inspected:
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/runbook.md
  - docs/migrations/wordpress-to-directus/specification.md
  - docs/migrations/wordpress-to-directus/task-b-cli-integration.md
  - docs/migrations/wordpress-to-directus/task-b-directus-inventory.md
  - docs/migrations/wordpress-to-directus/task-b-gallery-discovery.md
  - docs/migrations/wordpress-to-directus/task-b-route-inventory.md
  - docs/migrations/wordpress-to-directus/task-b-wxr-media-inventory.md
files_changed:
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/runbook.md
  - docs/migrations/wordpress-to-directus/task-b-reconciliation.md
findings:
  - The repo already uses target-authoritative reconciliation language in the specification.
  - The runbook needed the manifest boundary made explicit before write-manifest construction.
  - `parser.yaml` wording needed one more explicit corroboration-only reminder.
verification:
  - Documentation-only review of the updated migration docs.
production_artifact_impact: none
risks:
  - If later edits soften the corroboration-only language, the reconciliation boundary could drift.
  - The new handoff is documentation-only and does not itself exercise code paths.
open_questions:
  - None.
next_action: Keep the reconciliation boundary and write-manifest gate aligned in future migration doc updates.
```
