# Read-only migration discovery

Status: completed repository/public-source discovery; authenticated Directus inventory still required

Observed: 2026-06-19

## Scope and safety

This discovery was performed under ADR 0001 and the repository `AGENTS.md` rules.

Actions performed:

- read repository documentation and source code;
- read the public WordPress website and public gallery pages;
- inspect deployment manifests in the separate `homelab` repository read-only;
- inspect the historical `parser.yaml` mapping read-only.

Actions not performed:

- no Directus create, update, or delete request;
- no WordPress write request;
- no schema or permission change;
- no importer execution;
- no database, PVC, backup, or deployment action;
- no production inventory or article body committed to Git.

`production_artifact_impact: none`

## Executive findings

1. The remaining migration cannot use the existing importer as a production executor because it contains update, overwrite, delete, content fallback, media replacement, stale-cache, and create-then-update behavior.
2. WordPress categories overlap. A post may be in News and also Notiziari, Eventi, Corsi, Storie dei Soci, or Raduni. Category membership is evidence and classification input, not a unique source partition.
3. The public WordPress gallery currently exposes seven album pages under `/dt-gallery/...`.
4. Gallery order is semantic. At least one album has a visibly non-alphabetical image sequence, while the current frontend gallery sorts Directus files by title and filename.
5. The frontend resolves feeds globally by slug even inside category routes. Slug and route collision detection must therefore be global.
6. The current gallery frontend finds a Directus folder whose name exactly equals the feed slug. The article importer creates a different folder naming convention, so the two contracts are not interchangeable.
7. No Directus schema snapshot is versioned in this repository. The exact production schema, constraints, relations, states, permissions, and Directus runtime version require an authenticated read-only inventory.
8. The custom CMS image is pinned in source, but production deploys a mutable `latest` image. The repository alone cannot prove the exact Directus version running in production.
9. `parser.yaml` is useful historical evidence but cannot prove that a mapped Directus ID still exists or still represents the same item in the current target.
10. Task B should implement fresh read-only source and target clients, deterministic manifests, and count validation before reconciliation logic or any write path.

## Evidence sources

### Repository

- `AGENTS.md`
- `CONTEXT.md`
- `docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md`
- `cms/utils/wordpress/main.py`
- `cms/utils/wordpress/wordpress.py`
- `cms/utils/wordpress/directus.py`
- `cms/utils/wordpress/parser.py`
- `cms/utils/wordpress/parser.yaml`
- `cms/utils/wordpress/README.md`
- `lib/types.ts`
- `lib/server.ts`
- `components/gallery.tsx`
- `app/news/[id]/page.tsx`
- `app/feed/[category]/[slug]/page.tsx`
- `next.config.mjs`
- `cms/Dockerfile`
- `cms/docker-compose.yaml`
- `.github/workflows/build-and-deploy.yml`

### Public WordPress pages

- `https://www.clubaviazionepopolare.org/`
- `https://www.clubaviazionepopolare.org/news/`
- `https://www.clubaviazionepopolare.org/notiziari/`
- `https://www.clubaviazionepopolare.org/attivita/`
- `https://www.clubaviazionepopolare.org/attivita/storiedeisoci/`
- `https://www.clubaviazionepopolare.org/corsi/`
- `https://www.clubaviazionepopolare.org/raduni/`
- `https://www.clubaviazionepopolare.org/gallery/`
- `https://www.clubaviazionepopolare.org/dt-gallery/49-raduno-cap-ozzano-emilia-10-11-12-settembre-2021/`

Public HTML is discovery evidence only. Complete source totals and REST contracts must be captured by the Task B inventory client.

## WordPress source contract

### Posts

The existing client reads:

```text
https://www.clubaviazionepopolare.org/wp-json/wp/v2/posts
```

with `per_page=100`, page pagination, and `_embed=true`.

It currently maps:

- WordPress ID;
- publication date;
- canonical link;
- status;
- slug;
- rendered title and content;
- category IDs;
- embedded featured-media URL.

The new inventory must additionally capture:

- `modified` and `modified_gmt`;
- post type;
- excerpt;
- tags;
- featured-media attachment ID;
- inline image and attachment URLs;
- pagination totals from the same `per_page=100` response series;
- source errors;
- a deterministic record hash.

The current `get_posts()` result is cached with joblib and has no refresh or run identity. The Task B path must use fresh reads by default.

### Categories and overlap

The historical importer recognizes these WordPress category IDs:

| WordPress ID | Historical label | Existing target mapping intention |
|---:|---|---|
| 3 | Eventi - Attività | News |
| 5 | Corsi di aggiornamento | Corsi |
| 6 | News | News |
| 8 | Raduni - Efficiency Race | News |
| 15 | Notiziari | Notiziari |

Category 14, Storie dei Soci, is present in comments/history but is not active in the current category constant.

Public archive evidence confirms overlapping category membership:

- Notiziari may also be News.
- Eventi may also be News and Raduni.
- Corsi may also be News.
- Storie dei Soci may also be News.

Consequences:

- do not run independent category imports that race to claim or overwrite the same source post;
- inventory each WordPress post once with its complete category set;
- apply one deterministic target classification rule during reconciliation;
- retain the complete source category set in the run artifacts and future ledger;
- classify uncertain category mapping for review rather than updating an existing feed.

### Recommended discovery scope

For inventory, use all WordPress posts with `status=publish` and retain all category IDs.

This is intentionally broader than the final write scope. Exclusions belong in reconciliation, not in source retrieval, because a narrow category query can hide overlapping posts.

Final target category selection remains a Phase 0 decision and must not be inferred by the inventory client.

## WordPress gallery contract

The public gallery archive exposes seven albums at the observation date:

1. `53° Raduno CAP – Reggio Emilia 5-6-7/9-2025`
2. `52° Raduno CAP LILH – 6/7/8-9-2024`
3. `49° Raduno CAP – OZZANO EMILIA 10/11/12 Settembre 2021`
4. `Foto Fly-In Vichy 2007`
5. `Foto Raduno 2002`
6. `Foto Raduno 2001`
7. `Foto recenti`

Album routes use `/dt-gallery/<slug>/`, which proves a separate public gallery content route but not its REST `rest_base` or `show_in_rest` setting.

The 49th Raduno album begins in this order:

```text
IMG_3161
IMG_3175
IMG_3174
IMG_3160
IMG_3159
```

This is not filename order. Source DOM order must be captured as explicit `sort` data.

Task B discovery order:

1. request `/wp-json/wp/v2/types`;
2. identify a type whose public or REST base corresponds to `dt-gallery`;
3. use the exposed REST endpoint when available;
4. otherwise record that an authenticated WordPress export is preferred;
5. use the public archive and album HTML as the read-only fallback;
6. extract original image links, not only thumbnails;
7. retain album and image order exactly.

REST exposure remains unverified in this discovery environment.

## Directus target contract inferred from code

### Collections and resources

The frontend and importer reference:

- `feeds`;
- `categories`;
- `directus_files`;
- `directus_folders`;
- pages and page sections;
- other site collections not directly in migration scope.

Relevant feed fields inferred from `lib/types.ts` and queries:

```text
id
status
slug
title
content
description
date
author
category
cover
featured
gallery
original_uri
cover_offset_x
cover_offset_y
```

This is an inferred application contract, not an authoritative schema snapshot.

### Missing schema evidence

The repository does not contain a Directus schema snapshot or migration history sufficient to prove:

- field types and maximum lengths;
- required and nullable fields;
- unique constraints;
- category relation cardinality;
- gallery relation availability;
- all status values;
- public/read-only role access;
- file and folder relation rules;
- event hooks or flows that run on create;
- exact production Directus version.

Task B requires a dedicated read-only identity capable of reading:

- schema metadata needed for these collections;
- all feed statuses in scope;
- categories and relations;
- Directus file/folder metadata;
- permission evidence relevant to inventory.

It must not have create, update, delete, schema mutation, settings, user, role, policy, or permission-management capabilities.

## Frontend identity and route contract

### Feed lookup

`getFeedBySlug()` queries the `feeds` collection by `slug` and returns the first published result. It does not scope the lookup by category.

Both of these routes depend on that global lookup:

```text
/news/<id-or-slug>
/feed/<category>/<slug>
```

The category segment in `/feed/<category>/<slug>` is presentation context, not part of feed identity.

Consequences:

- target feed slugs must be treated as globally collision-sensitive;
- reconciliation must query all statuses, because a draft slug can collide before publication;
- numeric strings also need review because `/news/[id]` interprets numeric values as Directus IDs first;
- static top-level routes must be reserved when a future redirect or alternate route could shadow them;
- creation must stop on any exact or normalized slug/route collision.

### Static route inventory relevant to collisions

Repository routes include at least:

```text
/
/news
/news/[id]
/feed/[category]
/feed/[category]/[slug]
/trofei/[slug]
/associazioni
/associazioni/[slug]
/efficiency-race
/eventi
/contatti
/area-soci
/cosa-facciamo
/costruire-un-aereo
/la-nostra-storia
/albo-storico
/flotta
/organigramma
/login
```

No dedicated `/gallery` route is present in the current repository search results.

The future route inventory should be generated from the repository instead of maintained manually.

## Current gallery frontend contract

`components/gallery.tsx`:

1. receives a feed slug;
2. calls `getFolderBySlug(slug)`;
3. resolves the first Directus folder whose **name** exactly equals the slug;
4. fetches every file in that folder;
5. renders links and images from Directus assets.

`getFiles()` sorts by:

```text
title
filename_download
```

This order is incompatible with WordPress album order when that order is non-alphabetical.

The existing article importer creates media folders named:

```text
YYYY-MM-<directus-id>-<slug>
```

That folder cannot be discovered by the gallery component's exact-slug folder lookup.

Legacy preservation requirement:

- do not rename or move existing gallery folders;
- do not change existing file ordering or metadata;
- retain exact-slug folder lookup as fallback;
- add ordered relation rendering only for newly created galleries after separate schema review.

## Existing importer risk inventory

### State and identity

- `parser.yaml` maps WordPress ID to Directus ID but has no environment identity.
- Mapping lookup does not first prove that the target record still exists and matches.
- `id_wordpress` is removed from the Directus item payload.
- Matching falls back to `original_uri`, then slug.
- Historical mappings reach WordPress content from 2011 through December 2025, but coverage does not prove current target completeness.

Classification rule for Task B:

- `parser.yaml` is imported as an optional evidence source;
- every mapped target ID must be looked up in the current target;
- URL, slug, and selected metadata must corroborate the mapping;
- missing or conflicting targets become `stale_historical_mapping` or manual review;
- the YAML file must never cause a source record to be skipped by itself.

### Mutation paths

The legacy implementation includes:

- item update and delete;
- file and folder delete;
- overwrite flags;
- thumbnail replacement by deleting an existing file;
- create-or-update behavior by slug;
- create item before media processing, then update it;
- forced `published` status;
- fallback payloads that remove category or cover;
- fallback payloads that truncate or omit content;
- AI formatting;
- heuristic image removal;
- TLS verification disabled.

None of these paths may be imported into the Task B read-only client.

### Cover and media behavior

The legacy parser may choose the largest uploaded image as cover instead of preserving the WordPress featured image. It also removes the selected cover image from article HTML.

Task B must inventory featured-media identity separately from inline media. It performs no cover selection and no HTML transformation.

## Deployment and version findings

- `cms/Dockerfile` pins a Directus base image.
- `cms/docker-compose.yaml` uses an unpinned Directus image.
- the root application package declares a Directus dependency that may not match the CMS image.
- the production Kubernetes manifest in `homelab` deploys the custom CMS image using the mutable `latest` tag.
- the repository workflow targets `main`, while the repository default branch is `develop`.

Therefore the exact production CMS version and image digest cannot be established from source alone.

Task B target inventory metadata must record:

- `/server/info` result when permitted;
- deployed image digest or immutable image reference from an approved runtime check;
- schema metadata hash;
- target base URL;
- inventory timestamp.

No deployment manifest change belongs in Task B.

## Verified and unverified matrix

| Area | Status | Evidence / next action |
|---|---|---|
| Additive-only target invariant | Verified | ADR 0001 accepted and merged |
| Existing importer mutation risk | Verified | Repository source review |
| WordPress public post archives | Verified | Public HTML |
| Category overlap | Verified | Public archive labels and importer constants |
| Public gallery archive | Verified | Seven public album cards |
| Gallery route form | Verified | `/dt-gallery/<slug>/` public pages |
| Gallery source order semantic | Verified | 49th Raduno public album order |
| Gallery REST exposure | Unverified | Probe `/wp-json/wp/v2/types` in Task B |
| Exact WordPress post/media totals | Unverified | Fresh REST inventory required |
| Directus collection fields and constraints | Partially inferred | Read-only schema inventory required |
| Existing Directus record counts and states | Unverified | Authenticated read-only inventory required |
| Current `parser.yaml` target validity | Unverified | Revalidate against current target |
| Exact production Directus version | Unverified | Runtime info/image digest required |
| Production permission model | Unverified | Read-only permission report required |
| Existing gallery folders and files | Unverified | Read-only target inventory required |

## Task B implementation scope

### Goal

Build deterministic, fresh, read-only source and target inventory libraries and tests. Do not implement reconciliation or writes in the same task.

### Recommended slices

1. Common manifest models, canonical JSON, hashing, pagination result, and error model.
2. WordPress read-only client for types, categories, posts, media, and gallery type discovery.
3. Public gallery HTML fallback parser with explicit image order.
4. Directus read-only client for server metadata, schema metadata, feeds, categories, files, folders, and relevant relations.
5. Route inventory helper or static route manifest used only for later collision checks.
6. Tests and fixtures using synthetic data only.
7. CLI commands that write controlled manifests outside Git.

Each slice should be a separate agent-loop worker task when it touches shared contracts.

### Allowed files

```text
cms/utils/wordpress/inventory/**
cms/utils/wordpress/tests/**
cms/utils/wordpress/pyproject.toml
docs/migrations/wordpress-to-directus/**
```

A minimal CLI registration change in `cms/utils/wordpress/main.py` is allowed only in a final isolated slice after the inventory libraries and tests pass. It must expose read-only commands and must not call legacy mutation helpers.

### Forbidden files and behavior

```text
cms/utils/wordpress/parser.yaml
cms/utils/wordpress/ai.py
cms/utils/wordpress/ai-models.yaml
cms/utils/wordpress/fix_author.py
cms/utils/wordpress/directus.py mutation functions
cms/utils/wordpress/parser.py mutation/media-processing flow
lib/**
components/**
app/**
cms schema or extensions
homelab repository
```

Forbidden runtime behavior:

- any `POST`, `PATCH`, `PUT`, or `DELETE`;
- any Directus or WordPress write credential;
- stale joblib cache by default;
- production manifests committed to Git;
- article content logging;
- automatic classification as missing;
- update, overwrite, cleanup, deduplication, or publication.

### Verification commands

From `cms/utils/wordpress`:

```bash
uv run pytest tests/test_manifest.py tests/test_wordpress_inventory.py tests/test_gallery_discovery.py tests/test_directus_inventory.py
uv run python -m compileall inventory tests
```

Before opening the Task B PR, also verify that the changed-file list contains only the approved paths.

### Stop conditions

Stop and return to explorer when:

- complete WordPress pagination cannot be proven;
- gallery REST and HTML sources disagree without an explicit error state;
- target inventory requires a token broader than read-only;
- drafts or relevant relations cannot be read;
- schema metadata is unavailable and inferred fields would become authoritative;
- a client code path can emit a non-read method;
- fixtures contain copied production article bodies or credentials;
- route inventory cannot distinguish static and dynamic collision rules;
- historical mappings are used to skip current target validation.

## Open decisions

1. Final article target-category precedence remains to be confirmed. Inventory should remain category-neutral.
2. Operator and independent reviewer identities for baseline and production approval remain to be assigned.
3. The exact mechanism for obtaining a read-only Directus token and runtime image digest requires an operational decision outside this repository task.
4. Gallery REST exposure remains to be probed by the Task B source client.
5. The append-only ledger schema is intentionally deferred to Phase 6.

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/migrations/wordpress-to-directus/*
  - cms/utils/wordpress/*
  - lib/types.ts
  - lib/server.ts
  - components/gallery.tsx
  - app/news/[id]/page.tsx
  - app/feed/[category]/[slug]/page.tsx
  - next.config.mjs
  - cms/Dockerfile
  - cms/docker-compose.yaml
  - .github/workflows/build-and-deploy.yml
files_changed:
  - docs/migrations/wordpress-to-directus/discovery.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/README.md
findings:
  - Public WordPress categories overlap and must not drive independent destructive imports.
  - Seven public gallery albums use dt-gallery routes.
  - Source gallery order is semantic and current Directus folder sorting cannot preserve it.
  - Feed slug identity is global across category routes.
  - Existing importer and historical cache cannot be used as production authority.
  - Full target discovery needs a strict read-only Directus identity.
verification:
  - Repository and public-source reads only.
  - No source, target, schema, permission, deployment, database, or media write.
  - No production inventory or content added to Git.
production_artifact_impact: none
risks:
  - Directus runtime/schema/permission facts remain unverified until authenticated read-only inventory.
  - Mutable production image tag prevents source-only version proof.
  - Gallery schema design remains a later separately approved task.
open_questions:
  - Target-category precedence.
  - Operator/reviewer assignment.
  - Read-only Directus credential provisioning.
next_action: Implement Task B read-only inventory contracts and synthetic-data tests in serial agent-loop slices.
```
