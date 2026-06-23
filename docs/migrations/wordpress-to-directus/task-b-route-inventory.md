# Task B slice 5 — Repository route inventory

Status: implemented and ready for review

Date: 2026-06-19

## Scope

This slice adds a filesystem-only inventory of Next.js App Router routes and a
deterministic collision input contract for migration reconciliation. It performs
no network access and does not change frontend behavior.

Implemented:

- recursive discovery of `page.ts`, `page.tsx`, `route.ts`, and `route.tsx`
  under `app/`;
- public page routes and API routes recorded separately;
- static and dynamic route normalization;
- `app/public` asset exclusion;
- dynamic segment extraction;
- concrete glob-style collision patterns for dynamic route positions;
- migration collision scopes for global feed slug routes, numeric news IDs,
  dynamic public routes, reserved static public routes, and API routes;
- deterministic target manifest conversion;
- synthetic tests for route discovery, ordering, collision scopes, manifest
  serialization, and missing app directory failure.

## Safety properties

- No WordPress or Directus endpoint is called.
- No frontend files are changed.
- No production data, inventory output, credential, or binary media is committed.
- Route inventory is derived from repository files only.
- The collision contract explicitly treats `/news/[id]`,
  `/feed/[category]/[slug]`, `/efficiency-race`, and `/trofei/[slug]` as global
  feed slug collision inputs.
- Dynamic route collision patterns include all-dynamic wildcard forms such as
  `/feed/*/*` for concrete candidate matching.

## Files changed

```text
cms/utils/wordpress/inventory/routes.py
cms/utils/wordpress/tests/test_route_inventory.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-route-inventory.md
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

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It only reads repository paths.
2. Could any runtime path emit `POST`, `PATCH`, `PUT`, or `DELETE`? **No.** There is no network client in this slice.
3. Could frontend behavior change? **No.** No files under `app/`, `components/`, or `lib/` are modified.
4. Could route collisions be scoped only by category? **No.** Global feed-slug routes are explicitly marked.
5. Could public assets become route records? **No.** `app/public` is excluded.
6. Could generated inventories enter Git? **No.** This slice adds code and synthetic tests only.

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
  - app/
  - lib/server.ts
  - cms/utils/wordpress/inventory/models.py
files_changed:
  - cms/utils/wordpress/inventory/routes.py
  - cms/utils/wordpress/tests/test_route_inventory.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-route-inventory.md
findings:
  - Feed lookup is globally slug-based in `/news/[id]` and `/feed/[category]/[slug]`.
  - Static public routes are reserved collision inputs for future article slugs.
  - API routes should be recorded for completeness but excluded from public slug collision decisions.
verification:
  - Focused route unit tests passed during implementation.
  - Full required test suite must pass before commit.
production_artifact_impact: none
risks:
  - Future route groups or parallel routes may require extending normalization rules.
  - Collision policy remains conservative; reconciliation must still combine this with current target slugs.
open_questions:
  - None introduced by this slice.
next_action: Implement Task B slice 6, read-only CLI integration and atomic manifest writer.
```
