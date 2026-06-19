# Task B slice 4 — Directus read-only inventory client

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice adds a target-side Directus inventory client for anonymous/read-only
inventory attempts. It performs no writes and does not approve any production
baseline.

Implemented:

- read-only Directus client using `ReadOnlyHttpClient`;
- runtime singleton inventory for `/server/info`;
- permission, collection, field, and relation metadata inventory;
- paginated inventory for feeds, categories, files, and folders;
- explicit feed and category fields covering the protected fields consumed by
  the frontend contract in `lib/types.ts` and `lib/server.ts`;
- `meta.filter_count` and `meta.total_count` validation;
- explicit fatal target issues for `401` and `403` inaccessible endpoints;
- fail-closed HTTP, JSON, shape, identity, and pagination errors;
- deterministic target manifest conversion;
- synthetic tests for GET-only behavior, pagination, inaccessible endpoints,
  system metadata identities, fresh reads, and manifest serialization.

## Anonymous preflight

Anonymous GET probes against `https://cap-cms.skunklabs.uk` returned:

```text
server/info      200
permissions/me   403
collections      403
fields           403
relations        403
items/feeds      200
items/categories 403
files            200
folders          200
```

This is useful public-view evidence, but it is **not sufficient for an approved
baseline** because schema, relations, permissions, categories, and all relevant
feed statuses cannot be proven anonymously.

## Safety properties

- Only `ReadOnlyHttpClient` is used for network access.
- Public request paths permit `GET` and `HEAD` only.
- No Directus create, update, delete, schema, permission, role, token, or settings endpoint is called.
- The legacy mutable Directus helper is not imported.
- Inaccessible target endpoints are represented as explicit fatal issues.
- A snapshot containing inaccessible endpoints must not be treated as a complete production baseline.
- Feed and category inventory includes the user-visible/protected fields needed
  to detect content, route, cover, category, status, sort, and audit-date drift.
- Live inventories, credentials, article bodies, private metadata, and binary media are not committed.

## Files changed

```text
cms/utils/wordpress/inventory/directus.py
cms/utils/wordpress/tests/test_directus_inventory.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-directus-inventory.md
```

## Verification

Required from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall -q inventory tests
```

`uv run python -m inventory --help` remains part of the Task B exit gate after
the read-only CLI is implemented in slice 6.

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It uses only the read-only transport.
2. Could any runtime path emit `POST`, `PATCH`, `PUT`, or `DELETE`? **No.** The public transport rejects non-read methods before network use.
3. Could an anonymous partial view be mistaken for an approved baseline? **No.** Inaccessible endpoints are fatal target issues and the handoff records that anonymous access is insufficient.
4. Could protected feed/category fields be silently omitted from the baseline input? **No.** Tests lock the explicit field lists used by the frontend contract.
5. Could hidden schema, relations, categories, or permissions be silently omitted? **No.** `401` and `403` endpoint results are explicit issues.
6. Could stale cache or historical mappings influence inventory? **No.** This slice uses fresh HTTP reads and does not use `parser.yaml`.
7. Could broad permissions be changed or probed by writes? **No.** No write probes are implemented in this slice.

## Handoff

```yaml
files_inspected:
  - AGENTS.md
  - CONTEXT.md
  - docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
  - docs/handoffs/codex_handoff_cap_wordpress_migration.md
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/specification.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/runbook.md
  - docs/migrations/wordpress-to-directus/agent-loop.md
  - docs/migrations/wordpress-to-directus/discovery.md
  - cms/utils/wordpress/inventory/http.py
  - cms/utils/wordpress/inventory/models.py
  - cms/utils/wordpress/inventory/pagination.py
  - cms/utils/wordpress/inventory/wordpress.py
  - cms/utils/wordpress/tests/test_wordpress_inventory.py
files_changed:
  - cms/utils/wordpress/inventory/directus.py
  - cms/utils/wordpress/tests/test_directus_inventory.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-directus-inventory.md
findings:
  - Anonymous target access can inventory a public subset but cannot approve a full baseline.
  - The inventory client can preserve inaccessible endpoint evidence without using write probes.
  - Directus pagination must validate both `filter_count` and `total_count` for unfiltered inventory.
  - Feed and category fields must follow the protected/frontend contract rather than a minimal public listing.
verification:
  - Focused Directus unit tests passed during implementation.
  - Full required test suite must pass before commit.
production_artifact_impact: none
risks:
  - A strict read-only Directus identity is still required before baseline approval.
  - Authenticated schema may reveal additional fields or relations that require extending the field list.
open_questions:
  - Which strict read-only Directus identity will be used for approved baseline capture?
next_action: Implement Task B slice 5, repository route inventory and collision input contract.
```
