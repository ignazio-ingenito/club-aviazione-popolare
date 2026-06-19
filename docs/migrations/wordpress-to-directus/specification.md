# Migration specification

Status: normative design

## 1. Safety requirements

The migration is additive-only.

It MUST NOT update, delete, rename, move, replace, or re-relate any target object present in the approved baseline. This applies to feeds, files, binary objects, folders, covers, categories, gallery relations, and any other content record in scope.

An existing Directus record always wins over WordPress. Source drift is diagnostic information only.

The migration MUST fail closed when identity is ambiguous, inventory is incomplete, permissions are broader than approved, or baseline verification cannot be completed.

## 2. Definitions

**Protected production artifact**: a target object captured in the approved baseline, or an object created by a completed migration run after that run is accepted.

**Migration-owned artifact**: a new object created by one identified migration run and recorded in the append-only ledger.

**Source identity**: a stable WordPress identity such as `wordpress:post:<id>`, `wordpress:media:<id>`, or `wordpress:gallery:<id-or-slug>`.

**Baseline**: a timestamped, immutable inventory of target identifiers, relevant metadata, relations, and fingerprints created before any migration write.

**Reconciliation report**: the read-only classification of every source and target candidate, including evidence and required action.

## 3. Inventory requirements

### Source inventory

The source inventory MUST be collected without relying on stale joblib cache or `parser.yaml`.

For posts it MUST include, when available:

- WordPress ID and type;
- slug and canonical URL;
- publication and modification timestamps;
- status;
- rendered title, excerpt, and content;
- category and tag IDs;
- featured-media ID and URL;
- embedded and linked media URLs;
- a deterministic source hash.

Pagination MUST be complete and checked against WordPress totals.

For galleries it MUST include:

- source identity, slug, title, URL, and date;
- album cover when identifiable;
- every image in source order;
- attachment identity when exposed;
- original image URL, title, alt text, and caption when available;
- a deterministic album hash.

### Target inventory

The target inventory MUST be read-only and include:

- all feeds in scope, including drafts and archived states;
- all relevant files, folders, and relations;
- `id`, slug, `original_uri`, status, category, cover, title, dates, and gallery flag;
- file metadata and checksum where obtainable;
- relation ordering;
- deterministic row and relation fingerprints.

The target inventory MUST be generated from the same environment that will receive the migration.

### Baseline storage

Inventories and reports MUST NOT be committed when they contain production content, private metadata, credentials, or binary data. Store them as controlled run artifacts with hashes recorded in the migration handoff.

## 4. Reconciliation states

Every source item MUST receive exactly one state:

- `ledger_match`: a previously accepted ledger entry maps the source to a target object.
- `exact_existing`: a unique target match is proven by strong evidence.
- `validated_historical_mapping`: `parser.yaml` points to a current target and is corroborated by URL or other strong evidence.
- `protected_existing_drift`: source and target represent the same content but differ; target remains unchanged.
- `manual_review_candidate`: evidence suggests a match but is not conclusive.
- `create_candidate`: no credible existing target match or route collision exists.
- `conflict`: multiple target matches, duplicate source identities, or incompatible evidence exist.
- `excluded`: outside the approved source/category/status scope.
- `source_error`: the source record or its required media could not be inventoried.

Every target item MUST be either matched or classified as `target_only_protected`. Target-only objects are never deletion candidates.

Only `create_candidate` may proceed to an approved write manifest.

## 5. Matching policy

Evidence is evaluated conservatively in this order:

1. accepted append-only ledger entry;
2. unique exact `original_uri` match after URL normalization;
3. validated historical mapping whose target exists and whose identity is corroborated;
4. unique exact canonical slug plus corroborating date/title/category evidence;
5. content, title, date, and media similarity for manual review only.

Rules:

- `parser.yaml` is historical evidence, never authoritative state;
- a stale Directus ID invalidates the historical mapping;
- slug or title alone MUST NOT authorize creation or mutation;
- a route collision blocks automatic creation;
- a matched target remains protected even when hashes differ;
- uncertain cases stop in manual review.

## 6. Write policy

The production executor MUST use a dedicated Directus identity with read and create permissions only.

The executor MUST enforce both:

- an HTTP method allowlist: `GET`, `HEAD`, and approved `POST` endpoints only;
- an endpoint allowlist for the target collections, folders, files, and migration ledger.

Any attempted `PATCH`, `PUT`, or `DELETE` is a fatal error.

Dry-run MUST make no non-read request.

The production write manifest MUST be immutable, reviewed, hashed, and linked to the source inventory, target baseline, and reconciliation report from which it was generated.

## 7. Article creation

For each approved missing article:

1. validate source identity and manifest hash;
2. re-check that no target match or route collision appeared since reconciliation;
3. download required media over verified TLS;
4. validate response status, size limit, MIME type, and basic file signature;
5. compute SHA-256;
6. upload files only into a migration-owned folder;
7. deterministically rewrite source media URLs to newly created Directus assets;
8. create the feed once, as draft, with its final content and cover;
9. record all created IDs and checksums in the ledger;
10. verify the new draft and its assets.

The importer MUST NOT:

- update an existing feed to finish an import;
- choose a different existing feed because creation failed;
- truncate or omit content to satisfy a schema error;
- drop category or cover silently;
- use AI formatting;
- remove source images or text based on editorial heuristics;
- publish automatically.

If a required step fails before feed creation, the article is not created. Newly uploaded run-owned files remain recorded for review; they are not deleted automatically.

## 8. Media handling

Existing files are immutable.

A new source media object may reuse an existing file only when an accepted ledger entry already proves the mapping. Similar filename, URL, size, or checksum without a ledger entry is diagnostic evidence, not authorization to mutate or reassign an existing file.

New uploads MUST retain source provenance in the ledger. Original filename, source URL, source ID, checksum, MIME type, byte size, created Directus ID, and run ID must be recorded.

No migration path may replace a thumbnail, rename a file, move a file between folders, or delete an unused upload.

## 9. Gallery handling

Discovery MUST first inspect WordPress content types and use the REST endpoint when the gallery type is exposed. Otherwise use an approved export; public HTML discovery is the final read-only fallback.

Image order from the source MUST be preserved explicitly.

For new galleries, the preferred target is:

- one new feed with `gallery=true`;
- one migration-owned folder;
- an ordered relation between the feed and newly created Directus files;
- explicit cover selection;
- ledger entries for the album and every image.

Existing production galleries MUST continue to work with the current folder-by-slug behavior. New relation-based rendering must include that legacy fallback until all existing galleries are independently reviewed under a separate project.

## 10. Ledger requirements

The production ledger is append-only and separate from protected feed/file rows.

Each entry records at least:

- source system, type, ID, URL, and source hash;
- target collection and ID;
- status: pre-existing protected or migration-created;
- match evidence or create approval;
- run ID;
- source inventory hash and target baseline hash;
- reviewer and approval timestamp when applicable;
- verification result.

Corrections are new superseding entries, not in-place edits or deletions.

## 11. Concurrency and retry

- Inventory reads may use bounded concurrency.
- Production writes are serial by default.
- A retry is allowed only when the prior request is proven not to have created an object, or when the created object can be recovered through the ledger/run id without updating it.
- Ambiguous network outcomes stop the run for manual reconciliation.
- Creation must use deterministic idempotency checks based on the approved manifest and ledger, not slug-only upsert behavior.

## 12. Verification and acceptance

Before production:

- backup and upload-volume protection are verified;
- baseline and inventories are complete and hashed;
- the approved write manifest contains only `create_candidate` items;
- permissions and method guards are tested;
- staging rehearsal passes twice, with the second run creating nothing.

After production:

- every protected object still exists;
- protected row and relation fingerprints are unchanged;
- protected file checksums are unchanged;
- no update or delete request occurred;
- every created object has a ledger entry;
- all new feeds remain draft until editorial approval;
- every new asset is reachable;
- a fresh reconciliation produces no duplicate create candidate for completed source identities;
- failures and unresolved cases are explicitly reported.

Any failed invariant makes the migration run unsuccessful, even when all intended new records were created.
