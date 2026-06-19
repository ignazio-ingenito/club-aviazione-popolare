# Task B slice 3 — Gallery discovery

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice adds source-side gallery inventory discovery for WordPress galleries.
It performs no Directus access and exposes no write path.

Implemented:

- REST-first gallery discovery through `/wp-json/wp/v2/types`;
- exposed gallery REST endpoint inventory with complete WordPress pagination;
- ordered public HTML fallback for `/gallery/` and `/dt-gallery/<slug>/`;
- album order preservation from the archive DOM;
- image order preservation from each album DOM;
- explicit source issues for missing REST exposure, unreadable albums, empty albums, and empty archives;
- synthetic tests for REST discovery, fallback discovery, ordering, issues, manifest serialization, and GET-only transport behavior.

## Safety properties

- Only `ReadOnlyHttpClient` is used for network access.
- Public request paths permit `GET` and `HEAD` only.
- No WordPress write endpoint is called.
- No Directus endpoint is called.
- No legacy importer, joblib cache, `parser.yaml`, AI formatter, or mutable Directus client is imported.
- Public HTML discovery records album and image order as explicit ordered lists.
- Live inventory artifacts, article bodies, credentials, and binary media are not committed.

## Files changed

```text
cms/utils/wordpress/inventory/gallery.py
cms/utils/wordpress/tests/test_gallery_inventory.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-gallery-discovery.md
```

## Verification

Required from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall -q inventory tests
```

`uv run python -m inventory --help` remains part of the Task B exit gate after
the read-only CLI is implemented in slice 6.

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It is source-side inventory only and does not call Directus.
2. Could any runtime path emit `POST`, `PATCH`, `PUT`, or `DELETE`? **No.** The public transport rejects non-read methods before network use.
3. Could gallery order be lost? **No.** Archive album order and album image order are preserved in ordered lists.
4. Could REST absence be hidden? **No.** The fallback adds an explicit `gallery_rest_type_not_exposed` warning.
5. Could missing albums or images be silently omitted? **No.** Empty archives, unreadable albums, and image-less albums emit explicit issues.
6. Could stale cache or historical mappings influence inventory? **No.** This slice does not use joblib cache or `parser.yaml`.
7. Could the implementation classify an album as a create candidate? **No.** Reconciliation and write manifests are outside scope.

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/handoffs/codex_handoff_cap_wordpress_migration.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/specification.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/runbook.md
  - docs/migrations/wordpress-to-directus/agent-loop.md
  - docs/migrations/wordpress-to-directus/discovery.md
  - docs/migrations/wordpress-to-directus/task-b-inventory-contracts.md
  - cms/utils/wordpress/inventory/http.py
  - cms/utils/wordpress/inventory/wordpress.py
  - cms/utils/wordpress/inventory/models.py
  - cms/utils/wordpress/tests/test_wordpress_inventory.py
files_changed:
  - cms/utils/wordpress/inventory/gallery.py
  - cms/utils/wordpress/tests/test_gallery_inventory.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-gallery-discovery.md
findings:
  - The current inventory package can support gallery discovery without touching the unsafe legacy importer.
  - REST discovery and HTML fallback can share manifest record contracts while keeping discovery method explicit.
  - HTML fallback must preserve DOM order because WordPress gallery order is semantic.
verification:
  - Focused gallery unit tests passed during implementation.
  - Full required test suite must pass before commit.
production_artifact_impact: none
risks:
  - Public HTML selectors may need adjustment after live source inventory, but failures are explicit issues.
  - REST gallery exposure remains a runtime fact to capture in controlled run artifacts outside Git.
open_questions:
  - None introduced by this slice.
next_action: Implement Task B slice 4, the Directus anonymous/read-only inventory client.
```
