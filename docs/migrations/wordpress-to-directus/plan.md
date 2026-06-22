# WordPress to Directus migration plan

Status: active planning and implementation

Last updated: 2026-06-20

This is the canonical binary plan. Every checkbox is either completed (`[x]`) or still required (`[ ]`). Do not use partial states. Split partially completed work into one closed task and one or more open tasks.

## Current active task

- [x] Reconcile WordPress REST source inventory with WXR media export evidence and authenticated Directus target artifacts outside Git.

## Next up

1. Obtain explicit human approval for the authenticated Directus baseline review.
2. If approval is granted, freeze the baseline hash and move to write-manifest review.
3. If more evidence is needed, collect it with the same strict read-only identity before any write work.

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
- [ ] Add a test proving dry-run sends no non-read request.
- [x] Add a test proving protected target records cannot enter a write manifest.
- [ ] Add a test proving ambiguous matches fail closed.
- [x] Add a test proving broad permissions or missing permission evidence stop execution.
- [x] Establish immutable manifest, hashing, JSONL, issue, and pagination contracts without network or write behavior.
- [ ] Remove stale-cache dependence from new migration commands.
- [ ] Keep legacy delete and overwrite commands outside the approved execution path.

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

## Phase 8A — Members-only content

- [x] Capture the initial members-only migration decisions in a dedicated operating specification.
- [x] Obtain a phpMyAdmin SQL export that includes users, password hashes, roles, capabilities, user metadata, plugin membership data, private content, taxonomy data, and relevant options.
- [x] Record that `member_feeds.content` stores sanitized HTML and is not converted to Markdown during initial migration.
- [x] Produce an aggregate WordPress media retrieval report for the members-only migration.
- [x] Create an agent-loop execution plan for `/soci` and `articoli-tecnici`.
- [x] Capture read-only SQL evidence that `sport-aviation` is the source-backed route slug for the `articoli-tecnici` content family.
- [x] Capture read-only SQL evidence that member bootstrap should use `soci_cap` plus approved `pw_user_status`.
- [x] Add a read-only SQL export inventory command for `sport-aviation` articles, required media, taxonomy terms, and membership aggregates.
- [x] Propose Directus members-only schema and permission boundaries without applying them.
- [x] Approve the proposed `member_*` schema direction for implementation planning.
- [x] Create the operational schema apply plan and gates for `member_*`.
- [x] Inventory authenticated Directus application collections with the read-only migration token.
- [ ] Inventory authenticated WordPress members-only categories, sections, articles, media, and galleries.
- [x] Determine the source-backed public label and URL slug for `articoli-tecnici`; prefer the proven magazine/publication name over the technical source post type.
- [ ] Generate a required-media list from members-only content before downloading or archiving WordPress uploads.
- [ ] Retrieve only referenced private media through FTP or a targeted uploads archive when possible.
- [ ] Use temporary FTP access for referenced media retrieval without committing credentials, transfer logs, or downloaded files.
- [ ] Model members-only articles in a dedicated `member_feeds` collection.
- [ ] Model members-only categories in a dedicated `member_categories` collection.
- [ ] Implement and run the `member_*` schema dry-run artifact generator.
- [ ] Apply the approved `member_*` schema with a schema-capable token after preflight gates pass.
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

## Definition of done

The migration is done only when all phases are closed, no protected artifact changed, no forbidden method was used, every new object has provenance, reruns are idempotent, and unresolved cases are explicitly excluded or reviewed.
