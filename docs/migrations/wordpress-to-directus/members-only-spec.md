# Members-only migration specification

Status: draft operating specification

Date: 2026-06-21

## Purpose

This document defines the initial `/soci` migration scope.

The members-only area is a separate authenticated content scope. It is not an
update path for public articles that were already migrated, curated, or
modernized in Directus.

The authentication decision is recorded in
[ADR 0002](../../adr/0002-use-directus-auth-with-temporary-wordpress-password-bridge.md).

## Decisions

- The initial migration is faithful to WordPress members-only content.
- Any reorganization of members-only categories, sections, or navigation is a
  separate post-migration editorial task.
- The frontend members-only root is `/soci`.
- Members-only article routes use `/soci/<categoria>/<slug>`.
- Anonymous users requesting `/soci` routes are redirected to login and returned
  to the originally requested URL after authentication.
- Authenticated users without members access receive a simple `403` in the first
  release.
- Members-only articles already visible to members in WordPress become visible
  to members after migration verification.
- Uncertain, new, or editorially unresolved members-only content is not made
  member-visible until reviewed.
- Members-only article content is stored as sanitized HTML, not Markdown, to
  preserve the WordPress source and match the existing public article rendering
  contract.

## Target model

The members-only area uses dedicated content collections:

- `member_feeds` for members-only articles;
- `member_categories` for members-only categories;
- `member_galleries` only if private galleries are discovered during inventory.

`member_feeds.content` stores HTML. The initial migration does not convert
WordPress HTML to Markdown and does not use AI to rewrite or normalize the
content. The frontend `/soci` article renderer should sanitize and render this
HTML with the same safety posture used for public article content.

Public `feeds` and public `categories` remain separate from members-only
content. Public Directus content remains protected and target-authoritative.

Editorial status and access visibility are separate concepts. Publication state
must not be used as the access-control boundary.

## Roles

The target role model is:

- `member`: frontend access to members-only content;
- `redazione`: editorial work in the Directus backend;
- `pubblicazione`: publication/approval work in the Directus backend.

Users without clear WordPress evidence of membership or editorial role receive
no private-content access by default.

## Account migration

All WordPress users are inventoried and migrated during the initial account
bootstrap. WordPress is the account source only for that bootstrap; after import,
the new authentication system is authoritative.

Password migration preference:

1. reuse WordPress password hashes only if the chosen authentication mechanism
   can verify them safely;
2. otherwise use an approved invitation or password-reset flow;
3. never extract, store, or transmit plaintext passwords.

Authentication provider selection prioritizes:

1. WordPress password-hash compatibility;
2. implementation and operational simplicity;
3. current cost/free-tier fit;
4. clean integration with `/soci` and Directus.

Password-hash reuse is preferred but not a blocking requirement.

### Recommended auth direction

Use Directus as the final authoritative authentication system for members,
redazione, and pubblicazione users.

The repository already contains a frontend login page and a Next.js login API
route that call Directus `/auth/login`. Directus also provides password reset
endpoints and user APIs, so this direction preserves the current system shape
and avoids introducing a second long-lived auth provider.

To preserve WordPress passwords where possible, add a temporary legacy-password
bridge:

1. import all WordPress users into Directus with target roles/policies and a
   generated unusable password or reset-required state;
2. store WordPress password hashes in a migration-owned, private legacy
   credential store, not in public content collections;
3. on login, first attempt normal Directus authentication;
4. if Directus authentication fails and a legacy hash exists, verify the
   submitted password against the WordPress hash format server-side;
5. on successful legacy verification, set the user's Directus password to the
   submitted password, mark the legacy credential as consumed, and continue with
   normal Directus login/session handling;
6. after the 90-day transition window from go-live, remove or quarantine
   unconsumed legacy hashes and require password reset for remaining users.

This keeps Directus authoritative after first successful login while allowing
WordPress hash compatibility without keeping WordPress online as an auth
provider.

Current source checks:

- WordPress password verification must support modern `$wp` bcrypt hashes,
  legacy `$P$` phpass hashes, older md5 hashes, and any plugin override
  discovered in the export.
- Directus supports login, refresh, and password reset through its auth API.
- Directus API extensions can register custom endpoints or hooks if the bridge
  belongs inside Directus rather than the Next.js API layer.
- Auth.js remains a fallback if Directus cannot support the bridge cleanly; its
  Credentials provider supports custom server-side authorization logic.

The first prototype implements the legacy-password bridge in the Next.js/API
layer. This keeps iteration close to the existing login route and lets the
bridge be tested with synthetic WordPress hashes before adding Directus
extensions. Moving the bridge into Directus remains a later option if the
prototype proves the flow and centralizing auth logic becomes preferable.

The temporary legacy credential store is a dedicated Directus collection named
`legacy_wordpress_credentials`. It is migration-owned, private, and accessible
only through backend/service-role code. It must not be exposed to the frontend
or normal Directus users. It records legacy hashes, verification state, consumed
timestamp, and provenance needed to remove or quarantine unconsumed credentials
after the 90-day transition window.

## Source evidence

The WordPress membership mechanism is currently uncertain and may come from a
plugin. The migration must discover it through read-only inspection of the
WordPress export.

Current SQL-export evidence indicates that frontend member bootstrap should use
the WordPress `soci_cap` role together with the `pw_user_status=approved`
approval state. `soci_cap` alone is not sufficient because denied and pending
users also exist in the export.

MailPoet and UsersWP data appear to mirror WordPress users or newsletter/profile
state; they are supporting evidence, not the primary membership discriminator.

The export does not safely prove how to split the two editorial target profiles
(`redazione` and `pubblicazione`). Users with WordPress editorial-capable roles
must remain a manual-review bucket until a separate mapping decision is made.

The `articoli-tecnici` WordPress custom post type is a source implementation
name, not the preferred public URL label. Source routes and page metadata
support `sport-aviation` as the initial `/soci/<categoria>` slug for that
content family. The approved display label is `Sport Aviation`.

Required export evidence:

- users;
- password hashes;
- roles and capabilities;
- user metadata;
- plugin membership data;
- private posts/pages/custom post types;
- private categories/sections/taxonomies;
- relevant options;
- media references.

The expected export mechanism is phpMyAdmin. A complete SQL export is preferred.
If a complete export is not available, the export must include the WordPress
users/usermeta tables, content tables, taxonomy tables, options table, and any
plugin membership tables.

## Media retrieval

The WordPress uploads directory may be large and is not copied wholesale by
default.

The migration first derives a required-media list from members-only content.
Only referenced files are retrieved, through temporary FTP access or a targeted
archive.

FTP credentials are sensitive run inputs and must not be committed. Generated
media lists, transfer logs, and downloaded files stay outside the repository.

## Reconciliation

Members-only reconciliation is independent from public-content reconciliation.
It must not update or reinterpret public protected articles.

Rules:

- preserve source categories and sections during initial import;
- classify source content with missing media or uncertain membership evidence as
  unresolved;
- import only verified content;
- report discovered private galleries separately and model them as
  `member_galleries` if they exist.

## Stop conditions

Stop before import when:

- the WordPress export does not contain enough user, membership, or private
  content evidence;
- the membership plugin mechanism cannot be identified;
- password hash handling cannot be assessed safely;
- the legacy-password bridge cannot be implemented without exposing hashes or
  plaintext credentials;
- media references cannot be resolved into a required-media list;
- Directus permissions for members-only collections are not explicitly approved;
- Directus permissions for `legacy_wordpress_credentials` are not restricted to
  backend/service-role access;
- the auth provider decision is not approved;
- the `/soci` route access rules are not implemented and tested.

## Verification

Before production:

- inventory all WordPress users and classify target roles;
- inventory members-only content and required media;
- verify that users without membership evidence have no private-content access;
- verify anonymous `/soci` routes redirect to login with return URL;
- verify authenticated non-members receive `403`;
- verify members can read migrated content;
- verify redazione and pubblicazione workflows happen in Directus;
- verify no public protected article is changed.

## Next actions

1. Obtain the phpMyAdmin SQL export.
2. Build a read-only export inventory for users, roles, plugin membership data,
   private content, taxonomies, and media references.
3. Generate the required-media list.
4. Evaluate authentication options against WordPress password-hash compatibility
   and operational simplicity.
5. Prototype the Directus-auth legacy-password bridge in the Next.js/API layer
   against synthetic WordPress hashes.
6. Design Directus schema and permission changes for `member_feeds`,
   `member_categories`, and optional `member_galleries`.
7. Implement `/soci` routes after schema and auth decisions are approved.
