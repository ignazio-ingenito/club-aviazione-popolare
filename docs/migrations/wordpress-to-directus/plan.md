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

Gallery media permission discovery on 2026-06-26:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-permission-gates-20260626T155615Z
blocked_report_sha256: 6d28be2670e6259fc952643d18d7d2e8d4fc33d2dda6fb429b0959ab608a91f3
policy_probe_sha256: 8afd790514a8a70724228f22ec3ee47254f0f0d552df881bf31a48f43ba891e0
```

Findings:

```text
GET /server/info: 200
GET /policies?filter[name][_eq]=directus-createonly-content-migration: 200
GET /permissions?filter[policy][_eq]=<policy_id>: 200
GET /roles?filter[name][_eq]=directus-createonly-content-migration: 403
```

The current `directus-createonly-content-migration` policy has exactly:

```text
feeds.read
feeds.create
```

It does not have `directus_folders` or `directus_files` read/create
permissions. This confirms that gallery media migration cannot proceed with the
current execution identity. The recommended next permission-management task is
to create a separate `directus-createonly-gallery-media-migration` identity, or
explicitly approve broadening the existing identity for this phase only. The
separate identity is safer because it preserves the feed-only evidence already
used for article creation.

Schema-token GET-only read gate on 2026-06-26:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-read-gate-20260626T195547Z
directus_manifest: directus-core.schema-token.jsonl
directus_manifest_sha256: d974e7f9397e76ebf96b16a9313e17ab9f04109f0baf259efa9c1668c6f56467
comparison_report: gallery-media-read-gate.report.json
comparison_report_sha256: aded7cb0127e7f0bf3358705a4a04380d3a7e2fa3916de7030d421fd5bf26893
live_methods_used: GET only
production_mutations: none
```

Target inventory visible with the schema token:

```text
directus_files: 627
directus_folders: 246
directus_feeds: 326
inventory_issues: 0
```

Gallery comparison result:

```text
gallery_count: 7
gallery_images: 291
unique_gallery_filenames: 291
duplicate_gallery_filenames: 0
folder_name_collisions_for_gallery_slugs: 0
image_filename_collisions: 9
galleries_with_image_filename_collisions: 4
```

The 9 filename matches are not approved reuse evidence. Same filename does not
prove same binary content or same intended gallery placement. Treat them as
manual review candidates or require stronger checksum/content evidence before
reusing existing files.

Gallery-media identity discovery on 2026-06-27:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-identity-20260627T055028Z
identity_name: directus-createonly-gallery-media-migration
service_email: cap-gallery-media-migration@skunklabs.uk
live_methods_used: GET only
live_state_classification: absent_safe_to_create
apply_requested: false
apply_performed: false
production_mutations: none
```

Artifacts:

```text
gallery-media-identity.discovery.json: 8c4158e37cdf1986d8c3179bf01d18626063e4e4eade0bb7f9217351f23c59c6
gallery-media-identity.blocked.json: e907e626c17f75605182aa3ef3d2f2c5f381661f9b53a7355c7f48673221024a
```

The schema/admin token was used only for sanitized permission-management GET
discovery. No gallery-media role, policy, user, token, SOPS secret, folder,
file, feed, or media object was created because
`APPLY_DIRECTUS_GALLERY_MEDIA_IDENTITY=true` was not present.

Production readiness remains blocked until the dedicated gallery-media identity
is created or provided, encrypted in SOPS, and proven with GET-only token probes
and redacted policy evidence. Do not upload gallery media yet.

Gallery-media identity apply attempt on 2026-06-27:

```text
run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-identity-20260627T060034Z
identity_name: directus-createonly-gallery-media-migration
service_email: cap-gallery-media-migration@skunklabs.uk
pre_apply_classification: absent_safe_to_create
post_apply_classification: existing_matches_expected
apply_requested: true
apply_performed: true
```

Permission-management mutations performed:

```text
POST /roles
POST /policies
POST /permissions
POST /users
```

Created live permission graph:

```text
feeds.read
directus_folders.read
directus_folders.create
directus_files.read
directus_files.create
```

No `PATCH`, `PUT`, `DELETE`, content import, media upload, folder content
creation, file upload, feed mutation, schema apply, or frontend change was
performed.

The run remains blocked because the static token captured during user creation
could not be validated afterward. The encrypted secret was not committed: after
the initial SOPS write failed, admin GET recovery exposed only a masked token,
and all gallery-media token GET probes returned HTTP 401. The invalid SOPS file
was removed from the worktree.

Artifacts:

```text
gallery-media-identity.pre-apply-discovery.json: fd09ce7acc8ead6b03fc8f5ce306a5b1ad2644ae4f849014e1caa473c3d05d77
gallery-media-identity.apply.json: 9186fe6c7bbf3625a3d246409bff05ab771faf003dc897a17af20709afdb5688
gallery-media-identity.post-apply-discovery.json: 4f011bc3e44085786f3261f70da80ed9dc8239792ce30a3976dc79767c5f4fef
gallery-media-token-get-probes.json: 6655a6c2b5bda21559c91dd48d330beca36eb84ad32a74a5db210e5f550eda59
gallery-media-identity.final-blocked.json: 188e935adaf7d640613c464359f46e744848fcd880bdb98f87f3069b9ef6ddf5
```

Next action: resolve the gallery-media service user static token with an
approved Directus token regeneration/update procedure, then create the SOPS
secret and rerun GET-only token probes plus redacted policy evidence before any
gallery media upload.

Gallery-media token recovery helper prepared on 2026-06-27:

```text
files:
  cms/utils/wordpress/gallery_media_token_recovery.py
  cms/utils/wordpress/tests/test_gallery_media_token_recovery.py
status: local helper implemented; no live token recovery executed
default_behavior: GET-only discovery/reporting
apply_gate: APPLY_DIRECTUS_GALLERY_MEDIA_TOKEN_REGEN=true
allowed_apply_mutation: PATCH /users/<gallery-media-user-id> token only
forbidden_apply_mutations: roles, policies, permissions, feeds, folders, files, schema, frontend, homelab
```

Verification:

```text
cd cms/utils/wordpress
uv run python -m unittest tests/test_gallery_media_token_recovery.py -v
uv run python -m compileall -q gallery_media_token_recovery.py tests/test_gallery_media_token_recovery.py
```

The helper writes sanitized reports outside Git and refuses output paths inside
the repository. It does not serialize admin or gallery-media tokens into JSON
reports. Production readiness remains blocked until an explicitly approved live
token-regeneration run succeeds, the token is encrypted into SOPS, GET-only
token probes are approved, and redacted policy evidence confirms the identity
is not broader than the intended gallery-media read/create scope.

Gallery media upload completed on 2026-06-27:

```text
token_recovery_run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-token-recovery-20260627T075447Z
token_recovery_status: token_regenerated
token_probe_status: approved
secret_written: secrets/migration/directus-createonly-gallery-media-migration.20260626.sops.yaml

first_upload_attempt_run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-upload-20260627T075707Z
first_upload_status: stopped_on_first_error
first_upload_result: created 1 empty folder, uploaded 0 files
first_upload_error: dedicated gallery-media token received HTTP 403 on POST /files

upload_run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-upload-schema-token-20260627T075818Z
credential_used: directus-schema-token.20260622.sops.yaml
upload_status: completed
created_folders: 6
reused_empty_migration_folder: 1
uploaded_files: 291
post_endpoints: /folders, /files
forbidden_methods_sent: none

schema_verify_run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-post-upload-schema-verify-20260627T080043Z
schema_verify_status: approved
verified_galleries: 7
verified_files: 291

public_read_verify_run_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-public-read-verify-20260627T080104Z
public_read_verify_status: approved
```

Artifact hashes:

```text
gallery-media-token-recovery.apply.json: c996065b76e84f0bfbe8e87a478b7e029a71939ea63548557bf060c139a6073c
gallery-media-token-recovery.probes.json: 4d097ddcd39d1d8048bdb97789b437ef5b552f7326836ff25d702c4757cd67f8
gallery-media-upload-report.json: d0ff923cf0e6830ef18daee6d9ea40885a97dc409f7b3468a58ade5459cf71f8
gallery-media-upload-events.jsonl: 50f32eace3831451565ce0e99a18ecd307d2f268a774c455c46535124f06de78
gallery-media-post-upload-schema-verification.json: eb4a24386ee70f8a22ec38cf2d4f2e39f1b3dad370c135d7343d6ef0aa763979
gallery-media-public-read-verification.json: e723062870f73932fb2ab5e06b54dae89ea69a909d5c1dd599055c93b9073aea
```

The schema token was used for the final upload only after the dedicated
gallery-media token proved unusable for `POST /files`. The operation still used
only `GET`, `HEAD`, and `POST`; no `PATCH`, `PUT`, `DELETE`, feed update,
folder/file update, schema change, frontend change, or homelab change was
performed during media upload. The migrated galleries rely on the existing
folder-by-slug frontend fallback; filenames were uploaded with numeric prefixes
to preserve source order under the current `title, filename_download` sorting.

## Definition of done

The migration is done only when all phases are closed, no protected artifact changed, no forbidden method was used, every new object has provenance, reruns are idempotent, and unresolved cases are explicitly excluded or reviewed.
