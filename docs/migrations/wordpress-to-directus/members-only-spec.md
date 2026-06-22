# Members-only migration specification

Status: draft operating specification

Date: 2026-06-21

## Purpose

This document defines the initial `/soci` migration scope.

The members-only area is a separate authenticated content scope. It is not an
update path for public articles that were already migrated, curated, or
modernized in Directus.

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

## Target model

The members-only area uses dedicated content collections:

- `member_feeds` for members-only articles;
- `member_categories` for members-only categories;
- `member_galleries` only if private galleries are discovered during inventory.

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

## Source evidence

The WordPress membership mechanism is currently uncertain and may come from a
plugin. The migration must discover it through read-only inspection of the
WordPress export.

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
- media references cannot be resolved into a required-media list;
- Directus permissions for members-only collections are not explicitly approved;
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
5. Design Directus schema and permission changes for `member_feeds`,
   `member_categories`, and optional `member_galleries`.
6. Implement `/soci` routes after schema and auth decisions are approved.
