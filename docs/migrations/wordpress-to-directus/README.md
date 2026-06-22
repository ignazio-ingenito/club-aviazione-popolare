# WordPress to Directus migration

Status: governance and discovery accepted; Task B inventory implementation complete; authenticated live read-only inventories, baseline review notes, create-only client notes, approved write-manifest notes, permission-gate notes, and reconciliation artifacts are captured outside Git. This documentation does not authorize a production run.

Last updated: 2026-06-20

## Goal

Import the articles and galleries still missing from the online WordPress site into Directus while preserving every article, file, folder, cover, category relation, and gallery relation already present in the target.

## Safety invariant

Existing Directus content is production data, not a disposable copy of WordPress.

All target objects captured by the approved baseline are protected production artifacts. A difference in WordPress must be reported, never converted into an update of the target.

The durable decision is recorded in [ADR 0001](../../adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md).

## Document map

- [Read-only discovery](discovery.md): verified repository/public-source contracts, limitations, risks, and Task B scope.
- [Task B slice 1 handoff](task-b-inventory-contracts.md): manifest, canonical hashing, JSONL, pagination, tests, and reviewer checklist.
- [Task B slice 3 handoff](task-b-gallery-discovery.md): REST-first gallery discovery, ordered public-HTML fallback, tests, and reviewer checklist.
- [Task B slice 4 handoff](task-b-directus-inventory.md): anonymous/read-only Directus inventory client, inaccessible endpoint issues, tests, and reviewer checklist.
- [Task B slice 5 handoff](task-b-route-inventory.md): repository route inventory, collision input contract, tests, and reviewer checklist.
- [Task B slice 6 handoff](task-b-cli-integration.md): read-only CLI integration, atomic manifest writer, checksum sidecars, tests, and reviewer checklist.
- [Task B slice 7 handoff](task-b-wxr-media-inventory.md): local WordPress WXR media export inventory for REST-private attachments.
- [Task B reconciliation handoff](task-b-reconciliation.md): reconciliation states, parser.yaml corroboration only, review gates, and write-manifest boundary.
- [Task B target baseline review](task-b-target-baseline.md): authenticated baseline review, duplicate-file evidence, and approval gate.
- [Task B create-only Directus client](task-b-create-only-directus-client.md): method/endpoint allowlist and future write-safety wrapper.
- [Task B approved write-manifest selection](task-b-write-manifest.md): candidate-only manifest selection and record gate.
- [Task B permission gate](task-b-permission-gate.md): fail-closed permission evidence validation for future execution identities.
- [Task B draft-only create-manifest executor](task-b-create-manifest-executor.md): approved artifact validation, dry-run reports, request plan, and execution gate.
- [Members-only migration specification](members-only-spec.md): `/soci` scope, account migration, auth, private content model, and media retrieval.
- [WordPress media retrieval report](media-retrieval-report.md): aggregate media counts, retrieval strategy, and rclone-oriented next steps.
- [Members-only agent-loop plan](members-only-agent-loop-plan.md): bounded `/soci` and `articoli-tecnici` task plan with parallel explorer guidance.
- [Members-only schema proposal](members-only-schema-proposal.md): proposed Directus collections, fields, and access boundaries for `/soci`.
- [Members-only schema apply plan](members-only-schema-apply-plan.md): operational sequence, gates, and stop conditions for applying the approved `member_*` schema.
- [Specification](specification.md): normative behavior, identity rules, write policy, and acceptance criteria.
- [Execution plan](plan.md): canonical binary task plan and phase gates.
- [Operational runbook](runbook.md): operator procedure from backup through post-run verification.
- [Agent Loop](agent-loop.md): task cards for explorer, worker, and reviewer loops.
- [ADR 0002](../../adr/0002-use-directus-auth-with-temporary-wordpress-password-bridge.md): Directus auth with a temporary WordPress password bridge for `/soci`.
- [`AGENTS.md`](../../../AGENTS.md): repository-wide agent constraints.
- [`CONTEXT.md`](../../../CONTEXT.md): compact product, architecture, and migration context.

## Scope

Included:

- published WordPress posts in the approved categories;
- featured images, inline images, and required attachments for missing articles;
- public gallery albums and ordered gallery images;
- read-only source and target inventories;
- conservative reconciliation against existing Directus artifacts;
- an append-only migration ledger;
- reconciliation before write-manifest construction;
- additive creation of approved missing content;
- proof that protected target artifacts did not change.

Excluded:

- synchronizing source changes into existing Directus records;
- deleting or deduplicating existing content;
- changing existing categories, covers, files, folders, or galleries;
- AI rewriting or editorial formatting during migration;
- automatic publication without editorial review;
- WordPress shutdown, redirects, or DNS cutover;
- production schema or permission changes without a separate approval gate.

## Operating sequence

1. Review and accept the documentation and ADR.
2. Implement read-only source and target discovery.
3. Verify database backup and upload-volume protection.
4. Capture and approve an immutable target baseline.
5. Build a complete source inventory without stale cache.
6. Produce and review the reconciliation report.
7. Rehearse in staging with the same create-only permission model.
8. Import only explicitly approved create candidates.
9. Verify that all baseline fingerprints and checksums are unchanged.
10. Publish newly created drafts through a separate editorial action.

No phase implies approval for the next phase.

## Existing importer status

The utility under `cms/utils/wordpress/` is useful for discovery but is not approved for production execution in its current form. It contains update, overwrite, replacement, delete, cache, and content-fallback behavior that conflicts with ADR 0001.

Useful parsing and download logic may be reused only after unsafe paths are isolated behind new create-only interfaces and covered by tests.

## Recommended next Agent Loop prompt

```text
usa agent-loop per inventari live read-only della migrazione WordPress-to-Directus.
Leggi AGENTS.md, CONTEXT.md, ADR 0001, discovery.md,
task-b-inventory-contracts.md e tutti i documenti della migrazione.

Obiettivo: eseguire inventari WordPress, gallery, route e public-view Directus
con la CLI read-only, salvando gli artifact fuori Git in una run directory
controllata.

Prima usa explorer read-only. Poi esegui solo comandi CLI GET/HEAD.
Allowed files: nessuna modifica repo richiesta salvo handoff/report sintetici.
Forbidden: parser.yaml, importer legacy, AI, Directus writes, frontend
behavior changes, schema apply, permessi, homelab, dati di produzione e
inventari live in Git.
Nessun metodo HTTP diverso da GET/HEAD.

Verifica richiesta: checksum `.sha256`, conteggi per manifest, issue fatali
esplicite per endpoint Directus anonimi non leggibili, e dichiarazione che
il public-view Directus non è una baseline approvabile.
Restituisci production_artifact_impact, stop_conditions e handoff.
```

## Authority

- Directus is authoritative for content already present in the target.
- WordPress is authoritative only as the source of candidates that may still be missing.
- The operator approves the baseline and reconciliation report.
- A human editor approves publication of newly created feeds.
- Backup, schema apply, permission creation, and production execution require explicit approval.
