# Codex Context

This file gives agents a compact, high-signal understanding of the Club Aviazione Popolare repository and the planned WordPress-to-Directus migration.

## Product Context

- Product: public website for Club Aviazione Popolare.
- Public language: Italian.
- Source website during migration: `https://www.clubaviazionepopolare.org` (WordPress).
- New frontend: Next.js App Router.
- CMS: Directus backed by PostgreSQL.
- Repository and image names intentionally use the existing spelling `club-aviazione-popolare`; do not rename them as part of migration work.
- Default development branch: `develop`.

## Runtime Architecture

- Frontend source: `app/`, `components/`, `lib/`.
- CMS image: `cms/Dockerfile`.
- Local CMS compose file: `cms/docker-compose.yaml`.
- WordPress import utility: `cms/utils/wordpress/`.
- Production frontend: `https://cap.skunklabs.uk`.
- Production Directus: `https://cap-cms.skunklabs.uk`.
- Kubernetes/GitOps deployment is owned by the separate `homelab` repository under `gitops/apps/cap/`.
- Directus uploads are stored on persistent volume `cap-cms-uploads`; the current homelab manifest requests 5 GiB.
- PostgreSQL database name and role are `cap` on the shared CNPG cluster.

## Application Data Model

Relevant Directus collections and system resources inferred from the application:

- `feeds`: articles and article-like content.
- `categories`: feed categories.
- `directus_files`: uploaded media.
- `directus_folders`: virtual media folders.
- `pages` and `page_sections`: static page content.
- `chapters`, `meetings`, menu collections, and metadata: other application content.

Relevant `feeds` fields used by the frontend include:

- `id`;
- `status`;
- `slug`;
- `title`;
- `content`;
- `description`;
- `date`;
- `author`;
- `category`;
- `cover`;
- `featured`;
- `gallery`;
- `original_uri`;
- cover offsets.

The current gallery component resolves a Directus folder by exact slug and renders every file in that folder. New gallery work must preserve the fallback behavior for any existing production gallery.

## Existing WordPress Import Utility

Main files:

- `cms/utils/wordpress/main.py`: Typer CLI and category import orchestration.
- `cms/utils/wordpress/wordpress.py`: WordPress REST retrieval and media download.
- `cms/utils/wordpress/directus.py`: Directus item, folder, and file operations.
- `cms/utils/wordpress/parser.py`: HTML processing, media upload, and local YAML mapping.
- `cms/utils/wordpress/parser.yaml`: historical WordPress-to-Directus mappings.

Current importer behavior that must not be used as production authority:

- WordPress responses are cached with joblib without a migration-run identity.
- `parser.yaml` can cause an item to be skipped without validating the current target record.
- WordPress ID is removed from the Directus payload.
- existing items can be updated by slug or `original_uri`;
- `--overwrite` and `--overwrite-media` enable mutation of existing records;
- thumbnail replacement can delete existing files;
- error fallbacks can remove category/cover or truncate/omit content;
- content and images may be transformed editorially;
- HTTP clients currently disable TLS certificate verification;
- the importer creates an item before media processing and updates it later.

These behaviors are incompatible with the approved additive-only production migration and must be isolated or replaced before execution.

## Fundamental Data Invariant

At the approved baseline timestamp, every existing target feed, file, folder, category relation, and gallery relation becomes a protected production artifact.

Protected production artifacts are target-authoritative even when WordPress differs. They must not be updated, overwritten, renamed, moved, replaced, or deleted by migration tooling.

The migration may create only content proven missing. Ambiguous matches are manual-review items, never automatic writes.

The canonical decision is recorded in `docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md`.

## Members-Only Content

The members-only area is a separate authenticated content scope, not an update
path for already migrated public articles.

Public Directus articles already migrated or editorially updated remain
protected. Members-only WordPress content must be inventoried, reconciled,
modeled, and permissioned as its own authenticated area.

Members-only content should be migrated faithfully first, preserving the source
categories and sections. Any reorganization is a separate editorial follow-up
after the migration is verified.

The members-only area requires a frontend login page and an explicit
authenticated user experience. The authentication mechanism may use an
open-source library or an external service only after checking that its free
tier or self-hosted model fits the expected member count.

Members-only user accounts should be migrated from WordPress. Existing
passwords may be migrated only as password hashes when the chosen
authentication mechanism can verify them safely; plaintext password extraction
or storage is not acceptable. If hash reuse is not supported, the migration
should use an invitation or password-reset flow.

WordPress is the user source only for the initial account migration. After the
bootstrap import, the new authentication system becomes authoritative.
All WordPress users should be inventoried and migrated during the initial
account bootstrap. Target roles and permissions determine post-migration access.
WordPress membership classification is the expected source for mapping users
into the member role. Users without clear membership or editorial-role evidence
receive no private-content access by default.
The exact WordPress membership mechanism is currently uncertain and may come
from a plugin. It must be discovered through read-only inventory of active
plugins, roles, capabilities, and user metadata before role mapping is finalized.
The migration will use a WordPress export rather than direct database access.
The export must include enough evidence for users, password hashes, roles,
capabilities, user metadata, plugin membership data, and private content.
The expected export mechanism is phpMyAdmin. A complete SQL export is preferred;
otherwise the export must include the WordPress users/usermeta tables, content
tables, taxonomy tables, options table, and any plugin membership tables.
The WordPress uploads directory may be large and should not be copied wholesale
unless needed. The migration should first derive a required-media list from the
private content inventory, then retrieve only referenced files through FTP or a
targeted archive.
Temporary FTP access can be used to retrieve referenced WordPress media. FTP
credentials are sensitive run inputs and must not be committed; generated media
lists, transfer logs, and downloaded files belong outside the repository.

The target role model has one frontend members role for private content access
and two editorial profiles for article workflow: redazione and pubblicazione.
Editorial permissions are separate from ordinary member reading access.
Redazione and pubblicazione users use the Directus backend for editorial work;
the frontend `/soci` area is for members-only content access.
The first members frontend account scope includes login, members-only content
reading, and password reset. Editable member profiles are deferred.
Authentication provider selection prioritizes WordPress password-hash
compatibility, then implementation and operational simplicity, current
cost/free-tier fit, and clean integration with `/soci` and Directus.
WordPress password-hash reuse is preferred but not a blocking requirement; an
approved password-reset flow is acceptable if compatible auth options are too
complex or operationally risky.
The preferred auth direction is Directus as the final authoritative auth system
plus a temporary legacy-password bridge that verifies WordPress hashes on first
successful login, then upgrades the user to a normal Directus password.
The first bridge prototype belongs in the Next.js/API layer, close to the
existing login route. A Directus extension remains a later option after the flow
is proven with synthetic hashes.
Legacy WordPress hashes are stored temporarily in a private,
migration-owned Directus collection named `legacy_wordpress_credentials`,
accessible only to backend/service-role code.
The legacy-password transition window is 90 days from go-live; after that,
unconsumed legacy hashes are removed or quarantined and remaining users must
reset their password.

Members-only articles that are already visible to members in WordPress should
be migrated as visible to members after verification. Draft status is reserved
for uncertain, new, or editorially unresolved private content.

The canonical frontend root for the members-only area is `/soci`.
Members-only article routes use `/soci/<categoria>/<slug>`. Route readability is
not a security boundary; authentication and permissions control access.
Anonymous users who request a members-only route are redirected to login and
returned to the originally requested URL after successful authentication.
Authenticated users without the member role receive a simple 403 response in
the first release.
Members-only articles and categories are separate from public articles and
categories. Members-only articles use a dedicated `member_feeds` collection,
and members-only categories use a dedicated `member_categories` collection. This
avoids permission leakage between public and private queries, semantic
collisions with public category slugs, and lets future members-only
reorganization evolve independently from public navigation.

Members-only galleries are not expected in the initial migration. If the
WordPress inventory discovers private galleries, they should use a dedicated
`member_galleries` collection rather than being modeled as `member_feeds`.

Editorial status and audience visibility remain separate concepts. Public
content and members-only content can each have their own workflow state without
using publication status as an access-control boundary.

## Migration Architecture

The intended workflow is:

1. verify database and upload-volume protection;
2. create a read-only target baseline with hashes;
3. create a complete WordPress source inventory without stale cache;
4. reconcile source and target conservatively;
5. manually approve only unambiguous create candidates;
6. rehearse in staging with a create-only Directus role;
7. import new articles and media additively;
8. verify every protected baseline object is byte-for-byte or field-for-field unchanged;
9. preserve an append-only run manifest and ledger;
10. publish new content separately after editorial review.

## Identity And Reconciliation

- `parser.yaml` is evidence only, never source of truth.
- exact `original_uri` is a strong match when unique.
- a validated historical mapping requires corroboration by target existence and metadata.
- slug/title/date/category similarity can produce a candidate, but not an automatic match.
- content hashes are useful for diagnostics but cannot override manually edited Directus content.
- target-only items remain protected.
- WordPress changes to an already matched target are reported as drift only.
- production import requires a durable append-only ledger outside protected feed/file rows.

## Gallery Direction

WordPress gallery content uses `/dt-gallery/...` URLs and may be a custom post type.

Discovery order:

1. inspect `/wp-json/wp/v2/types` and use the REST route when exposed;
2. otherwise use a WordPress export or authenticated source data when available;
3. otherwise scrape the public gallery archive and album pages read-only.

The preferred new target model is an ordered relation between a new gallery feed and Directus files, while retaining the current folder-by-slug fallback for pre-existing galleries. Schema work requires a separate approved task.

## Canonical Migration Documents

- `docs/migrations/wordpress-to-directus/README.md`: entrypoint and status.
- `docs/migrations/wordpress-to-directus/specification.md`: normative requirements.
- `docs/migrations/wordpress-to-directus/plan.md`: atomic execution plan.
- `docs/migrations/wordpress-to-directus/runbook.md`: operator procedure.
- `docs/migrations/wordpress-to-directus/agent-loop.md`: agent-loop task cards.
- `docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md`: durable safety decision.

## Current Gaps

- No approved read-only inventory/reconciliation command exists yet.
- No production baseline manifest exists yet.
- No durable migration ledger has been implemented.
- No safe create-only importer has been implemented.
- Gallery source discovery and target schema are not implemented.
- CMS versions are inconsistent across files: the custom CMS image is pinned, the local compose image is not pinned, and the root package version may differ.
- CI workflows target `main` while the repository default branch is `develop`.
- A credential-like value is present in historical PostgreSQL documentation and must be rotated/removed through a separate security task.

## Near-Term Priorities

1. Review and accept the migration documentation and ADR.
2. Implement source and target inventory commands with tests and no write credentials.
3. Generate a target baseline and reconciliation report in a non-production rehearsal.
4. Decide and implement the append-only migration ledger.
5. Implement a create-only article/media path.
6. Design the ordered gallery relation with legacy fallback.
7. Rehearse in staging before any production action.
