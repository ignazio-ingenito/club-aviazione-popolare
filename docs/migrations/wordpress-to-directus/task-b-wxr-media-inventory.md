# Task B slice 7 — WordPress WXR media export inventory

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice adds a local, source-only inventory path for WordPress admin WXR
exports when public WordPress REST media pagination is incomplete.

Implemented:

- `python -m inventory wordpress-wxr-media`;
- parsing only local WXR `attachment` items;
- `wordpress_media` records keyed as `wordpress:media:<post_id>`;
- source URL capture from `wp:attachment_url` with `link` fallback;
- issue emission for malformed attachment IDs or missing attachment URLs;
- no network access in the WXR parser;
- `.gitignore` protection for common local WordPress/WXR export filenames;
- tests for parsing, malformed IDs, missing files, CLI output, and checksum creation.

## Observed production source evidence

The admin export `cap.WordPress.2026-06-19.xml` contains:

- `1444` total WXR items;
- `1444` attachment items;
- `0` duplicate attachment IDs;
- `0` attachments missing `wp:attachment_url`;
- attachment ID range `3291` to `8395`.

Public REST media pagination exposed `1436` IDs while reporting `1444` total
items. The eight WXR attachment IDs missing from public REST pagination are:

```text
3308, 3309, 3310, 3311, 3312, 3313, 3314, 3315
```

Individual public REST reads for those IDs returned `401`. Therefore the WXR
export is required as source evidence for REST-private media attachments.

## Safety properties

- The WXR parser reads only a local XML export.
- It performs no WordPress or Directus network requests.
- It creates no write manifests and no import candidates.
- Common local WordPress/WXR export filenames remain untracked by default.
- Operators should still keep source exports outside the repository when possible.
- Generated manifests still must be written outside Git through the existing
  artifact writer.

## Files changed

```text
.gitignore
cms/utils/wordpress/inventory/__main__.py
cms/utils/wordpress/inventory/wxr.py
cms/utils/wordpress/tests/test_inventory_cli.py
cms/utils/wordpress/tests/test_wxr_inventory.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-wxr-media-inventory.md
```

## Verification

Required from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall -q inventory tests
uv run python -m inventory --help
```

Live artifact command:

```bash
uv run python -m inventory wordpress-wxr-media \
  --input /path/to/cap.WordPress.2026-06-19.xml \
  --output-dir "$RUN_DIR" \
  --filename wordpress-wxr-media.jsonl \
  --environment production
```

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-cli-integration.md
  - cms/utils/wordpress/inventory/__main__.py
  - cms/utils/wordpress/inventory/wordpress.py
  - cms/utils/wordpress/inventory/models.py
  - cms/utils/wordpress/tests/test_inventory_cli.py
files_changed:
  - .gitignore
  - cms/utils/wordpress/inventory/__main__.py
  - cms/utils/wordpress/inventory/wxr.py
  - cms/utils/wordpress/tests/test_inventory_cli.py
  - cms/utils/wordpress/tests/test_wxr_inventory.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-wxr-media-inventory.md
findings:
  - WordPress admin WXR export contains all 1444 media attachments reported by REST totals.
  - Public REST omits eight media IDs from pagination and returns 401 for direct reads of those IDs.
  - WXR is source evidence only; it is not a target baseline and does not authorize writes.
verification:
  - Full required test suite must pass before commit.
production_artifact_impact: none
risks:
  - WXR is not a full site backup; use it as attachment source evidence and reconcile against REST/posts separately.
  - Local export XML can contain production data and must not be committed.
open_questions:
  - Whether source reconciliation should prefer REST payloads for public media and WXR payloads only for REST-private media.
next_action: Generate a controlled WXR media manifest outside Git and use it with REST source inventory during reconciliation.
```
