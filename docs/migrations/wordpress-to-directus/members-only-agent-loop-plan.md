# Members-only migration agent-loop plan

Status: ready for read-only execution

Date: 2026-06-22

## Purpose

This plan breaks the `/soci` and `articoli-tecnici` migration into bounded
agent-loop tasks. It is designed to maximize safe parallel read-only work while
keeping schema, auth, import, and production actions serial and explicitly
approved.

This plan does not authorize production writes, Directus schema changes,
permission changes, FTP transfers, or publication.

## Governing decisions

- Existing Directus artifacts are protected and target-authoritative.
- The members-only area is separate from public `feeds` and public categories.
- Initial members-only migration is faithful to WordPress; reorganization is a
  later editorial project.
- `member_feeds.content` stores sanitized HTML, not Markdown.
- `articoli-tecnici` is treated as a source implementation name, not as the
  default public URL label. The public `/soci` category/route name must be
  derived from source evidence. If the collection represents translations of a
  specific magazine or publication, use the proven publication name for the
  category slug instead of `articoli-tecnici`.
- WordPress users are a one-time bootstrap source; Directus becomes
  authoritative after migration.
- Directus auth plus a temporary Next.js/API legacy-password bridge is the
  accepted auth direction.
- Generated inventories, media lists, credentials, transfer logs, downloaded
  files, and private content stay outside Git.

## Common run context

Every loop reads:

- `AGENTS.md`
- `CONTEXT.md`
- `docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md`
- `docs/adr/0002-use-directus-auth-with-temporary-wordpress-password-bridge.md`
- `docs/migrations/wordpress-to-directus/README.md`
- `docs/migrations/wordpress-to-directus/specification.md`
- `docs/migrations/wordpress-to-directus/members-only-spec.md`
- `docs/migrations/wordpress-to-directus/media-retrieval-report.md`
- `docs/migrations/wordpress-to-directus/runbook.md`
- `docs/migrations/wordpress-to-directus/agent-loop.md`

Current local source export:

- encrypted: `secrets/migration/wordpress-db.20260622.sql.sops.yaml`
- plaintext working copy: `/tmp/cap-migration-runs/20260622-members-only-source/wordpress-db.sql`

Plaintext SQL is sensitive and must not be committed.

## Model routing and parallelization strategy

Use parallel agents only for read-only exploration or disjoint file writes.
Route each task by risk:

- Use `5.5` for the main agent, reviewer decisions, production schema apply,
  auth/session/password work, permission design, recovery planning, and any task
  that can affect production state.
- Use `5.4` for bounded local code, tests, and documentation workers when the
  task does not touch production writes, auth, schema recovery, token handling,
  or permission boundaries.
- Use `5.4-mini` only for read-only explorers: log parsing, JSONL summaries,
  aggregate SQL counts, grep-style inventory, report/table generation, and
  artifact checks.
- Escalate immediately from `5.4-mini` to `5.5` when an explorer finds
  ambiguity, Directus drift, partial schema state, unexpected API responses,
  permission mismatch, source/target collision, or private-data handling risk.
- Keep the current schema-apply recovery after the `POST /relations` `500`
  under `5.5`. Cheaper agents may only summarize audit files and live state in
  read-only mode.

| Work type | Agent role | Model profile | Parallel? | Reason |
| --- | --- | --- | --- | --- |
| Docs/source inspection | explorer | `5.4-mini` | yes | Low-risk grep/read tasks. |
| SQL export structure inventory | explorer | `5.4-mini` | yes | Deterministic table/column/count analysis. |
| Membership and role inference | explorer | `5.5` | yes | Requires cautious interpretation of plugin/capability evidence. |
| Directus current-state inventory | explorer | `5.4-mini` for GET-only summaries; `5.5` on drift | yes, read-only | Independent GET-only target evidence, escalated on mismatch. |
| Parser implementation | worker | `5.4` | no | Shared code/tests; keep serial. |
| Auth bridge prototype | worker | `5.5` | no | Sensitive auth/security path. |
| Schema proposal | explorer/reviewer | `5.5` | no | Domain and permission consequences. |
| Schema apply or recovery | operator/reviewer | `5.5` | no | Production schema state and failure recovery. |
| Media retrieval via FTP/rclone | operator | `5.5` for credentials and execution; `5.4-mini` for post-transfer summaries | no | External credentials and transfer side effects. |
| Production import | operator/reviewer | `5.5` | no | Explicit approval and invariant verification required. |

When a tool exposes requested/effective model, every handoff must record it.
When it does not, record `model_effective: unknown`.

## Stop conditions

Stop and ask before continuing when:

- a task needs Directus schema apply, role creation, token creation, or
  permission changes;
- a task needs FTP/SFTP credentials or starts network transfer;
- a task would write to production Directus;
- a task would update, delete, rename, move, replace, or re-relate existing
  Directus artifacts;
- a membership rule cannot be proven from WordPress roles/capabilities/plugin
  data;
- a media match is based only on ambiguous filename evidence;
- a parser would need to print or commit private content, emails, password
  hashes, SQL rows, media lists, or downloaded files;
- a gallery migration cannot preserve source order;
- three agent-loop attempts fail or drift for the same task.

## Phase 1: Parallel read-only evidence

These explorers can run in parallel because they only inspect repository files
or the local SQL export and write no production state.

### Task 1A: SQL export structure and content-scope inventory

Role: explorer

Model profile: economical/fast

Allowed files:

- no writes required
- run artifacts under `/tmp/cap-migration-runs/<run-id>/`

Forbidden:

- repository writes
- Directus writes
- network access
- printing SQL rows or private content

Goal:

Identify tables, columns, post types, statuses, taxonomies, and safe aggregate
counts relevant to `/soci`, especially `articoli-tecnici`.

Verification:

- report only aggregate counts and table/column names;
- state plaintext SQL path and SHA-256 if used;
- `production_artifact_impact: none`.

Prompt:

```text
usa agent-loop explorer per Task 1A.
Leggi i documenti comuni del piano members-only.
Analizza in sola lettura il dump SQL locale:
/tmp/cap-migration-runs/20260622-members-only-source/wordpress-db.sql

Obiettivo: produrre un handoff aggregato su tabelle, colonne, post type,
status, tassonomie, categorie e conteggi legati ad articoli-tecnici e /soci.

Allowed: solo lettura repo e dump SQL, artifact in /tmp se necessari.
Forbidden: stampare righe SQL, email, password hash, contenuti articolo,
URL media completi, scrivere in Directus, modificare repo.

Restituisci files_inspected, files_changed, findings, verification,
production_artifact_impact, risks, open_questions, next_action.
```

### Task 1B: Membership and user-role evidence inventory

Role: explorer

Model profile: higher reasoning

Allowed files:

- no writes required
- run artifacts under `/tmp/cap-migration-runs/<run-id>/`

Forbidden:

- printing users, emails, password hashes, serialized raw usermeta, or SQL rows
- deciding final role mappings without evidence

Goal:

Determine how WordPress identifies members, redazione, pubblicazione, and
ordinary users using roles, capabilities, plugin tables, options, usermeta, and
MailPoet/UsersWP evidence.

Verification:

- aggregate counts by discovered role/capability only;
- list uncertain mechanisms as open questions;
- no private identifiers in output.

Prompt:

```text
usa agent-loop explorer per Task 1B.
Leggi i documenti comuni del piano members-only.
Analizza in sola lettura utenti, usermeta, options e tabelle plugin dal dump SQL.

Obiettivo: capire il meccanismo WordPress per soci, redazione e pubblicazione.
Produci solo conteggi aggregati per ruolo/capability/plugin evidence e una
proposta conservativa di classificazione.

Forbidden: stampare email, user_login, hash password, righe SQL, usermeta raw,
contenuti privati, modificare repo, scrivere in Directus.

Se la membership non è dimostrabile, fermati e segnala quale export/evidenza
serve. Restituisci handoff completo agent-loop.
```

### Task 1C: Existing Directus file/content coverage inventory

Role: explorer

Model profile: standard

Allowed files:

- no writes required
- generated inventories only under `/tmp/cap-migration-runs/<run-id>/`

Forbidden:

- Directus `POST`, `PATCH`, `PUT`, `DELETE`
- schema or permission changes
- committing inventories

Goal:

Capture a fresh read-only target view of files, folders, feeds, and candidate
members-only collections if they already exist.

Prerequisite:

Requires a read-only Directus token or confirmed anonymous endpoint coverage.
If unavailable, stop and ask.

Verification:

- HTTP methods limited to `GET`/`HEAD`;
- run artifact hashes recorded outside Git;
- `production_artifact_impact: none`.

Prompt:

```text
usa agent-loop explorer per Task 1C.
Leggi i documenti comuni del piano members-only.
Prima prova accesso anonimo read-only a Directus, poi usa token read-only solo
se disponibile e necessario.

Obiettivo: inventariare files, folders, feeds e presenza/assenza di collection
member_* senza scritture.

Allowed: GET/HEAD soltanto, artifact in /tmp.
Forbidden: POST/PATCH/PUT/DELETE, schema, permessi, commit di inventory.

Se non c'è token read-only sufficiente, fermati e chiedi.
Restituisci handoff agent-loop con metodi usati e artifact hash.
```

### Task 1D: Publication-name and route-label discovery

Role: explorer

Model profile: higher reasoning

Allowed files:

- no writes required
- run artifacts under `/tmp/cap-migration-runs/<run-id>/`

Forbidden:

- choosing `articoli-tecnici` as the user-facing URL without checking source
  evidence
- inventing a publication name from title similarity alone
- printing article bodies or private content

Goal:

Determine whether the WordPress `articoli-tecnici` custom post type represents
translations from a specific magazine/publication and identify the best
user-facing `/soci/<categoria>` slug.

Evidence to inspect:

- WordPress custom post type labels from options/plugin metadata when present;
- menu items and page links pointing to `articoli-tecnici`;
- taxonomy labels for `argomento`;
- recurring publication names in titles or excerpts as aggregate evidence only;
- existing WordPress routes for the custom post type.

Verification:

- proposed slug is backed by at least two independent source clues, or the task
  returns `unresolved`;
- no private article text is printed;
- `production_artifact_impact: none`.

Prompt:

```text
usa agent-loop explorer per Task 1D.
Leggi i documenti comuni del piano members-only.
Verifica se il custom post type WordPress articoli-tecnici corrisponde a una
rivista/pubblicazione specifica. Cerca evidenze in options, menu, post type
metadata, tassonomie, rotte e aggregati dei titoli senza stampare contenuti.

Obiettivo: proporre il nome e lo slug pubblico per /soci/<categoria> oppure
restituire unresolved se non è dimostrabile. Non usare articoli-tecnici come
label pubblico senza prova che sia la scelta corretta.

Forbidden: stampare body articoli, dati utenti, righe SQL, scrivere repo,
scrivere Directus.
Restituisci handoff agent-loop completo.
```

## Phase 2: SQL inventory tooling

Serial worker. Do not start until Phase 1A has a stable source contract.

### Task 2A: SQL export parser and tests

Role: worker

Model profile: standard

Allowed files:

- `cms/utils/wordpress/inventory/sql_export.py`
- `cms/utils/wordpress/inventory/__init__.py`
- `cms/utils/wordpress/inventory/__main__.py`
- `cms/utils/wordpress/tests/test_sql_export_inventory.py`
- `docs/migrations/wordpress-to-directus/members-only-agent-loop-plan.md`
- `docs/migrations/wordpress-to-directus/plan.md`

Forbidden:

- modifying legacy mutable importer execution paths
- reading live Directus
- committing generated SQL-derived reports
- printing private rows

Goal:

Implement a deterministic read-only SQL export inventory command that can emit
non-sensitive JSON/JSONL artifacts outside Git for:

- `articoli-tecnici` records;
- source-backed publication/category label candidates;
- required original media paths;
- taxonomy/category relationships;
- aggregate user/role evidence;
- source hashes without exposing content in Git.

Verification command:

```bash
cd cms/utils/wordpress
uv run pytest tests/test_sql_export_inventory.py
```

Stop if parsing requires a real MySQL import or if privacy-safe output cannot
be guaranteed.

## Phase 3: Local source reports

Serial worker after Task 2A.

### Task 3A: Generate `/soci` source inventory artifacts

Role: worker/operator

Model profile: standard

Allowed files:

- no repo writes unless updating documentation/handoff
- artifacts under `/tmp/cap-migration-runs/<run-id>/`

Forbidden:

- committing generated artifacts
- Directus writes
- FTP/SFTP transfer

Goal:

Generate current source artifacts for:

- `articoli-tecnici` article inventory;
- required media list;
- category/taxonomy report;
- membership evidence aggregate report;
- artifact SHA-256 sidecars.

Verification:

- artifact files exist outside Git;
- checksums recorded in a handoff;
- no private rows printed in final response.

## Phase 4: Reconciliation before media transfer

Task 4A can run after Task 1C and Task 3A complete.

### Task 4A: Reconcile `articoli-tecnici` media against Directus files

Role: worker/reviewer

Model profile: standard

Allowed files:

- reconciliation modules/tests if needed;
- docs handoff updates;
- artifacts under `/tmp/cap-migration-runs/<run-id>/`

Forbidden:

- Directus writes
- using filename-only match as proof
- committing media lists

Goal:

Classify required media as already present, ambiguous filename match,
missing, or unresolved.

Verification:

- every source media path has exactly one classification;
- ambiguous matches are review items, not reuse authorizations;
- output stays outside Git.

## Phase 5: Media retrieval

External operation. Requires user-provided FTP/SFTP access and explicit approval
before starting transfer.

### Task 5A: Retrieve missing source originals

Role: operator

Model profile: standard

Allowed:

- `rclone copy` or equivalent targeted transfer using `--files-from`
- transfer artifacts under `/tmp/cap-migration-runs/<run-id>/`

Forbidden:

- committing credentials, rclone config, transfer logs, media lists, or files
- downloading all uploads unless explicitly approved
- Directus upload

Goal:

Download only missing `articoli-tecnici` originals and compute checksums.

Stop condition:

No FTP/SFTP credentials or explicit transfer approval.

## Phase 6: Schema and auth design

These are design/review tasks first. Schema apply and permission changes are
separate explicit approval gates.

### Task 6A: Directus schema proposal for members content

Role: explorer/reviewer

Model profile: higher reasoning

Allowed files:

- docs/schema proposal under `docs/migrations/wordpress-to-directus/`
- ADR only if a new durable trade-off appears

Forbidden:

- applying schema
- changing production permissions
- frontend implementation

Goal:

Propose fields, relations, policies, and access semantics for:

- `member_feeds`
- `member_categories`
- optional `member_galleries`
- `legacy_wordpress_credentials`

The proposal must preserve HTML content, source provenance, member visibility,
and editorial workflow separation.

### Task 6B: Legacy password bridge prototype plan

Role: explorer/worker after approval

Model profile: higher reasoning

Allowed initially:

- tests with synthetic hashes only
- Next.js/API auth code only after schema/storage decisions are approved

Forbidden:

- real WordPress hashes in tests or repo
- exposing legacy credential collection to frontend
- changing production Directus users

Goal:

Prototype verification for supported WordPress hash formats and Directus
password upgrade flow using synthetic fixtures.

## Phase 7: Frontend `/soci`

Serial after schema/auth design is accepted.

### Task 7A: Authenticated `/soci` route prototype

Role: worker

Model profile: standard

Allowed files:

- `app/soci/**`
- focused auth/session helpers
- focused tests

Forbidden:

- changing public article routes
- bypassing backend permissions in UI only
- exposing private content to anonymous users

Goal:

Implement:

- `/soci`
- `/soci/<categoria>/<slug>`
- login redirect with return URL
- simple 403 for authenticated non-members
- HTML rendering for `member_feeds.content`

## Phase 8: Import rehearsal and production

Human-supervised operator tasks only.

### Task 8A: Staging rehearsal

Requires:

- approved schema;
- approved permissions;
- source inventory hash;
- target baseline hash;
- approved write manifest;
- retrieved media checksums.

Verification:

- dry-run emits zero writes;
- first staging run creates only expected migration-owned objects;
- protected baseline unchanged;
- second staging run creates zero objects.

### Task 8B: Production readiness and execution

Requires explicit current-session approval and exact manifest hash.

No agent may infer production approval from this plan, from completed code, or
from staging success.

## Suggested immediate execution order

1. Run Task 1A, Task 1B, and Task 1D in parallel.
2. Run Task 1C in parallel only if a read-only Directus token is available.
3. Integrate explorer handoffs and narrow scope.
4. Run Task 2A as the first worker.
5. Generate Task 3A artifacts.
6. Stop for review before any FTP/SFTP transfer or Directus schema work.

## Main-agent integration checklist

For every completed loop:

- verify `production_artifact_impact` is not `unknown`;
- inspect files changed before accepting worker output;
- run the focused verification command;
- update `docs/migrations/wordpress-to-directus/plan.md`;
- leave a handoff with artifact paths and hashes;
- commit documentation/code separately from generated run artifacts.
