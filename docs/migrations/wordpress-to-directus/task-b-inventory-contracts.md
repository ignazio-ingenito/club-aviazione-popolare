# Task B slice 1 — Inventory contracts

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice establishes the deterministic, read-only data contracts used by later WordPress and Directus inventory clients. It performs no network access and exposes no write path.

Implemented:

- canonical JSON normalization;
- explicit rejection of ambiguous unordered or binary values;
- UTC normalization for timezone-aware datetimes;
- SHA-256 helpers;
- immutable source/target manifest records;
- structured warning/error/fatal inventory issues;
- deterministic record and issue sorting;
- duplicate identity rejection;
- separate content and run-document fingerprints;
- deterministic JSONL rendering;
- strict pagination metadata and complete-page sequence validation;
- synthetic-data unit tests using the Python standard library.

## Safety properties

- No WordPress or Directus client is imported or called.
- No HTTP method is available in this package.
- Manifest input data is copied and recursively frozen.
- Lists and tuples preserve order so gallery order remains semantic.
- Sets are rejected rather than silently sorted.
- Binary values are rejected and must be referenced by an external checksum.
- Naive datetimes are rejected.
- Duplicate `(entity_type, identity)` records are rejected.
- A source record cannot be added to a target manifest, or vice versa.
- Pagination must be contiguous, internally consistent, and complete before items can be merged.
- The content fingerprint excludes observation time; the full manifest fingerprint includes run metadata and observation time.

## Files changed

```text
cms/utils/wordpress/inventory/__init__.py
cms/utils/wordpress/inventory/canonical.py
cms/utils/wordpress/inventory/jsonl.py
cms/utils/wordpress/inventory/models.py
cms/utils/wordpress/inventory/pagination.py
cms/utils/wordpress/tests/__init__.py
cms/utils/wordpress/tests/test_manifest.py
docs/migrations/wordpress-to-directus/task-b-inventory-contracts.md
```

No dependency or lockfile change is required. Tests use `unittest` from the Python standard library.

## Verification

Executed from a synthetic local copy of the new package:

```bash
python -m unittest discover -s tests -v
python -m compileall -q inventory tests
```

Result:

- 16 tests passed;
- compile check passed.

The test suite covers:

- key-order-independent object hashes;
- order-sensitive sequences;
- timezone normalization;
- rejection of naive datetimes, sets, and binary data;
- immutable record inputs;
- deterministic record sorting;
- duplicate and scope rejection;
- content hash versus run-document hash;
- JSON serializability and deterministic JSONL;
- complete, missing, inconsistent, and empty pagination.

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It has no network or Directus code.
2. Could stale cache or historical mapping bypass current target validation? **No.** Neither is referenced.
3. Can any runtime path emit a forbidden HTTP method? **No.** No HTTP client exists in this slice.
4. Can a source-target difference become an update? **No.** Reconciliation and writes are outside scope.
5. Can ambiguous identity become automatic creation? **No.** Duplicate identity is rejected and no creation path exists.
6. Are retries idempotent under uncertain network outcomes? **Not applicable.** No network operations exist.
7. Are new feeds drafts and publication separate? **Not applicable yet; preserved by the governing specification.**
8. Are generated inventories and credentials kept outside Git? **Yes.** Only contracts and synthetic tests are committed.

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/migrations/wordpress-to-directus/discovery.md
  - docs/migrations/wordpress-to-directus/specification.md
  - docs/migrations/wordpress-to-directus/agent-loop.md
  - cms/utils/wordpress/pyproject.toml
files_changed:
  - cms/utils/wordpress/inventory/__init__.py
  - cms/utils/wordpress/inventory/canonical.py
  - cms/utils/wordpress/inventory/jsonl.py
  - cms/utils/wordpress/inventory/models.py
  - cms/utils/wordpress/inventory/pagination.py
  - cms/utils/wordpress/tests/__init__.py
  - cms/utils/wordpress/tests/test_manifest.py
  - docs/migrations/wordpress-to-directus/task-b-inventory-contracts.md
findings:
  - Standard-library contracts are sufficient for deterministic manifests and tests.
  - Top-level record order is normalized, while nested sequence order is preserved.
  - Pagination can fail closed before source or target data is accepted as complete.
verification:
  - 16 unit tests passed.
  - compileall passed.
production_artifact_impact: none
risks:
  - Entity-specific source and target payload schemas remain to be defined by their clients.
  - Runtime inventories still require strict read-only credentials and must remain outside Git.
open_questions:
  - None introduced by this slice.
next_action: Implement Task B slice 2, the fresh WordPress read-only client, against these contracts using synthetic HTTP fixtures.
```
