# WordPress to Directus migration

Status: governance and discovery accepted; Task B slices 1-2 implemented; gallery discovery is next. This documentation does not authorize a production run.

Last updated: 2026-06-19

## Goal

Import the articles and galleries still missing from the online WordPress site into Directus while preserving every article, file, folder, cover, category relation, and gallery relation already present in the target.

## Safety invariant

Existing Directus content is production data, not a disposable copy of WordPress.

All target objects captured by the approved baseline are protected production artifacts. A difference in WordPress must be reported, never converted into an update of the target.

The durable decision is recorded in [ADR 0001](../../adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md).

## Document map

- [Read-only discovery](discovery.md): verified repository/public-source contracts, limitations, risks, and Task B scope.
- [Task B slice 1 handoff](task-b-inventory-contracts.md): manifest, canonical hashing, JSONL, pagination, tests, and reviewer checklist.
- [Task B slice 2 handoff](task-b-wordpress-client.md): GET/HEAD-only transport, WordPress REST inventory, source issues, and synthetic HTTP tests.
- [Specification](specification.md): normative behavior, identity rules, write policy, and acceptance criteria.
- [Execution plan](plan.md): canonical binary task plan and phase gates.
- [Operational runbook](runbook.md): operator procedure from backup through post-run verification.
- [Agent Loop](agent-loop.md): task cards for explorer, worker, and reviewer loops.
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
usa agent-loop per Task B slice 3 della migrazione WordPress-to-Directus.
Leggi AGENTS.md, CONTEXT.md, ADR 0001, discovery.md,
task-b-inventory-contracts.md, task-b-wordpress-client.md e tutti i documenti della migrazione.

Obiettivo: implementare soltanto la discovery gallery read-only.
Prima verificare i tipi restituiti da WordPress e individuare un eventuale
custom post type con route `/dt-gallery/`. Quando non è esposto via REST,
usare un parser HTML deterministico per archivio e album pubblici.

Requisiti:
- riusare il transport GET/HEAD-only;
- conservare l'ordine DOM delle immagini;
- estrarre URL originali senza scaricare binari;
- produrre record e source issue usando i manifest contracts;
- usare solo fixture sintetiche nei test;
- non modificare importer legacy, frontend, Directus, schema, permessi o homelab.

Test richiesti: tipo REST esposto/non esposto, archivio vuoto o malformato,
ordine immagini non alfabetico, URL relativo/assoluto, duplicati espliciti,
errori HTTP/HTML e nessun metodo di scrittura.
Restituisci production_artifact_impact, stop_conditions e handoff.
```

## Authority

- Directus is authoritative for content already present in the target.
- WordPress is authoritative only as the source of candidates that may still be missing.
- The operator approves the baseline and reconciliation report.
- A human editor approves publication of newly created feeds.
- Backup, schema apply, permission creation, and production execution require explicit approval.
