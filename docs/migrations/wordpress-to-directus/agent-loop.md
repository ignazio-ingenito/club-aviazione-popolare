# Agent Loop execution guide

Status: ready for documentation review

Use this guide with the global `agent-loop` skill. It does not authorize production actions.

## Global loop contract

Every task follows this sequence:

1. **Explorer**: read-only analysis, inventory, risk, and proposed scope.
2. **Main agent**: accepts or reduces scope and defines allowed files, forbidden files, verification, and stop conditions.
3. **Worker**: performs one atomic change.
4. **Reviewer**: independently checks the production invariant and verification evidence.
5. **Main agent**: updates `plan.md` and leaves a durable handoff.

Parallel explorers are allowed for independent read-only work. Writers remain serial for schema, migration state, Directus clients, reconciliation, ledger, and shared frontend contracts.

After three failed loops or evidence of a wrong direction, stop and return to the last read-only checkpoint with a narrower prompt.

## Mandatory context for every loop

Read:

- `AGENTS.md`;
- `CONTEXT.md`;
- ADR 0001;
- migration `README.md`;
- `specification.md`;
- `plan.md`;
- the relevant section of `runbook.md`.

Every task must report `production_artifact_impact`. `unknown` is a stop condition.

## Task A — Read-only discovery

Purpose: document the current WordPress, Directus, importer, schema, route, and gallery contracts.

Type: explorer-only first; documentation worker may follow.

Allowed files:

- `docs/migrations/wordpress-to-directus/**`;
- `CONTEXT.md` when a durable fact changes.

Forbidden:

- importer code;
- schema apply;
- Directus data writes;
- permissions and credentials;
- `homelab` changes;
- generated inventories in Git.

Verification:

- documentation links resolve;
- every finding cites a repository path, API response, or controlled run artifact;
- no repository code or production data changed.

Prompt:

```text
usa agent-loop per il Task A: discovery read-only della migrazione WordPress-to-Directus.
Explorer only: inventaria schema Directus, tipi WordPress, categorie, gallery,
route frontend e comportamento dell'importer esistente.
Non modificare codice, dati, schema, permessi o homelab.
Restituisci findings, risks, allowed_files, forbidden_files,
verification, production_artifact_impact e open_questions.
```

Stop when source/target environment identity is unclear or discovery would require a write.

## Task B — Inventory contracts and read-only clients

Purpose: implement fresh, paginated, deterministic source and target inventories.

Type: explorer, then one serial worker slice at a time.

Candidate allowed files:

- new modules under `cms/utils/wordpress/` dedicated to inventory;
- focused tests under `cms/utils/wordpress/tests/`;
- migration documentation.

Forbidden:

- legacy update/delete helpers;
- Directus schema;
- frontend files;
- production data;
- `parser.yaml` mutation;
- AI formatter files.

Required behavior:

- no stale cache by default;
- complete pagination and count validation;
- canonical hashes;
- read-only credentials;
- explicit source errors;
- no content or inventory artifacts committed.

Suggested verification:

```text
uv run pytest tests/test_inventory.py
uv run python -m compileall .
```

Stop if a target inventory needs broad administrator access or cannot include all statuses and relations in scope.

## Task C — Baseline verifier

Purpose: define and test immutable target baseline fingerprints and comparison.

Type: serial worker after inventory contracts pass.

Allowed:

- new baseline/fingerprint modules;
- focused tests;
- specification and runbook clarifications.

Forbidden:

- target writes;
- schema changes;
- deletion or cleanup;
- production baseline files in Git.

Required tests:

- stable canonical hashing;
- order-independent hashing where order is not semantic;
- order-sensitive relation hashing for galleries;
- added target objects do not alter protected-object fingerprints;
- changed or missing protected objects fail verification.

Stop if canonicalization would hide a meaningful content, cover, category, folder, file, or relation change.

## Task D — Reconciliation engine

Purpose: classify source and target records without producing writes.

Type: explorer, then serial worker.

Allowed:

- reconciliation modules and tests;
- report schemas;
- migration docs.

Forbidden:

- Directus write calls;
- automatic update or delete states;
- modifying `parser.yaml`;
- treating title or slug alone as a match;
- production execution.

Required tests:

- accepted ledger match;
- exact unique URL match;
- valid and stale historical mapping;
- target drift classified as protected;
- ambiguous match classified for manual review;
- route collision blocks creation;
- target-only object remains protected;
- only `create_candidate` can enter a write manifest.

Suggested verification:

```text
uv run pytest tests/test_reconciliation.py
```

Stop if a rule could classify an existing edited Directus article as a write target.

## Task E — Append-only ledger design

Purpose: design provenance storage without modifying protected feed or file rows.

Type: architecture explorer, documentation/fixture worker, reviewer; schema apply is a later separately approved action.

Allowed initially:

- ADR follow-up when a real new trade-off emerges;
- schema proposal or snapshot fixture under a dedicated docs/schema location;
- ledger tests against local or disposable staging.

Forbidden initially:

- production schema apply;
- backfill into existing `feeds` or `directus_files` rows;
- mutable or deletable ledger semantics;
- secrets and production tokens.

Required decisions:

- collection names and fields;
- append-only enforcement;
- supersession model;
- run identity;
- mapping of pre-existing protected and migration-created objects;
- permissions and audit visibility.

Stop before any schema or permission action and request explicit approval with the exact proposal and rollback implications.

## Task F — Create-only client and executor

Purpose: implement the only approved write path for new articles and media.

Type: serial, test-first worker slices.

Allowed:

- a new create-only Directus client;
- request-method guard;
- immutable write-manifest reader;
- article/media creation modules;
- focused tests and docs.

Forbidden:

- modifying the legacy mutable client to make production execution easier;
- `PATCH`, `PUT`, or `DELETE`;
- slug-based upsert;
- overwrite flags;
- field-dropping or truncation fallback;
- AI formatting;
- automatic publication;
- production execution.

Required tests:

- dry-run emits no write;
- method guard rejects forbidden methods before network use;
- endpoint allowlist rejects unexpected paths;
- existing match stops creation;
- media validation and checksum;
- feed created once with final payload as draft;
- partial media failure creates no feed;
- ambiguous response stops safely;
- completed ledger identity creates nothing on rerun.

Suggested verification:

```text
uv run pytest tests/test_create_only_client.py tests/test_article_import.py
```

Stop if a workflow requires updating the newly created feed after media upload. Redesign it so the final feed is created once.

## Task G — Gallery migration and legacy fallback

Purpose: import new ordered galleries without changing existing gallery behavior.

Type: explorer for source/schema/frontend, then sequential workers for schema proposal, importer, and frontend.

Candidate allowed files by slice:

- gallery discovery/import modules and tests;
- `lib/types.ts` and focused server helpers;
- `components/gallery.tsx` or a new gallery component;
- a new gallery listing route;
- migration docs.

Forbidden:

- modifying existing Directus gallery files or folders;
- removing the folder-by-slug fallback;
- sorting new galleries by filename instead of source order;
- combining schema apply, importer, and frontend behavior in one worker task;
- production execution.

Required tests:

- REST type discovery and fallback discovery;
- source order preserved;
- duplicate filenames remain distinct source entries when required;
- missing required image blocks album completion;
- existing folder-based gallery renders unchanged;
- new relation-based gallery renders in stored order.

Stop before schema apply and request explicit approval.

## Task H — Permission and staging rehearsal

Purpose: prove the same create-only permission model and code are safe before production.

Type: operator task after implementation PRs are accepted.

Allowed:

- staging-only role and token setup after approval;
- staging inventory, import, and verification;
- run artifacts outside Git;
- documentation handoff.

Forbidden:

- production writes;
- broad admin token;
- automatic cleanup;
- changing code during the rehearsal without returning to a worker PR.

Required evidence:

- permission report;
- dry-run zero writes;
- first run expected creations;
- protected baseline unchanged;
- second run zero creations;
- no forbidden methods;
- asset and gallery verification.

Stop on the first protected-object difference.

## Task I — Production readiness review

Purpose: assemble a go/no-go packet. It does not execute the migration.

Type: explorer/reviewer only.

Required packet:

- accepted code commit;
- backup and storage evidence;
- source inventory hash;
- target baseline hash;
- reconciliation and write-manifest hashes;
- permission report;
- staging rehearsal report;
- known failures and exclusions;
- exact operator procedure and stop conditions.

The reviewer returns `GO`, `NO-GO`, or `GO WITH EXPLICITLY LISTED EXCLUSIONS`. Anything else is no-go.

## Task J — Production execution

Purpose: execute the exact approved write manifest.

Type: human-supervised operator task. Agent may assist only within the approved runbook.

Requirements:

- explicit approval in the current session;
- exact manifest hash;
- current backup, source, target, and permission checks;
- production dry-run;
- serial execution;
- immediate stop on invariant failure;
- post-run independent verification.

No agent may infer production approval from merged code, an accepted ADR, a staging success, or this task card.

## Handoff template

```yaml
files_inspected: []
files_changed: []
findings: []
verification: []
production_artifact_impact: none | described
risks: []
open_questions: []
next_action: ""
```

For worker tasks also include:

```yaml
allowed_files: []
forbidden_files: []
test_command: ""
stop_conditions: []
```

## Reviewer checklist

The reviewer must explicitly answer:

1. Could this change update or delete a protected feed, file, folder, or relation?
2. Could stale cache or historical mapping bypass current target validation?
3. Can any runtime path emit a forbidden HTTP method?
4. Can a source-target difference become an update?
5. Can ambiguous identity become automatic creation?
6. Are retries idempotent under uncertain network outcomes?
7. Are new feeds drafts and publication separate?
8. Are generated inventories and credentials kept outside Git?

Any uncertain answer blocks completion.
