# Task B slice 2 — WordPress read-only inventory client

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice adds a fresh-by-default, read-only client for the public WordPress REST API. It inventories content types, categories, published posts, and media metadata using the immutable contracts introduced by Task B slice 1.

No live source inventory is committed by this slice. Runtime manifests remain controlled artifacts outside Git.

## Implemented

- shared HTTP transport restricted to `GET` and `HEAD`;
- relative-endpoint validation and parent-path rejection;
- same-origin redirect enforcement;
- TLS verification enabled by default;
- sanitized HTTP and invalid-JSON errors that exclude response bodies;
- WordPress `/types` discovery;
- complete paginated category, post, and media retrieval;
- validation of `X-WP-Total` and `X-WP-TotalPages` on every page;
- stable ordering by WordPress numeric ID where supported;
- published-post scope as the default, while retaining all category IDs;
- featured-media metadata without downloading binary files;
- extraction of inline image and link references without modifying HTML;
- explicit warnings for empty post slug/title;
- explicit errors for malformed records, categories/tags, links, and media URLs;
- manifest metadata recording API totals, normalized counts, issues, page counts, and the fresh/no-cache policy.

## Fail-closed behavior

The inventory stops rather than accepting incomplete evidence when:

- a non-read HTTP method is requested;
- an endpoint is absolute, traverses to a parent path, or redirects to another origin;
- an HTTP request fails;
- JSON is invalid;
- a paginated endpoint does not return an array;
- WordPress pagination headers are absent, invalid, negative, or inconsistent;
- a page is missing or contains an unexpected item count.

Malformed individual records are omitted from normalized records and emitted as structured source issues. They are never silently treated as missing-content candidates.

## Files changed

```text
cms/utils/wordpress/inventory/__init__.py
cms/utils/wordpress/inventory/transport.py
cms/utils/wordpress/inventory/wordpress.py
cms/utils/wordpress/inventory/wordpress_records.py
cms/utils/wordpress/tests/test_readonly_transport.py
cms/utils/wordpress/tests/test_wordpress_inventory.py
cms/utils/wordpress/tests/test_wordpress_inventory_errors.py
cms/utils/wordpress/tests/test_wordpress_media_inventory.py
cms/utils/wordpress/tests/wordpress_fixtures.py
docs/migrations/wordpress-to-directus/task-b-wordpress-client.md
```

The migration README and canonical plan are updated in the same PR.

No dependency or lockfile change is required; `httpx` and Beautiful Soup were already declared by the existing utility.

## Verification

Targeted synthetic verification:

```bash
python -m unittest discover -s tests -p 'test_*wordpress*py' -v
python -m unittest tests.test_readonly_transport -v
python -m compileall -q inventory tests
```

Equivalent isolated execution covered 18 new tests and passed compilation.

Covered behavior:

- forbidden methods rejected before transport invocation;
- absolute/traversing endpoints rejected;
- cross-origin redirects rejected;
- HTTP and JSON failures sanitized;
- complete two-page post retrieval;
- GET-only request observation;
- fresh repeated retrieval without implicit cache;
- empty collection handling;
- malformed pagination and records;
- explicit warning/error issue generation;
- types response validation;
- media metadata normalization without binary download;
- invalid media source URL reporting;
- page-size validation.

## Production artifact impact

`none`

This slice does not:

- call Directus;
- modify WordPress;
- download or upload media binaries;
- read `parser.yaml`;
- invoke legacy importer paths;
- write a manifest to the repository;
- alter schema, permissions, articles, files, folders, relations, deployment manifests, or database state.

## Reviewer checklist

1. Can any client path emit `POST`, `PATCH`, `PUT`, or `DELETE`? **No; the transport rejects it before network I/O.**
2. Can a redirect escape the configured WordPress origin? **No; final origin is checked.**
3. Can stale joblib data affect results? **No cache is used.**
4. Can missing or changing pagination totals be accepted? **No; the pagination contracts fail closed.**
5. Can malformed source content disappear silently? **No; record-level problems become structured issues.**
6. Is article HTML rewritten? **No; it is retained and inspected read-only for references.**
7. Are media binaries downloaded? **No; only REST metadata is inventoried.**
8. Are production content or credentials committed? **No.**

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/migrations/wordpress-to-directus/discovery.md
  - docs/migrations/wordpress-to-directus/specification.md
  - docs/migrations/wordpress-to-directus/task-b-inventory-contracts.md
  - cms/utils/wordpress/inventory/*
  - cms/utils/wordpress/wordpress.py
files_changed:
  - cms/utils/wordpress/inventory/__init__.py
  - cms/utils/wordpress/inventory/transport.py
  - cms/utils/wordpress/inventory/wordpress.py
  - cms/utils/wordpress/inventory/wordpress_records.py
  - cms/utils/wordpress/tests/test_readonly_transport.py
  - cms/utils/wordpress/tests/test_wordpress_inventory.py
  - cms/utils/wordpress/tests/test_wordpress_inventory_errors.py
  - cms/utils/wordpress/tests/test_wordpress_media_inventory.py
  - cms/utils/wordpress/tests/wordpress_fixtures.py
  - docs/migrations/wordpress-to-directus/task-b-wordpress-client.md
findings:
  - A first-page GET plus validated response headers is sufficient to drive complete WordPress pagination.
  - Record-level normalization errors can be represented without accepting an incomplete inventory as successful.
  - Featured media and inline references can be inventoried without binary downloads or source HTML mutation.
verification:
  - 18 targeted synthetic tests passed.
  - Python compilation passed.
production_artifact_impact: none
risks:
  - The client has not yet been used to create an approved live source inventory.
  - Gallery custom-post-type discovery and HTML fallback are intentionally deferred to slice 3.
  - A changing source with stable totals can still require later identity-level reconciliation checks.
open_questions:
  - Gallery REST exposure remains to be discovered in slice 3.
next_action: Implement Task B slice 3 for gallery REST discovery and ordered public-HTML fallback using only synthetic fixtures.
```
