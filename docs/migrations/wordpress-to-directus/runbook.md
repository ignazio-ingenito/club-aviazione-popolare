# Operational runbook

Status: procedure design. Production execution requires explicit approval.

## 1. Purpose

This runbook governs the WordPress-to-Directus migration from preflight through post-run verification. It is subordinate to ADR 0001 and the migration specification.

The operator must stop whenever a required artifact, approval, permission check, or invariant is missing.

## 2. Roles

- **Operator**: executes approved read-only checks and the exact approved write manifest.
- **Reviewer**: independently reviews inventories, reconciliation, permissions, and verification evidence.
- **Editor**: reviews and publishes newly created drafts after migration.
- **Infrastructure owner**: verifies database backup, upload-volume protection, capacity, and restore readiness.

One person may hold multiple roles, but operator and reviewer actions must still be recorded separately in the handoff.

## 3. Environment separation

Use distinct configuration for:

- local development;
- staging rehearsal;
- production read-only inventory;
- production create-only execution.

Do not reuse a broad administrator token for execution. Do not store credentials, inventories, manifests, or production content in Git.

Each run needs a unique ID, UTC start time, source inventory hash, target baseline hash, reconciliation hash, write-manifest hash, code commit, environment, operator, and reviewer.

## 4. Forbidden production paths

The legacy importer is not an approved production executor.

Never run against production:

- the delete command;
- overwrite or media-overwrite options;
- AI formatting;
- helpers that update or delete Directus items, files, or folders;
- thumbnail replacement that removes an existing file;
- cleanup or deduplication routines;
- an importer that can emit `PATCH`, `PUT`, or `DELETE`;
- an importer that silently drops or truncates fields.

Do not use `parser.yaml` or a local cache as proof that a current target object exists.

## 5. Required run artifacts

Create a controlled directory outside Git for each environment and run. It must contain:

- `run.json`: run identity and approvals;
- `source-inventory.jsonl` and checksum;
- `target-baseline.jsonl` and checksum;
- `reconciliation.jsonl` and checksum;
- `write-manifest.jsonl` and checksum;
- permission verification report;
- dry-run report;
- execution event log with request method and endpoint, excluding credentials;
- post-run target inventory;
- invariant verification report;
- final operator and reviewer handoff.

Article bodies and private metadata must be protected according to the environment in which these artifacts are stored.

## 6. Preflight

Before any production inventory:

1. Confirm the repository commit and migration document versions.
2. Confirm the production Directus URL and exact Directus version.
3. Confirm the WordPress source URL and availability.
4. Confirm the category and status scope approved for the run.
5. Confirm no source or target freeze is being assumed without evidence.
6. Confirm enough controlled storage exists for inventories, logs, and downloaded media.
7. Confirm the operator has only the credentials needed for the current phase.
8. Confirm clocks are synchronized and timestamps are recorded in UTC.

Stop if environment identity is unclear or any credential is broader than required.

## 7. Database and media protection

Before a production write:

1. In the `homelab` repository, verify the shared CNPG cluster is healthy.
2. Verify the latest scheduled backup completed successfully and archiving is healthy.
3. Record the backup identity and completion time in `run.json`.
4. Verify the `cap` database is covered by the backup path.
5. Verify the Directus upload PVC and storage backend are healthy.
6. Record current PVC capacity, usage, and expected migration media size.
7. Use the infrastructure-approved snapshot or backup procedure for the upload volume when available.
8. Confirm a restore procedure is documented and understood; do not perform a restore drill against production.

Taking a new backup or snapshot is a production action and requires explicit approval. A recent scheduled backup may satisfy the gate only when the infrastructure owner accepts it.

Stop if backup status, archiving, volume protection, or capacity cannot be proven.

## 8. Capture the target baseline

Use the read-only inventory identity.

1. Fetch Directus schema metadata needed to interpret collections and relations.
2. Inventory all in-scope feeds across all statuses.
3. Inventory relevant categories, files, folders, covers, and gallery relations.
4. Follow pagination until counts agree with Directus totals.
5. Compute canonical row and relation fingerprints.
6. Compute file SHA-256 where the binary can be read; otherwise record metadata fingerprint and explicitly mark checksum coverage.
7. Record Directus version, schema hash, target URL, timestamp, and total counts.
8. Hash the complete baseline.
9. Have the reviewer compare independent counts and approve the baseline hash.

The approved baseline defines the immutable protected set. If the target changes before execution, the baseline is stale and cannot be reused.

## 9. Capture the WordPress source inventory

Use fresh network reads; disable legacy joblib cache.

1. Fetch the WordPress types and category inventory.
2. Fetch all posts in scope using complete pagination.
3. Compare fetched totals with WordPress response totals.
4. Record posts that fail to parse or reference unavailable required media.
5. Fetch media metadata and resolve original URLs deterministically.
6. Discover galleries through the exposed REST type when available; otherwise use the approved fallback source.
7. Preserve album image order.
8. Compute source record and album hashes.
9. Hash the complete source inventory.
10. Have the reviewer validate counts against public archive evidence.

Do not silently omit source errors. A source error is not a create candidate.

## 10. Reconcile

Run reconciliation without write credentials.

1. Load the accepted ledger first.
2. Compare exact canonical source URLs with target `original_uri`.
3. Revalidate every relevant `parser.yaml` mapping against the current target as corroboration only; parser.yaml is never authoritative.
4. Detect slug, route, title, date, category, and media evidence.
5. Classify each source and target using the specification states.
6. Treat every existing match and source-target drift as protected.
7. Put ambiguous or conflicting candidates in manual review.
8. Confirm every target-only object remains protected.
9. Review all `create_candidate` records for public-route collisions.
10. Hash and approve the reconciliation report.
11. Build a write manifest containing only approved new records from the approved reconciliation report.
12. Hash and approve the write manifest.

The reviewer must be able to explain why every write-manifest item is missing. “Not found in parser.yaml” is not sufficient evidence, because parser.yaml is corroboration only.

## 11. Verify execution permissions

Before staging and again before production:

1. Identify the exact Directus role and execution identity.
2. Verify allowed collection and system-resource endpoints.
3. Run negative permission probes against disposable staging objects where possible.
4. Prove update and delete are denied.
5. Prove schema, settings, users, roles, policies, and permissions are inaccessible.
6. Verify the client-side method guard rejects `PATCH`, `PUT`, and `DELETE` before network transmission.
7. Save the permission report without credentials.

Stop if permission evidence is incomplete or broader than read/create-only.

## 12. Staging rehearsal

Staging must represent the approved target baseline closely enough to test collisions and immutability.

1. Capture a staging baseline.
2. Run dry-run and confirm no non-read requests.
3. Execute the approved staging manifest serially.
4. Verify every new feed is draft and every new object is in the ledger.
5. Verify content, cover, category, media links, file checksums, and gallery order.
6. Re-inventory staging and prove protected fingerprints are unchanged.
7. Run the same manifest again and confirm zero creations.
8. Review request logs for forbidden methods and endpoints.
9. Record failures, duration, storage growth, and operator steps.
10. Obtain reviewer approval of the rehearsal report.

Any staging mutation of a protected object blocks production readiness.

## 13. Production go/no-go

Immediately before execution, confirm:

- the source inventory still represents WordPress;
- the target baseline still represents Directus;
- the backup and storage evidence is current;
- the execution identity is still create-only;
- the exact code commit passed tests;
- the exact write-manifest hash is approved;
- no unresolved conflict or source error is included;
- newly created feeds will remain draft;
- operator and reviewer are identified;
- a stop contact is available.

A changed source or target requires a new inventory, reconciliation, and approval. Do not patch the manifest manually.

## 14. Production dry-run and execution

### Dry-run

1. Load the approved immutable artifacts.
2. Re-check every create candidate against current target identities and routes.
3. Validate media availability, size, and MIME constraints without uploading.
4. Produce the proposed request list.
5. Confirm there are no non-read requests.
6. Obtain final production approval.

### Execution

1. Start the request audit log.
2. Process write-manifest items serially.
3. For each article, create required media and then create the final feed once as draft.
4. For each gallery, preserve album order and record each relation.
5. Append ledger entries as objects are created.
6. Verify each created object before advancing.
7. Stop on the first ambiguity, permission error, unexpected response, baseline change, route collision, or forbidden method.
8. Record the final run status and all created object IDs.

Never switch to a broader token or mutable legacy path to complete a failed item.

## 15. Post-run invariant verification

Using read-only credentials:

1. Capture a complete post-run target inventory.
2. Compare every baseline feed fingerprint.
3. Compare every baseline file row and available binary checksum.
4. Compare every baseline folder and relation fingerprint.
5. Confirm no protected object disappeared.
6. Confirm request audit contains no update or delete method.
7. Confirm every new object belongs to the run ledger.
8. Confirm all new feeds are draft.
9. Confirm new assets return successfully and match recorded checksums.
10. Confirm article routes do not shadow protected routes.
11. Confirm gallery image counts and order.
12. Run fresh reconciliation and confirm completed sources are not proposed again.
13. Have the reviewer sign the invariant report.

A single protected-object mismatch makes the run unsuccessful and requires incident review before any further action.

## 16. Failure handling

On failure:

- stop the executor;
- retain logs and the last confirmed ledger position;
- do not delete or update existing or newly created objects automatically;
- keep newly created feeds draft;
- identify run-owned files and folders in the report;
- classify ambiguous network results before retrying;
- rerun baseline verification;
- resume only with a newly approved manifest or documented idempotent recovery path.

Restoring a database or volume is exceptional, affects unrelated production data, and requires a separate incident decision.

## 17. Editorial publication

Publication is outside the migration executor.

An editor reviews each new draft for title, content integrity, category, cover, attachments, gallery order, and public route. Publication must not alter protected artifacts and must be recorded separately from the migration run.

WordPress remains available until migration, editorial review, route compatibility, and redirect work are independently accepted.
