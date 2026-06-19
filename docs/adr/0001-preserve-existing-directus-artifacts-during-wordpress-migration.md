# ADR 0001: Preserve existing Directus artifacts during the WordPress migration

Date: 2026-06-19

## Status

Accepted

## Context

The new website already contains articles and media imported into Directus. Some articles have subsequently been edited in Directus and are no longer exact copies of the online WordPress source. Those edits are intentional production work.

A normal synchronization or upsert process could overwrite curated text, covers, categories, authors, media, or gallery organization. The existing utility under `cms/utils/wordpress/` also contains update, overwrite, replacement, and delete paths that are not safe for the remaining production migration.

The remaining migration must add missing articles and galleries while proving that existing production content remains untouched.

## Decision

The WordPress-to-Directus migration is **additive-only and target-authoritative**.

At an explicitly approved baseline timestamp, all existing target objects in scope become protected production artifacts, including:

- existing `feeds` items;
- existing `directus_files` rows and binary objects;
- existing `directus_folders` rows;
- existing category, cover, gallery, and file relations;
- other target records identified by the baseline as part of a public article or gallery.

Migration tooling must not update, replace, move, rename, or delete a protected production artifact.

When WordPress and Directus differ, the Directus artifact is authoritative. Source drift is reported and never turned into a target update.

After backup, baseline, reconciliation, staging rehearsal, and explicit approval, the migration may only create:

- a new article proven absent from Directus;
- new media proven absent from Directus;
- migration-dedicated folders;
- new gallery albums and ordered image relations;
- append-only migration ledger and audit rows.

New content is created as draft by default and published through a separate editorial review.

Production execution must use a dedicated Directus identity with read and create permissions only. The importer must reject any attempted `PATCH`, `PUT`, or `DELETE` request.

Source identity must not be backfilled into protected feed or file rows. A separate append-only ledger records source identity, target identity, matching evidence, run identity, reviewer approval, and verification outcome.

## Alternatives Considered

### Mirror WordPress into Directus

Rejected because Directus contains curated production changes not present in WordPress.

### Upsert by slug or original URL

Rejected because identity does not authorize overwriting the curated target version.

### Backfill WordPress IDs into existing target rows

Rejected because backfill itself modifies protected production artifacts.

### Use `parser.yaml` as the migration database

Rejected because it can be stale, does not prove current target existence, and is not a production audit system.

### Additive-only migration with append-only ledger

Accepted because it protects production work, gives every write provenance, and forces manual review for ambiguous matches.

## Consequences

Benefits:

- manually edited articles and media remain unchanged;
- safety is enforceable through permissions and HTTP-method policy;
- every write is attributable to a migration run;
- source drift cannot silently overwrite target work.

Trade-offs:

- ambiguous matches require manual review;
- safe duplicate media may be accepted rather than risking mutation;
- failed-run files may remain in dedicated migration folders;
- publication is a separate action;
- the process is a migration, not a mirror or synchronization.

## Failure and rollback

The migration does not roll back by deleting created records or files.

On failure, protected baseline objects remain untouched, newly created feeds remain draft, newly created files remain run-owned and reported, and no automatic cleanup occurs. Restoration from backup is exceptional and requires separate approval.

## Verification

Before execution:

- database and upload-volume protection are recorded;
- a baseline fingerprints every protected object;
- reconciliation has no unresolved automatic-write ambiguity;
- the migration identity is proven unable to update or delete;
- staging rehearsal passes with the same code and permission model.

After execution:

- every protected object still exists;
- protected row fingerprints and file checksums are unchanged;
- request audit contains no `PATCH`, `PUT`, or `DELETE`;
- every new object is linked to the run ledger;
- a second reconciliation proposes no duplicate creation for completed source identities.
