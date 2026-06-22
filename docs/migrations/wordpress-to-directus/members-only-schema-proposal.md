# Members-only Directus schema proposal

Status: proposal, not applied

Date: 2026-06-22

## Purpose

This document proposes the Directus collections and permission model needed for
the first `/soci` release.

It does not authorize schema apply, permission changes, user migration, content
import, media upload, or production execution.

## Source decisions

- Public Directus `feeds` and `categories` remain protected and unchanged.
- Members-only content uses dedicated collections.
- `member_feeds.content` stores sanitized HTML, not Markdown.
- The source-backed route slug for the `articoli-tecnici` content family is
  `sport-aviation`.
- WordPress `argomento` terms are secondary topics/filters, not the top-level
  `/soci/<categoria>` route segment.
- Member bootstrap evidence is `soci_cap` plus `pw_user_status=approved`.
- Editorial role split into `redazione` and `pubblicazione` is not provable
  from the SQL export and remains manual-review.

## Proposed collections

### `member_categories`

Purpose: top-level members-only route categories.

Initial record expected:

- `slug`: `sport-aviation`
- `title`: editorial decision; source-backed short label is `Sport Aviation`
- `description`: optional editorial text

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `status` | string | yes | Draft/published workflow state, not access boundary. |
| `slug` | string | yes | Unique route segment under `/soci`. |
| `title` | string | yes | Human label. |
| `description` | text | no | HTML or plain text per Directus editor choice. |
| `sort` | integer | no | Navigation ordering. |
| `source_system` | string | yes | Constant `wordpress`. |
| `source_identity` | string | no | Optional, for source category/page provenance. |
| `source_slug` | string | no | WordPress source slug when applicable. |
| `date_created` / `date_updated` | system | yes | Directus system fields. |

Constraints:

- `slug` unique.
- Do not reuse public `categories` rows.

### `member_topics`

Purpose: secondary topic/filter taxonomy derived from WordPress `argomento`.

This avoids overloading `member_categories` with 31 topical terms while still
preserving source structure.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `slug` | string | yes | Source `argomento` slug. |
| `title` | string | yes | Source term name. |
| `source_taxonomy` | string | yes | Constant `argomento`. |
| `source_identity` | string | yes | Example `wordpress:taxonomy:argomento:<slug>`. |
| `sort` | integer | no | Optional UI ordering. |

Constraints:

- `slug` unique within `member_topics`.

### `member_feeds`

Purpose: members-only articles.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `status` | string | yes | Editorial workflow state. |
| `visibility` | string | yes | `members` for verified imported content; separate from status. |
| `slug` | string | yes | Unique within category. |
| `title` | string | yes | Source title unless later editorial task changes it. |
| `description` | text | no | Source excerpt or generated preview if approved. |
| `content` | text | yes | Sanitized/preserved HTML. |
| `content_format` | string | yes | Constant `html`. |
| `date` | datetime | no | Source publish date. |
| `modified_source_at` | datetime | no | Source modified date. |
| `author` | string | no | Source author label when available. |
| `category` | many-to-one | yes | `member_categories`. |
| `topics` | many-to-many | no | `member_topics`, preserving `argomento`. |
| `cover` | many-to-one | no | Directus file, if source cover exists. |
| `attachments` | many-to-many | no | Directus files for PDF/DOCX/XLSX attachments. |
| `source_system` | string | yes | Constant `wordpress`. |
| `source_identity` | string | yes | Example `wordpress:articoli-tecnici:<id>`. |
| `source_post_type` | string | yes | `articoli-tecnici`. |
| `source_url` | string | no | Source permalink. |
| `source_hash` | string | yes | Deterministic content/source hash from inventory. |
| `migration_run_id` | string | yes | Run provenance. |
| `date_created` / `date_updated` | system | yes | Directus system fields. |

Constraints:

- Unique route key: `category + slug`.
- Unique source identity: `source_system + source_identity`.
- `content_format` must be `html` for the first release.

Import behavior:

- Create only.
- Initial verified content may be member-visible after verification.
- Uncertain content remains non-visible until reviewed.
- No AI rewrite, Markdown conversion, or editorial normalization during import.

### `member_feeds_files`

Purpose: ordered attachment relation between `member_feeds` and Directus files.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `member_feed` | many-to-one | yes | Parent article. |
| `file` | many-to-one | yes | Directus file. |
| `sort` | integer | yes | Source order or deterministic import order. |
| `source_identity` | string | yes | WordPress media identity. |

### `member_feeds_topics`

Purpose: many-to-many relation between articles and `member_topics`.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `member_feed` | many-to-one | yes | Parent article. |
| `member_topic` | many-to-one | yes | Topic. |

### `member_galleries`

Purpose: deferred. Use only if private galleries are discovered.

The current `articoli-tecnici` evidence is PDF/DOCX/XLSX-heavy and does not
require `member_galleries` for the first `sport-aviation` batch.

### `legacy_wordpress_credentials`

Purpose: temporary private store for WordPress password hashes during the
90-day legacy-password bridge.

Fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | uuid or integer | yes | Directus primary key. |
| `directus_user` | many-to-one | yes | Target Directus user. |
| `wordpress_user_id` | integer | yes | Source user id. |
| `legacy_hash` | string | yes | WordPress password hash. Never exposed to frontend. |
| `hash_format` | string | yes | `$wp`, `$P$`, `md5`, or `unsupported`. |
| `status` | string | yes | `unused`, `consumed`, `quarantined`, `expired`. |
| `consumed_at` | datetime | no | Set after successful bridge login. |
| `expires_at` | datetime | yes | 90 days after go-live. |
| `source_hash` | string | yes | Hash of source credential record, not plaintext password. |
| `migration_run_id` | string | yes | Run provenance. |

Access rule:

- Backend/service-role only.
- No public, member, redazione, or pubblicazione read access.
- No frontend query path may expose this collection.

## Roles and policies

Initial target roles:

- `member`: read verified members-only content.
- `redazione`: editorial backend work; mapping requires manual review.
- `pubblicazione`: publication/approval backend work; mapping requires manual
  review.

Proposed read policy:

- Anonymous: no read access to `member_*`.
- Authenticated without `member`: no read access to `member_*`; frontend returns
  simple 403.
- `member`: read `member_categories`, `member_topics`, and member-visible
  `member_feeds`.
- `redazione` / `pubblicazione`: backend permissions to be designed after
  editorial mapping is approved.

## Directus system evidence still useful

The current read-only token exposed enough schema metadata for existing
application collections. Before applying permissions, request read access to
the current Directus auth/policy system resources for a dry schema review:

- roles;
- policies;
- role-policy/user-policy access mapping;
- users only as aggregate counts or selected migration-owned test users.

Exact API/table names depend on the Directus version and should be verified
against the running instance before asking for a production export.

## Open questions

- Final display label: `Sport Aviation` or `Articoli tradotti da Sport
  Aviation`.
- Whether editorial-capable WordPress users without `soci_cap` should receive
  frontend member access or remain backend-only.
- How to split `redazione` and `pubblicazione`; the SQL export does not prove a
  safe automatic mapping.
- Whether `member_topics` should be shown in the first release or only stored
  for later filtering.

## Stop conditions

Stop before schema apply when:

- permission evidence for `legacy_wordpress_credentials` cannot prove
  backend-only access;
- editorial role mapping is treated as automatic despite insufficient evidence;
- an implementation would reuse public `feeds` or public `categories`;
- `content` would be converted to Markdown or rewritten during migration;
- existing Directus artifacts would be updated or backfilled.
