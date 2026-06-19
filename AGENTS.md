# Club Aviazione Popolare — Agent Instructions

## Purpose

This repository contains the public Club Aviazione Popolare website, its Directus CMS image, and utilities used to migrate content from the currently online WordPress site.

All agent-assisted work must preserve production content and follow the repository documentation before changing code, schema, data, or operational procedures.

## Global Instructions

Also follow the global agent instructions available in the execution environment. This file adds repository-specific constraints and takes precedence for this project when it is stricter.

## Canonical Documentation

Read these files before working on the WordPress migration:

1. `CONTEXT.md`
2. `docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md`
3. `docs/migrations/wordpress-to-directus/README.md`
4. `docs/migrations/wordpress-to-directus/specification.md`
5. `docs/migrations/wordpress-to-directus/plan.md`
6. `docs/migrations/wordpress-to-directus/runbook.md`
7. `docs/migrations/wordpress-to-directus/agent-loop.md`

The ADR and migration specification are authoritative for safety. The plan tracks execution. The runbook governs production operations.

## Fundamental Production Invariant

**Every article, file, folder, category relation, and gallery relation already present in the target Directus instance at the approved baseline timestamp is an immutable production artifact.**

Agents and migration tools MUST NOT:

- update or overwrite an existing `feeds` item;
- change the title, slug, content, category, cover, author, status, dates, metadata, or relations of an existing feed;
- delete an existing Directus item;
- replace, update, rename, move, or delete an existing Directus file;
- add files to an existing gallery folder when that can change an existing page;
- delete or rename an existing Directus folder;
- rewrite an existing article merely because WordPress contains a different version;
- treat WordPress as authoritative over content already curated in Directus;
- use cleanup, deduplication, overwrite, or synchronization semantics against production.

If an existing Directus article differs from WordPress, the Directus version wins and is classified as a protected production artifact. The difference is reported; it is never reconciled by mutation.

The protected set includes both:

- all target objects captured by the approved pre-migration baseline; and
- all objects created by a completed migration run after that run is accepted.

## Migration Write Boundary

Production migration is additive-only.

Allowed production writes, after explicit approval and all runbook gates pass:

- create a new feed proven missing;
- create a new file proven missing;
- create a new folder dedicated to the current migration;
- create a new relation whose parent and child are migration-owned or whose creation does not mutate an existing artifact;
- append an entry to the migration ledger or run audit collection.

All production writes must use a dedicated service role that can read and create only. The role must not have update, delete, schema, settings, user, or permission-management capabilities.

A migration worker must fail closed if it cannot prove that the effective token is create-only.

## Legacy Importer Restrictions

The existing utility under `cms/utils/wordpress/` is useful for discovery but is not approved for production execution in its current form.

The following existing paths or options are forbidden against production:

- `main.py delete`;
- `--overwrite`;
- `--overwrite-media`;
- `directus.update_item`;
- `directus.delete_item` and `directus.delete_items`;
- `directus.delete_file`;
- `directus.delete_folder` and `directus.delete_folders`;
- any fallback that truncates or omits article content to make a write succeed;
- AI formatting during migration;
- automatic removal of images or logos from source content;
- using `parser.yaml` or joblib cache as proof that an item exists in the current target.

`parser.yaml` is historical evidence only. Every mapping must be revalidated against the current target inventory.

## Working Rules

Before implementation:

1. Identify whether the task is documentation, discovery, schema design, importer code, staging rehearsal, or production operation.
2. Use an `explorer` read-only pass before any worker writes code.
3. Read the canonical migration documents listed above.
4. Inspect the relevant existing implementation under `cms/utils/wordpress/` and the frontend consumers under `lib/`, `components/`, and `app/`.
5. State the allowed files, forbidden files, verification command, and stop conditions before assigning a worker.
6. Keep schema work, importer work, frontend gallery work, and production execution in separate tasks and preferably separate pull requests.
7. Use small, serial changes for migration state, Directus schema, and import code. Do not run parallel writers on shared migration files.
8. Add tests for every safety invariant before enabling a write path.
9. Prefer deterministic, reversible-by-quarantine behavior over cleanup or in-place updates.
10. Preserve original WordPress content. Only deterministic URL rewriting and documented sanitization are allowed for newly created items.
11. Do not use AI to rewrite, summarize, format, or correct imported content unless a separate editorial task is explicitly approved.
12. Never commit production inventories, tokens, exported content, binary media, or run manifests containing private data.

## Agent Loop Rules

Use the global `agent-loop` skill with the task cards in `docs/migrations/wordpress-to-directus/agent-loop.md`.

Each loop must follow this order:

1. `explorer`: read-only inventory, risks, proposed scope, and verification.
2. main agent: accept or reduce scope; define allowed and forbidden files.
3. `worker`: one atomic change only.
4. `reviewer`: independently check the production invariant and tests.
5. main agent: update the canonical plan and leave a handoff.

Parallel explorers are allowed for independent read-only analysis. Write-heavy work remains serial.

Stop immediately when:

- a task would require modifying or deleting a protected target object;
- a candidate match is ambiguous;
- the target baseline changed after approval;
- the Directus token has update or delete permission;
- the backup or upload-volume protection cannot be verified;
- a write path emits `PATCH`, `PUT`, or `DELETE`;
- schema, permission, or production actions were not explicitly approved;
- the source or target inventory is incomplete;
- an imported item would collide with an existing slug, URL, source identity, or route.

After three failed loops or evidence that the direction is wrong, stop and return to the last read-only checkpoint with a narrower prompt.

## Confirmation Boundaries

Routine repository exploration, documentation edits, local tests, and read-only inventory design do not require additional confirmation when they are within the approved task.

Explicit confirmation is required before:

- any production write;
- any Directus schema change or schema apply;
- creating or changing production roles, tokens, or permissions;
- taking or restoring a production backup or PVC snapshot;
- changing deployment manifests in the `homelab` repository;
- publishing imported feeds;
- quarantining migration-created records after a failed run;
- any destructive or irreversible action.

## Required Handoff

Every explorer, worker, and reviewer must report:

- `files_inspected`;
- `files_changed`;
- `findings`;
- `verification`;
- `production_artifact_impact`;
- `risks`;
- `open_questions`;
- `next_action`.

`production_artifact_impact` must explicitly say whether any baseline feed, file, folder, or relation could be affected. “Unknown” is a stop condition, not an acceptable completion state.

## Definition of Done

A migration-related task is complete only when:

- it follows ADR 0001 and the migration specification;
- no protected production artifact is modified or deleted;
- tests prove dry-run sends no non-read requests;
- tests prove execution never emits `PATCH`, `PUT`, or `DELETE`;
- identity and ambiguity handling fail closed;
- the planned verification command passes;
- documentation and the canonical plan are updated;
- assumptions and unresolved questions are listed;
- the final response includes a Conventional Commit suggestion.

## Final Response Format

Use these sections:

- Summary
- Files changed
- Production artifact impact
- Checks performed
- Assumptions
- Open questions
- Suggested commit message
