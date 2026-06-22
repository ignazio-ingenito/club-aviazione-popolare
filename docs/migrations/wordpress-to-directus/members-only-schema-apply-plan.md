# Members-only Directus schema apply plan

Status: approved to prepare schema apply; production apply pending schema-capable token and preflight gates

Date: 2026-06-22

## Purpose

This plan turns the approved `member_*` schema direction into an operational
schema-apply sequence for Directus.

It does not authorize content import, user import, media upload, password-hash
migration, role assignment, or frontend publication.

## Approved scope

Create new migration-owned collections only:

- `member_categories`
- `member_topics`
- `member_feeds`
- `member_feeds_files`
- `member_feeds_topics`
- `legacy_wordpress_credentials`

Defer:

- `member_galleries`, unless private galleries are discovered and separately
  approved.
- editorial role mapping for `redazione` and `pubblicazione`.
- any mutation of existing public `feeds`, `categories`, files, folders, pages,
  menu, chapters, meetings, metadata, or reference records.

## Required preflight evidence

Before production schema apply:

- approved schema document commit;
- fresh Directus schema baseline hash;
- fresh Directus application inventory hash;
- production backup or infrastructure-approved rollback evidence;
- schema-capable Directus token stored outside Git;
- dry-run schema plan artifact stored outside Git;
- operator approval and reviewer approval recorded in the run directory.

Stop if the active token can update or delete existing application content while
also applying schema. Schema apply should use an administrator/schema token only
for schema setup, then the token must be discarded or rotated out of the run.

## Collection creation order

1. `member_categories`
2. `member_topics`
3. `member_feeds`
4. `member_feeds_files`
5. `member_feeds_topics`
6. `legacy_wordpress_credentials`

Create base collections first, then relation fields and junction collections.

## Field model

### `member_categories`

Primary key:

- `id`: uuid primary key

Fields:

- `status`: string, required
- `slug`: string, required, unique
- `title`: string, required
- `description`: text, optional
- `sort`: integer, optional
- `source_system`: string, required
- `source_identity`: string, optional
- `source_slug`: string, optional

Initial record to create later during content bootstrap:

- `slug`: `sport-aviation`
- `title`: `Sport Aviation`
- `source_system`: `wordpress`

### `member_topics`

Primary key:

- `id`: uuid primary key

Fields:

- `slug`: string, required, unique
- `title`: string, required
- `source_taxonomy`: string, required
- `source_identity`: string, required, unique
- `sort`: integer, optional

### `member_feeds`

Primary key:

- `id`: uuid primary key

Fields:

- `status`: string, required
- `visibility`: string, required
- `slug`: string, required
- `title`: string, required
- `description`: text, optional
- `content`: text, required
- `content_format`: string, required
- `date`: datetime, optional
- `modified_source_at`: datetime, optional
- `author`: string, optional
- `category`: many-to-one to `member_categories`, required
- `cover`: many-to-one to `directus_files`, optional
- `source_system`: string, required
- `source_identity`: string, required, unique
- `source_post_type`: string, required
- `source_url`: string, optional
- `source_hash`: string, required
- `migration_run_id`: string, required

Route uniqueness requirement:

- `category + slug` must be unique.

Directus may require this composite uniqueness to be enforced outside the schema
API if the UI/API does not expose composite constraints. If so, migration code
must perform a pre-create uniqueness check and fail closed on duplicate route
keys.

### `member_feeds_files`

Primary key:

- `id`: uuid primary key

Fields:

- `member_feed`: many-to-one to `member_feeds`, required
- `file`: many-to-one to `directus_files`, required
- `sort`: integer, required
- `source_identity`: string, required

### `member_feeds_topics`

Primary key:

- `id`: uuid primary key

Fields:

- `member_feed`: many-to-one to `member_feeds`, required
- `member_topic`: many-to-one to `member_topics`, required

### `legacy_wordpress_credentials`

Primary key:

- `id`: uuid primary key

Fields:

- `directus_user`: many-to-one to `directus_users`, required
- `wordpress_user_id`: integer, required, unique
- `legacy_hash`: string, required
- `hash_format`: string, required
- `status`: string, required
- `consumed_at`: datetime, optional
- `expires_at`: datetime, required
- `source_hash`: string, required
- `migration_run_id`: string, required

Security boundary:

- no public, member, redazione, or pubblicazione policy may read this
  collection;
- only backend/service-role code may read it;
- no frontend route may query it directly.

## Policy setup sequence

1. Create or verify `member` role/policy.
2. Deny anonymous read access to all `member_*` collections.
3. Deny generic authenticated non-member read access to all `member_*`
   collections.
4. Grant `member` read access to:
   - `member_categories`
   - `member_topics`
   - `member_feeds` filtered to member-visible records
   - `member_feeds_files`
   - `member_feeds_topics`
   - referenced `directus_files` needed by member articles
5. Grant no frontend/member access to `legacy_wordpress_credentials`.
6. Defer `redazione` and `pubblicazione` permissions until editorial mapping is
   manually approved.

If Directus 11 policy resources differ between UI labels and API resources,
capture the exact API resources in a read-only permission inventory before
applying policy changes.

## Dry-run artifact

The schema apply tool must write a dry-run artifact outside Git containing:

- run id;
- Directus base URL;
- observed Directus version;
- current schema collection list;
- proposed collections;
- proposed fields;
- proposed relations;
- proposed policies;
- exact planned HTTP method and endpoint for every request;
- redacted token evidence, never the token value;
- stop conditions triggered or cleared.

The dry-run must not send any non-read request.

## Apply rules

Production apply must:

- create only missing `member_*` schema objects;
- never update existing public/application schema;
- stop if any target `member_*` collection already exists with incompatible
  fields or relations;
- stop if `legacy_wordpress_credentials` cannot be proven backend-only;
- stop if the token lacks schema privileges;
- stop if applying schema would require modifying existing `feeds`,
  `categories`, `directus_files`, `directus_folders`, `pages`, or menu
  collections.

## Post-apply verification

After schema apply:

- capture a fresh Directus schema inventory;
- verify all `member_*` collections exist;
- verify all relations exist;
- verify public application collections have unchanged field/relation
  fingerprints;
- verify `legacy_wordpress_credentials` has no public/member read access;
- verify no content records were created;
- verify no existing content records were updated or deleted.

## Next implementation task

Implement a schema plan generator with:

- default dry-run mode;
- `--apply` explicit execution flag;
- token read from an environment variable or protected file outside Git;
- request log with methods and endpoints only;
- tests proving dry-run emits no non-read requests;
- tests proving the executor never emits `PATCH`, `PUT`, or `DELETE`;
- tests proving incompatible existing `member_*` schema fails closed.
