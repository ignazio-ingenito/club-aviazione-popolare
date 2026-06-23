# Task B slice 9.3 - Approved write-manifest selection

Status: implemented and ready for review

Date: 2026-06-20

## Scope

This slice derives an approved write manifest from the reconciliation report.
It keeps protected target records out of the write path by selecting only
source-side `create_candidate` records.

Implemented:

- `build_approved_write_manifest` for filtered candidate selection;
- immutable metadata linking source, target, and reconciliation hashes;
- conversion back to a source-scoped `InventoryManifest` for controlled run
  writing;
- tests proving non-create records are excluded and wrong-scope input fails
  closed.

## Safety properties

- Protected existing target items do not enter the approved write manifest.
- Only source `create_candidate` records are selected.
- The builder never writes to Directus.
- The helper fails closed when the source manifest scope is wrong.

## Files changed

```text
cms/utils/wordpress/inventory/__init__.py
cms/utils/wordpress/inventory/write_manifest.py
cms/utils/wordpress/tests/test_write_manifest.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-write-manifest.md
```

## Verification

Required from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_write_manifest.py' -v
uv run python -m unittest discover -s tests -p 'test_*.py' -v
```

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It only selects records for a future manifest.
2. Could a protected target record enter the approved write manifest? **No.** Only source `create_candidate` records are selected.
3. Could the builder mutate Directus? **No.** It is pure in-memory selection.
4. Could wrong-scope input silently pass? **No.** It fails closed.
5. Could the future writer still use the wrong record set? **Yes, if wired incorrectly later.** That risk remains at integration time.

## Handoff

```yaml
files_inspected:
  - cms/utils/wordpress/inventory/__init__.py
  - cms/utils/wordpress/inventory/reconciliation.py
  - cms/utils/wordpress/tests/test_reconciliation.py
  - cms/utils/wordpress/tests/test_inventory_cli.py
files_changed:
  - cms/utils/wordpress/inventory/__init__.py
  - cms/utils/wordpress/inventory/write_manifest.py
  - cms/utils/wordpress/tests/test_write_manifest.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-write-manifest.md
findings:
  - The reconciliation report is sufficient to derive an approved candidate set.
  - Selection is cleaner as a pure helper than as part of the transport client.
  - The manifest still needs an eventual writer integration, but the record gate is now explicit.
verification:
  - Focused write-manifest tests passed.
  - Full wordpress package test suite passed.
production_artifact_impact: none
risks:
  - The helper is not yet connected to any production write executor.
  - Future writer integration must keep the same candidate-only filter.
open_questions:
  - Which commit should wire this approved manifest into the future create-only executor?
next_action: Integrate the approved manifest into the future writer path and continue closing the remaining Phase 2 checks.
```
