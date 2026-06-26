# WordPress to Directus migration plan

Status: active planning and implementation

Last updated: 2026-06-19

This is the canonical binary plan. Every checkbox is either completed (`[x]`) or still required (`[ ]`). Do not use partial states. Split partially completed work into one closed task and one or more open tasks.

## Current active task

- [ ] Task B3 — implement gallery REST-type discovery and the ordered public-HTML fallback parser.

## Task B slice status

- [x] Task B1 — common manifest records, canonical JSON, SHA-256 hashing, explicit inventory issues, and strict pagination contracts with synthetic-data tests.
- [x] Task B2 — fresh WordPress read-only client for post types, categories, published posts, media, content-media URL discovery, and complete pagination.
- [ ] Task B3 — gallery REST discovery and ordered public-HTML fallback parser.
- [ ] Task B4 — Directus read-only client for runtime metadata, schema metadata, feeds, categories, files, folders, and relevant relations.
- [ ] Task B5 — generated frontend route inventory and collision metadata.
- [ ] Task B6 — read-only CLI commands, controlled artifact output, and integrated synthetic-data tests.

## Next up

1. Gallery source discovery.
2. Directus read-only client.
3. Generated route inventory.

## Phase 0 — Governance and scope

- [x] Document the additive-only, target-authoritative decision in ADR 0001.
- [x] Add repository instructions for agent-assisted migration work.
- [x] Add compact repository and migration context.
- [x] Define normative specification, plan, runbook, and agent-loop task cards.
- [x] Review and merge the documentation PR, accepting ADR 0001 as the governing production invariant.
- [ ] Confirm the final WordPress category-to-target-category precedence for articles.
- [x] Confirm that newly imported feeds remain draft until editorial review.
- [ ] Confirm the operator and reviewer roles for baseline, reconciliation, and production approval.

Exit gate: documentation is reviewed and no unresolved decision changes the safety model.

## Phase 1 — Read-only discovery

- [x] Infer the Directus collections, fields, and relations currently consumed by the application without treating inference as an authoritative schema snapshot.
- [ ] Inventory the current Directus schema, field types, constraints, relations, states, and readable permissions with a strict read-only identity.
- [ ] Record the exact production Directus version and immutable image digest.
- [x] Inventory public WordPress archives, known historical category IDs, and overlapping category behavior.
- [ ] Inventory WordPress REST types, categories, post/media totals, and complete pagination through the Task B client.
- [x] Verify that public gallery albums are available through `/gallery/` and `/dt-gallery/<slug>/` HTML routes.
- [ ] Determine whether the gallery custom post type is exposed through WordPress REST or requires export/public-HTML fallback.
- [x] Inventory frontend routes and identify global slug and route collision rules.
- [x] Document the current production gallery behavior and legacy exact-folder-name fallback contract.
- [x] Review `parser.yaml` as historical evidence and document why it cannot be target authority.
- [ ] Validate historical mappings against the current Directus target during reconciliation inventory.
- [x] Produce the read-only discovery report with open questions and no production writes.

Exit gate: source and target contracts are known well enough to design deterministic inventories. Authenticated runtime facts are completed by the read-only inventory client before baseline approval.

## Phase 2 — Safety controls and tests

- [x] Introduce a guarded read-only HTTP client reusable by source and target inventory clients.
- [ ] Add a create-only Directus client separated from the legacy mutable client.
- [x] Add a method allowlist that rejects every method except `GET` and `HEAD` before network transmission.
- [ ] Add a test proving dry-run sends no non-read request.
- [ ] Add a test proving protected target records cannot enter a write manifest.
- [ ] Add a test proving ambiguous matches fail closed.
- [ ] Add a test proving broad permissions or missing permission evidence stop execution.
- [ ] Remove stale-cache dependence from new migration commands.
- [ ] Keep legacy delete and overwrite commands outside the approved execution path.

Exit gate: automated tests enforce the production invariant before a write path exists.

## Phase 3 — Target baseline

- [ ] Define the baseline manifest schema and canonical hashing rules.
- [ ] Inventory all feeds, files, folders, and relevant relations in scope.
- [ ] Record file checksums where accessible and metadata fingerprints otherwise.
- [ ] Include all statuses, not only published content.
- [ ] Record baseline timestamp, target URL, Directus version, schema hash, and inventory hash.
- [ ] Validate counts and pagination independently.
- [ ] Store the production baseline as a controlled run artifact, not in Git.
- [ ] Obtain explicit human approval of the baseline.

Exit gate: every existing in-scope target object is represented as a protected artifact.

## Phase 4 — Source inventory

- [x] Define the generic source manifest schema and canonical hashing rules.
- [ ] Fetch all approved posts with complete pagination and no stale cache.
- [x] Implement capture of categories, featured media, inline media, linked files, dates, and source hashes.
- [ ] Discover all public gallery albums and ordered images.
- [ ] Resolve original media URLs without mutating source or target.
- [x] Record malformed source records as explicit inventory issues rather than silently omitting them.
- [ ] Validate source counts against WordPress totals and archive pages.
- [ ] Store the source inventory as a controlled run artifact.

Exit gate: every source record in scope is inventoried or explicitly classified as an error.

## Phase 5 — Reconciliation and approval

- [ ] Implement the reconciliation states defined in the specification.
- [ ] Match accepted ledger entries first.
- [ ] Validate exact `original_uri` matches.
- [ ] Revalidate historical YAML mappings against the current target.
- [ ] Treat slug/title/date/category similarity as manual-review evidence only.
- [ ] Detect route, slug, source identity, and target identity collisions.
- [ ] Classify source-target drift as protected, never as an update candidate.
- [ ] Produce a human-readable and machine-readable reconciliation report.
- [ ] Review every `manual_review_candidate` and `conflict`.
- [ ] Generate an immutable write manifest containing only approved `create_candidate` items.
- [ ] Hash and approve the write manifest.

Exit gate: every proposed write is a new object with unambiguous evidence and explicit approval.

## Phase 6 — Append-only ledger and Directus permissions

- [ ] Design the append-only ledger schema and supersession model.
- [ ] Review the schema design separately before applying it.
- [ ] Apply schema changes only after explicit production approval.
- [ ] Create a dedicated Directus migration role and identity with read/create-only permissions.
- [ ] Prove the identity cannot update or delete feeds, files, folders, relations, or ledger rows.
- [ ] Record role and permission verification in the run artifacts without storing credentials.
- [ ] Add ledger integration tests for pre-existing and migration-created mappings.

Exit gate: production identity and provenance storage enforce the additive-only model.

## Phase 7 — Create-only article and media importer

- [ ] Download media with TLS verification, limits, MIME checks, and checksums.
- [ ] Upload only to migration-owned folders.
- [ ] Preserve source HTML except documented deterministic sanitization and URL rewriting.
- [ ] Use the WordPress featured image as cover when available and valid.
- [ ] Create each new feed once with final content and cover.
- [ ] Create feeds as draft.
- [ ] Record every created file, folder, feed, relation, and checksum in the ledger.
- [ ] Stop on schema validation rather than dropping or truncating fields.
- [ ] Stop on ambiguous network outcomes.
- [ ] Add unit and integration tests for success, retry, collision, partial failure, and rerun behavior.

Exit gate: a second run over the same accepted manifest creates zero objects.

## Phase 8 — Gallery implementation

- [ ] Finalize the ordered gallery relation design for new galleries.
- [ ] Preserve the folder-by-slug fallback for existing production galleries.
- [ ] Add schema changes in a separate reviewed task.
- [ ] Implement source-order preservation and explicit cover selection.
- [ ] Implement gallery inventory, reconciliation, and ledger entries.
- [ ] Add frontend rendering for ordered relations with legacy fallback.
- [ ] Add tests for album order, missing images, duplicate filenames, and legacy galleries.

Exit gate: new albums preserve source order and existing gallery rendering remains unchanged.

## Phase 9 — Staging rehearsal

- [ ] Restore or clone an approved target snapshot into staging.
- [ ] Use the same schema, code, permission model, and write manifest intended for production.
- [ ] Capture a staging baseline.
- [ ] Run dry-run and confirm zero writes.
- [ ] Execute the create-only import.
- [ ] Verify all protected staging fingerprints are unchanged.
- [ ] Verify new records, media, routes, and gallery order.
- [ ] Rerun and confirm zero additional creations.
- [ ] Review logs for forbidden methods or endpoints.
- [ ] Produce and approve the staging rehearsal report.

Exit gate: the complete process passes twice without changing protected artifacts.

## Phase 10 — Production readiness and execution

- [ ] Confirm the source has not changed since the approved inventory, or regenerate reconciliation.
- [ ] Confirm the target has not changed since the approved baseline, or capture and approve a new baseline.
- [ ] Verify the latest CNPG backup completed successfully.
- [ ] Verify upload-volume protection and available capacity.
- [ ] Verify create-only permissions immediately before execution.
- [ ] Obtain explicit production approval for the exact manifest hash.
- [ ] Run production dry-run.
- [ ] Execute writes serially with a unique run ID.
- [ ] Stop immediately on any invariant failure or unexpected request.
- [ ] Preserve logs, ledger entries, counts, and hashes.

Exit gate: execution completed without forbidden methods, mutations, or unresolved outcomes.

## Phase 11 — Post-run verification and publication

- [ ] Re-inventory the target after the run.
- [ ] Prove every protected baseline object still exists.
- [ ] Prove protected row, relation, and file fingerprints are unchanged.
- [ ] Prove every created object is linked to the run ledger.
- [ ] Verify asset availability, content integrity, category, cover, and route behavior.
- [ ] Run a fresh reconciliation and confirm no completed source identity is proposed again.
- [ ] Produce a signed-off migration report with failures and manual-review items.
- [ ] Review newly created drafts editorially.
- [ ] Publish approved drafts through a separate explicit operation.
- [ ] Keep WordPress online until content, routes, and redirects are independently accepted.

Exit gate: migration evidence is complete and publication is an independent reviewed decision.

## Production execution note — 2026-06-26

The narrowed public production execution was approved and started from commit
`b5d1534`. All pre-execution gates passed, including same-moment fresh target
absence.

The run stopped on the first unexpected Directus error:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-recovered-20260625T164519Z/production-execution-20260626T074914Z
execution_status: stopped_on_first_error
executed_operation_count: 5
failed_sequence: 6
failed_source_identity: wordpress:post:5786
failed_slug: 31-raduno-cap-toscana
failure_status: HTTP 400 Bad Request
```

Created draft feeds:

```text
402 wordpress:post:2715 draft
403 wordpress:post:2734 draft
404 wordpress:post:2740 draft
405 wordpress:post:2755 draft
406 wordpress:post:3957 draft
```

The created drafts are now migration-created artifacts and must be treated as
protected for any continuation. Do not rerun the original 28-item manifest.
Investigate the HTTP 400 for `wordpress:post:5786`, then prepare a continuation
manifest only for remaining uncreated items.

Root cause identified on 2026-06-26:

```text
feeds.description is varchar(500)
wordpress:post:5786 generated description length is 674
```

Only `wordpress:post:5786` violates this limit in the 28-item request plan.
Continuation is blocked until an explicit decision is made:

- widen `feeds.description` to `text` through a separately approved schema task;
- add an explicit deterministic description/excerpt transformation;
- exclude `wordpress:post:5786` from automated continuation and handle it
  manually.

Decision applied on 2026-06-26:

```text
feeds.description widened from varchar(500) to varchar(750)
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/feeds-description-schema-750-20260626T080446Z
post_apply_status: approved
manifest descriptions over 750: 0
```

Continuation can now be planned for the remaining uncreated items only. The 5
already-created draft feeds remain protected migration-created artifacts.

Single-item continuation applied on 2026-06-26:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/post-5786-single-retry-20260626T081720Z
source_identity: wordpress:post:5786
target_id: 407
target_status: draft
```

Protected migration-created drafts now include:

```text
402 wordpress:post:2715 draft
403 wordpress:post:2734 draft
404 wordpress:post:2740 draft
405 wordpress:post:2755 draft
406 wordpress:post:3957 draft
407 wordpress:post:5786 draft
```

Any continuation manifest must exclude these 6 created drafts.

Continuation gate prepared on 2026-06-26:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-continuation-after-407-20260626T145957Z
operation_count: 22
create_feed_draft: 15
create_gallery_draft: 7
manifest_sha256: 82d572a82e369da8fa1a69fc31c3e1129775e874d7cf62084b224c86301f2a76
approval_sha256: 7f1fa7ad7d96ff95e82a9829399742186ef8108ee640443b7d7a468b5a336a0a
```

The continuation excludes the 6 already-created draft feeds. The local
executor profile is `continuation_after_407_20260626T145957Z`.

Dry-run and pre-create gates:

```text
dry_run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-continuation-after-407-20260626T145957Z/dry-run-20260626T150051Z
dry_run_status: passed
dry_run_post_requests_sent: 0
planned_methods: POST
planned_endpoints: /items/feeds
request_plan_sha256: b6443b8bb8c3e30d3ff48b15a0b687107eeb64534c380e8df2bc89bae840d68f
permission_evidence_sha256: 290fe70e8b5e83f63622e45599333919c0634c035f9ede501fa7c9e0e38f7eb1
fresh_target_absence_sha256: fc9544bb83421110e37cbe08ac64ee33fee05747f88940055609fe57afd939e7
fresh_target_absence_status: approved
fresh_target_absence_get_requests: 44
```

No production `POST` was run for this 22-item continuation. Production
continuation remains blocked until explicit approval is given for the exact
manifest hash above.

Production continuation executed on 2026-06-26 after explicit approval:

```text
execution_run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-continuation-after-407-20260626T145957Z/production-execution-20260626T150859Z
execution_status: completed
executed_operations: 22
created_target_ids: 408-429
post_endpoints: /items/feeds
forbidden_methods_sent: none
post_execution_verification_status: approved
```

Execution artifact hashes:

```text
validation_report.json: 01ecfcbb0e6f96e814a0341eec20c38713305b5644c5199876188ff5cd884de8
request_plan.json: d1427fc7765232141b2748986c3ad237053ab96d395b81fd352f7ca7816d5ee2
dry_run_report.json: 885a7aada20b901ab98a4cc3621dac4e7422d34517f75578cf81aba8dc78b746
stop_condition_report.json: 480d569466af6994247dcfe7c3010730b915f7c59f7dd7552c509db6cf08b34b
execution_events.jsonl: 289aef1d0343b7beb79592f9b98d4f1b5de5f74a01b37709cb0500a9ed2ce133
execution_report.json: 685f795d40487ed9effc71b2f940c812f3cb9f44bb1c7824123df16b5b5deff7
post-execution-created-draft-verification.json: 43fc02c57a72c318d8a4cba57619441f298f1058ea0441698681e4b9ba8ed50a
```

The 6 earlier draft feeds were not deleted. The continuation added only new
draft feed records. New gallery records are draft feed rows with `gallery=true`;
their media/folder/relation import remains outside this execution.

Gallery media inventory refresh on 2026-06-26:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-inventory-20260626T154201Z
gallery_manifest: gallery-with-images.jsonl
gallery_manifest_sha256: 3fa7ccf3b220cfeeb2db3e349ad1bac18eb650bc40df9dd2b73084ac6f97ca86
gallery_count: 7
total_images: 291
```

Image counts:

```text
wordpress:gallery:3156 foto_recenti: 17
wordpress:gallery:3974 foto-raduno-2001: 10
wordpress:gallery:5064 foto-raduno-2002: 10
wordpress:gallery:5124 foto-fly-in-vichy-2007: 8
wordpress:gallery:5656 49-raduno-cap-ozzano-emilia-10-11-12-settembre-2021: 53
wordpress:gallery:7494 52-raduno-cap-lilh-6-7-8-9-2024: 148
wordpress:gallery:8152 53-raduno-cap-reggio-emilia-5-6-7-9-2025: 45
```

The prior gallery inventory had zero images because WordPress REST exposes the
`dt_gallery` records with empty rendered content. The inventory client now
enriches REST gallery records from the public album HTML when REST has no
images, and limits HTML image parsing to the `dt_gallery` article container when
present so site logos are not treated as gallery media.

Current blocker for media execution:

```text
GET /folders with the create-only token returns HTTP 403.
```

Gallery media migration requires a separate gate proving folder/file read and
create permissions, plus a create-only request plan for run-owned folders and
files. No gallery media upload was performed during this inventory refresh.

## Definition of done

The migration is done only when all phases are closed, no protected artifact changed, no forbidden method was used, every new object has provenance, reruns are idempotent, and unresolved cases are explicitly excluded or reviewed.
