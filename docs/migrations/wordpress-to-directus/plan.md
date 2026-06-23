# WordPress to Directus migration plan

Status: active planning and implementation

Last updated: 2026-06-23

This is the canonical binary plan. Every checkbox is either completed (`[x]`) or still required (`[ ]`). Do not use partial states. Split partially completed work into one closed task and one or more open tasks.

## Current active task

- [ ] Prepare a separate explicit production execution prompt. Final readiness
  review is `ready_for_explicit_execution_approval`, but production content
  `POST` is still not enabled.

## Next up

1. Use `/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/permission-evidence-create-only.json` as Gate 1 input.
2. Use the narrowed manifest artifacts in `/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z`.
3. Use the final readiness report generated in
   `/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z/final-execution-readiness-20260623T195141Z`.
4. Review the narrowed executor dry-run reports generated in
   `/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z/executor-dry-run-narrowed-20260623T192241Z`.
5. Prepare a separate explicit production execution prompt if the operator
   approves production content `POST /items/feeds`.

## Task B — Read-only inventory implementation

- [x] Slice 1: common manifest models, canonical JSON, SHA-256, JSONL, pagination contracts, and synthetic tests.
- [x] Slice 2: WordPress read-only client for types, categories, posts, and media.
- [x] Slice 3: gallery REST discovery and ordered public-HTML fallback.
- [x] Slice 4: Directus read-only client for runtime metadata, schema metadata, feeds, categories, files, folders, and relations.
- [x] Slice 5: repository route inventory and collision input contract.
- [x] Slice 6: read-only CLI integration and end-to-end synthetic fixtures.
- [x] Slice 7: local WXR media export inventory for WordPress attachments hidden from public REST.
- [x] Slice 8: reconciliation workflow, historical mapping corroboration only, and write-manifest gating.

Task B exit gate: all inventories are fresh by default, pagination and counts fail closed, generated artifacts stay outside Git, and no code path can emit a non-read request.

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
- [x] Capture complete WordPress media evidence from an admin WXR export when public REST pagination omits private attachments.
- [x] Verify that public gallery albums are available through `/gallery/` and `/dt-gallery/<slug>/` HTML routes.
- [ ] Determine whether the gallery custom post type is exposed through WordPress REST or requires export/public-HTML fallback.
- [x] Inventory frontend routes and identify global slug and route collision rules.
- [x] Document the current production gallery behavior and legacy exact-folder-name fallback contract.
- [x] Review `parser.yaml` as historical evidence and document why it cannot be target authority.
- [ ] Validate historical mappings against the current Directus target during reconciliation inventory.
- [x] Produce the read-only discovery report with open questions and no production writes.

Exit gate: source and target contracts are known well enough to design deterministic inventories. Authenticated runtime facts are completed by the read-only inventory client before baseline approval.

## Phase 2 — Safety controls and tests

- [x] Introduce a read-only HTTP client for source and target inventory.
- [x] Add a create-only Directus client separated from the legacy mutable client.
- [x] Add a method and endpoint allowlist that rejects `PATCH`, `PUT`, and `DELETE`.
- [x] Add a test proving dry-run sends no non-read request.
- [x] Add a test proving protected target records cannot enter a write manifest.
- [ ] Add a test proving ambiguous matches fail closed.
- [x] Add a test proving broad permissions or missing permission evidence stop execution.
- [x] Establish immutable manifest, hashing, JSONL, issue, and pagination contracts without network or write behavior.
- [ ] Remove stale-cache dependence from new migration commands.
- [ ] Keep legacy delete and overwrite commands outside the approved execution path.
- [x] Add a draft-only executor scaffold for the approved 28 article and 7 gallery create manifest.
- [x] Add mandatory pre-create safety gate validation for execute mode without enabling real POST emission.

Exit gate: automated tests enforce the production invariant before a write path exists.

## Phase 3 — Target baseline

- [ ] Define the target baseline entity schemas and canonical hashing rules using the common manifest contracts.
- [ ] Inventory all feeds, files, folders, and relevant relations in scope.
- [ ] Record file checksums where accessible and metadata fingerprints otherwise.
- [ ] Include all statuses, not only published content.
- [ ] Record baseline timestamp, target URL, Directus version, schema hash, and inventory hash.
- [ ] Validate counts and pagination independently.
- [ ] Store the production baseline as a controlled run artifact, not in Git.
- [ ] Obtain explicit human approval of the baseline.

Exit gate: every existing in-scope target object is represented as a protected artifact.

## Phase 4 — Source inventory

- [ ] Define the WordPress post, media, category, and gallery payload schemas using the common manifest contracts.
- [ ] Fetch all approved posts with complete pagination and no stale cache.
- [ ] Capture categories, featured media, inline media, links, dates, and source hashes.
- [ ] Discover all public gallery albums and ordered images.
- [ ] Resolve original media URLs without mutating source or target.
- [ ] Record source errors rather than silently omitting records.
- [ ] Validate source counts against WordPress totals and archive pages.
- [ ] Store the source inventory as a controlled run artifact.

Exit gate: every source record in scope is inventoried or explicitly classified as an error.

## Phase 5 — Reconciliation and approval

- [ ] Implement the reconciliation states defined in the specification.
- [ ] Match accepted ledger entries first.
- [ ] Validate exact `original_uri` matches.
- [ ] Revalidate historical YAML mappings against the current target as corroboration only, never as authority.
- [ ] Treat slug/title/date/category similarity as manual-review evidence only.
- [ ] Detect route, slug, source identity, and target identity collisions.
- [ ] Classify source-target drift as protected, never as an update candidate.
- [ ] Report strongly divergent source-target matches with article identities and field-level differences for later editorial reconciliation.
- [ ] Produce a human-readable and machine-readable reconciliation report.
- [ ] Review every `manual_review_candidate` and `conflict`.
- [ ] Generate an immutable write manifest containing only approved `create_candidate` items.
- [ ] Hash and approve the write manifest.

Exit gate: every proposed write is a new object with unambiguous evidence and explicit approval.

## Phase 6 — Append-only ledger and Directus permissions

- [x] Design the Directus read-only and create-only content-migration identities and SOPS secret plan without creating roles, users, tokens, or permissions.
- [x] Create a non-applied Directus content-migration permission implementation plan with draft-only create validation, presets, and additive-policy verification warnings.
- [x] Create a non-applied Directus policy-graph evidence plan and sanitized JSON example for future create-only permission validation.
- [x] Implement a pure local evaluator for sanitized Directus policy-graph evidence without live Directus collection.
- [x] Implement a strict local normalizer for synthetic raw Directus policy graph payloads without live Directus collection.
- [x] Implement a mocked GET-only Directus policy graph live collector scaffold without running it against production.
- [x] Adapt the live collector `/policies` query to the Directus 11.13.2 relation filter shape after GET-only live probing.
- [x] Resolve the live collector `/permissions` empty response with GET-only live probing. The selected role's attached policy has no readable permission rows, while `/permissions` itself is readable; this is not a collector query mismatch.
- [x] Verify the currently stored `DIRECTUS_ROLE_ID` in `secrets/migration/directus-schema-token.20260622.sops.yaml` with GET-only live evidence. It resolves to the `Administrator` role and `Administrator` policy with admin/app access, so it is the wrong role id for the intended create-only content-migration identity.
- [x] Prepare a dry-run Directus create-only identity plan for `directus-createonly-content-migration` and perform GET-only discovery. No matching role, policy, or planned service user currently exists; no Directus mutation was performed because the apply approval environment flag was absent.
- [x] Attempt the approved Directus create-only identity apply with `APPLY_DIRECTUS_CREATEONLY_IDENTITY=true`. The task created only permission-management resources: the dedicated role, dedicated policy, `feeds.read`, and draft-constrained `feeds.create`; it stopped before creating a usable execution identity because `POST /users` rejected the placeholder service email.
- [x] Run the approved recovery task with fresh GET-only comparison. Final comparison classified the partial state as `partial_state_matches_expected`: exactly one migration-owned role, one migration-owned policy, expected `feeds.read`, draft-constrained `feeds.create`, zero service users for the two planned emails, and no detected update/delete/wildcard permission.
- [x] Recover the create-only service user and static token with a Directus-accepted valid service email. The recovery used `cap-migration@skunklabs.uk` and only `POST /users` after fresh GET-only comparison.
- [x] Create `secrets/migration/directus-createonly-content-migration.20260622.sops.yaml` after the create-only token exists. The secret is SOPS-encrypted and contains `target_url`, `identity_name`, `role_id`, `token`, `service_email`, `created_at`, and `purpose`.
- [x] Provide a Directus migration identity policy graph export or equivalent operator-generated redacted permission evidence with complete permission rows. The approved redacted admin/operator export evaluated successfully and produced `permission-evidence-create-only.json` outside Git; the create-only token remains narrow and still cannot read `/roles`.
- [x] Design the append-only ledger schema and supersession model.
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

## Phase 8A — Members-only content

- [x] Capture the initial members-only migration decisions in a dedicated operating specification.
- [x] Obtain a phpMyAdmin SQL export that includes users, password hashes, roles, capabilities, user metadata, plugin membership data, private content, taxonomy data, and relevant options.
- [x] Record that `member_feeds.content` stores sanitized HTML and is not converted to Markdown during initial migration.
- [x] Produce an aggregate WordPress media retrieval report for the members-only migration.
- [x] Create an agent-loop execution plan for `/soci` and `articoli-tecnici`.
- [x] Record model-routing policy for members-only agent-loop execution.
- [x] Capture read-only SQL evidence that `sport-aviation` is the source-backed route slug for the `articoli-tecnici` content family.
- [x] Capture read-only SQL evidence that member bootstrap should use `soci_cap` plus approved `pw_user_status`.
- [x] Add a read-only SQL export inventory command for `sport-aviation` articles, required media, taxonomy terms, and membership aggregates.
- [x] Propose Directus members-only schema and permission boundaries without applying them.
- [x] Approve the proposed `member_*` schema direction for implementation planning.
- [x] Create the operational schema apply plan and gates for `member_*`.
- [x] Inventory authenticated Directus application collections with the read-only migration token.
- [ ] Inventory authenticated WordPress members-only categories, sections, articles, media, and galleries.
- [x] Determine the source-backed public label and URL slug for `articoli-tecnici`; prefer the proven magazine/publication name over the technical source post type.
- [x] Generate a required-media list from the `Sport Aviation` source inventory before downloading WordPress uploads.
- [x] Retrieve only referenced `Sport Aviation` media through FTP. Artifact directory: `/tmp/cap-migration-runs/20260622-wordpress-ftp-download/downloads`, 431 files, 134M, checksum manifest SHA-256 `541229a23d43bdb58fb301035aa96130b9540b86e99ecd27cecb6de8c387a435`.
- [x] Use temporary FTP access for referenced media retrieval without committing credentials, transfer logs, or downloaded files.
- [ ] Model members-only articles in a dedicated `member_feeds` collection.
- [ ] Model members-only categories in a dedicated `member_categories` collection.
- [x] Implement and run the `member_*` schema dry-run artifact generator. Artifact: `/tmp/cap-migration-runs/20260622-directus-member-schema-plan/directus-member-schema-plan.jsonl`, SHA-256 `2697c1199ccef9108c05f884138c04b9b818a5461ab39ff8e26489678ecf9ef8`.
- [ ] Apply the approved `member_*` schema with a schema-capable token after preflight gates pass. The corrected 2026-06-22 apply audit reports 59 POST requests, 59 successful, 0 skipped, and 0 failed, but final live post-apply verification is still pending.
- [ ] Resolve Directus schema-token permissions. Attempted `POST /collections` on 2026-06-22 with the encrypted schema token; Directus returned `403 FORBIDDEN`, and post-check confirmed 0 `member_*` collections were created.
- [x] Resolve the partial `member_*` schema apply failure. On 2026-06-22 the retry created the 6 approved migration-owned collections and fields, then stopped at `POST /relations` sequence 59 because Directus had auto-created integer primary keys while the manifest created UUID foreign-key fields for member-owned relations. The approved recovery verified 6 empty migration-owned collections with 0 relations, deleted only those collections, verified their removal, regenerated a corrected schema plan, and applied it with POST-only execution.
- [ ] Complete final live post-apply verification for the corrected `member_*` schema. Pending because the network approval system hit the usage limit before the verification script could run.
- [x] Review and approve the proposed `member_topics` secondary taxonomy model.
- [ ] Treat members-only galleries as absent by default; if discovered, model them in a dedicated `member_galleries` collection.
- [ ] Keep editorial status separate from audience visibility when modeling members-only content.
- [ ] Preserve source categories and sections during the initial migration.
- [ ] Defer any members-only content reorganization to a separate post-migration editorial task.
- [ ] Choose the members-only authentication mechanism, prioritizing WordPress password-hash compatibility, then implementation and operational simplicity, current cost/free-tier fit, and clean integration with `/soci` and Directus.
- [ ] Prefer Directus as the final authoritative authentication system if a temporary WordPress legacy-password bridge can be implemented safely.
- [ ] Store temporary WordPress password hashes in a private `legacy_wordpress_credentials` collection restricted to backend/service-role access.
- [ ] Enforce a 90-day post-go-live transition window for legacy WordPress password hashes.
- [ ] Inventory all WordPress users, roles, and password-hash format for account migration.
- [ ] Treat WordPress users as a one-time bootstrap source, then make the new authentication system authoritative.
- [ ] Migrate all WordPress users during the initial account bootstrap.
- [ ] Use WordPress membership evidence to map users into the member role.
- [ ] Discover the WordPress membership mechanism through read-only plugin, role, capability, and usermeta inventory.
- [ ] Give no private-content access by default to users without clear membership or editorial-role evidence.
- [ ] Map WordPress users into the target roles: member access, redazione, and pubblicazione.
- [ ] Use the Directus backend for redazione and pubblicazione workflows.
- [ ] Prefer password-hash migration only if the chosen authentication mechanism can verify WordPress hashes safely.
- [ ] Prototype first-login WordPress hash verification and Directus password upgrade in the Next.js/API layer with synthetic legacy hashes.
- [ ] Fall back to an approved invitation or password-reset flow when WordPress password hashes cannot be reused safely or simply.
- [ ] Implement a frontend login page and authenticated session experience.
- [ ] Support password reset in the first members-only frontend release.
- [ ] Defer editable member profiles until after the initial authenticated content release.
- [ ] Use `/soci` as the canonical frontend root for members-only routes.
- [ ] Use `/soci/<categoria>/<slug>` for members-only article routes.
- [ ] Redirect anonymous `/soci` requests to login and return users to the originally requested URL after authentication.
- [ ] Return a simple 403 for authenticated users without the member role.
- [ ] Configure authenticated frontend access for members-only routes.
- [ ] Configure Directus roles or policies for members-only content management.
- [ ] Reconcile members-only source content against members-only target content without mutating public protected articles.
- [ ] Import verified members-only content as visible to members when it is already visible to members in WordPress.
- [ ] Keep uncertain, new, or editorially unresolved members-only content out of member-visible publication until reviewed.

Exit gate: members-only content is migrated faithfully under authentication, and any reorganization remains a separate reviewed task.

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
- [x] Verify create-only permissions immediately before execution. Gate 1
  permission evidence was approved on 2026-06-23 with artifact
  `/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/permission-evidence-create-only.json`,
  SHA-256 `7b7cbcc3878729b85430dea508c6e1c57744e56b0c251426ad917c1fae0ae9d6`.
- [ ] Regenerate the approved create manifest before production execution.
  Gate 2 fresh target absence was attempted on 2026-06-23 and rejected because
  7 manifest slugs already exist in the target baseline/live Directus view
  (`14` slug collision entries: live plus baseline evidence). Artifact:
  `/tmp/cap-migration-runs/20260622T110402Z/fresh-target-absence-before-create-20260623T155104Z/fresh-target-absence-before-create.json`,
  SHA-256 `addfd2adca5deb073e8aa4689acb76f704d0dafafd340223c9a7701c69e198e9`.
- [x] Narrow the approved create manifest after Gate 2 slug collisions. The
  narrowed artifacts remove 7 colliding article operations and keep 28
  operations: 21 article drafts and 7 gallery drafts. Artifact directory:
  `/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z`.
  Narrowed manifest SHA-256:
  `9dd3289b2db550dc329032e7e825e74a48449a07ff69547ee455c3f4d9dbc0f9`.
  Narrowed approval SHA-256:
  `6b4093177cf4156084292add1bb1e7adac802d9f8c60e1633b5fc68621d98994`.
  Narrowed Gate 2 SHA-256:
  `bbf399f35c138396dc3240c5198c05ef8d45f7d7f95296f087bc377ab39a8a55`.
- [x] Wire the executor to the narrowed artifact hashes and counts through
  approved artifact profiles. The default remains the original 35-operation
  profile, while `narrowed_after_gate2_20260623T162618Z` validates the narrowed
  approval, manifest, Gate 2 hash, and 28-operation count.
- [x] Run narrowed executor dry-run only. Artifact directory:
  `/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z/executor-dry-run-narrowed-20260623T192241Z`.
  The request plan contains 28 theoretical `POST /items/feeds` draft creates,
  `execute_requested=false`, `non_read_requests_sent=0`, and
  `post_requests_sent=0`.
- [x] Prepare final execution-readiness review for the narrowed manifest.
  Readiness artifact directory:
  `/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z/final-execution-readiness-20260623T195141Z`.
  Status: `ready_for_explicit_execution_approval`. Report SHA-256:
  `1b17bfac4f3703fdabb9086593cd16042044c228058aee054c734025f38f3b76`.
  No `--execute` run was performed and no Directus mutation was performed.
- [ ] Obtain explicit production approval for the exact manifest hash and
  execution prompt.
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

## Definition of done

The migration is done only when all phases are closed, no protected artifact changed, no forbidden method was used, every new object has provenance, reruns are idempotent, and unresolved cases are explicitly excluded or reviewed.
