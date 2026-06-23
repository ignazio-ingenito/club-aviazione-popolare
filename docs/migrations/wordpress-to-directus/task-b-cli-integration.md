# Task B slice 6 — Read-only CLI and manifest writer

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice adds the read-only inventory CLI and atomic manifest writer used to
produce controlled run artifacts outside Git. It does not execute a production
import and does not approve any Directus baseline.

Implemented:

- `python -m inventory --help`;
- CLI commands for route, WordPress core, gallery, and Directus core inventories;
- explicit `--output-dir` and `--filename` for every command;
- deterministic JSONL rendering through existing manifest contracts;
- `.sha256` sidecar files;
- atomic temp-file and rename writes;
- refusal to write inside the repository;
- refusal to overwrite existing JSONL or checksum artifacts;
- restrictive output directory/file permissions when the OS permits them;
- synthetic tests for help output, route command output, writer replacement,
  checksum content, and unsafe filename rejection.

## Safety properties

- No write-capable WordPress or Directus client is imported.
- WordPress and Directus CLI commands use the existing GET/HEAD-only inventory clients.
- Route inventory uses only repository filesystem reads.
- Generated artifacts are written only to an explicit output directory.
- The writer rejects repository-local output directories.
- The writer refuses to overwrite existing run artifacts.
- Live inventories, credentials, article bodies, private metadata, and binary media are not committed.
- The CLI does not create write manifests or classify create candidates.

## Files changed

```text
cms/utils/wordpress/inventory/__main__.py
cms/utils/wordpress/inventory/writer.py
cms/utils/wordpress/tests/test_inventory_cli.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-cli-integration.md
```

## Verification

Required from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall -q inventory tests
uv run python -m inventory --help
```

## CLI examples

Use a run directory outside Git:

```bash
RUN_DIR="$HOME/cap-migration-runs/$(date -u +%Y%m%dT%H%M%SZ)-inventory"
mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR"

uv run python -m inventory routes --output-dir "$RUN_DIR" --filename routes.jsonl
uv run python -m inventory wordpress-core --output-dir "$RUN_DIR" --filename wordpress.jsonl
uv run python -m inventory gallery --output-dir "$RUN_DIR" --filename gallery.jsonl
uv run python -m inventory directus-core --output-dir "$RUN_DIR" --filename directus-public-view.jsonl
```

If anonymous Directus emits inaccessible endpoint issues, the resulting file is
a public-view inventory, not an approved baseline.

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It writes only local run artifacts.
2. Could any runtime path emit `POST`, `PATCH`, `PUT`, or `DELETE`? **No.** Network commands use the GET/HEAD-only clients.
3. Could generated live inventories be committed by default? **No.** Output location is explicit and examples use `$HOME/cap-migration-runs`.
4. Could checksum files drift from JSONL content? **No.** Tests assert sidecar checksum content.
5. Could unsafe filenames escape the output directory? **No.** Writer rejects path separators and non-JSONL filenames.
6. Could run evidence be silently overwritten? **No.** Writer refuses existing JSONL or checksum artifacts.
7. Could artifacts be written inside the repository? **No.** CLI passes the repository root and writer rejects paths below it.
8. Could this approve an incomplete Directus baseline? **No.** Directus public-view limitations remain explicit in docs and target issues.

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
  - cms/utils/wordpress/inventory/jsonl.py
  - cms/utils/wordpress/inventory/wordpress.py
  - cms/utils/wordpress/inventory/gallery.py
  - cms/utils/wordpress/inventory/directus.py
  - cms/utils/wordpress/inventory/routes.py
  - cms/utils/wordpress/pyproject.toml
files_changed:
  - cms/utils/wordpress/inventory/__main__.py
  - cms/utils/wordpress/inventory/writer.py
  - cms/utils/wordpress/tests/test_inventory_cli.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-cli-integration.md
findings:
  - The existing deterministic JSONL renderer can be reused by a narrow atomic writer.
  - CLI integration can stay standard-library only and avoid adding dependencies.
  - Live Directus anonymous output must be named public-view if endpoint issues remain.
  - Run artifacts must be outside the repository and immutable by default.
verification:
  - Focused CLI tests passed during implementation.
  - Full required test suite must pass before commit.
production_artifact_impact: none
risks:
  - Running WordPress or Directus CLI commands live can produce article bodies in run artifacts; keep output outside Git.
  - Anonymous Directus remains insufficient for an approved baseline.
open_questions:
  - Which strict read-only Directus identity will be used for approved baseline capture?
next_action: Execute live read-only inventories into a controlled run directory outside Git.
```
