# Task B slice 9.2 - Create-only Directus client

Status: implemented and ready for review

Date: 2026-06-20

## Scope

This slice adds a separate create-only Directus client for future approved
migration writes. It is distinct from the legacy mutable helper and rejects
non-create methods before transport use.

Implemented:

- `DirectusCreateOnlyClient` with `GET`, `HEAD`, and `POST` only;
- explicit rejection of `PATCH`, `PUT`, and `DELETE`;
- endpoint allowlist for item collections, files, and folders;
- bearer-token header support for authorized create-only requests;
- create wrappers for items, folders, and file uploads;
- synthetic tests for method rejection, endpoint rejection, create success, and
  empty-token validation.

## Safety properties

- The legacy mutable Directus helper remains untouched.
- No production endpoint is called by this slice.
- Mutating methods are rejected before any network request is emitted.
- Unapproved POST destinations fail closed.
- The client is suitable only for future reviewed write work.

## Files changed

```text
cms/utils/wordpress/directus_create_only.py
cms/utils/wordpress/tests/test_directus_create_only.py
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-create-only-directus-client.md
```

## Verification

Required from `cms/utils/wordpress`:

```bash
uv run python -m unittest discover -s tests -p 'test_directus_create_only.py' -v
uv run python -m unittest discover -s tests -p 'test_*.py' -v
```

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It adds a new client and tests only.
2. Could any runtime path emit `PATCH`, `PUT`, or `DELETE` through the new client? **No.** They are rejected before transport use.
3. Could a create request hit an unapproved endpoint? **No.** POST destinations are allowlisted.
4. Could the legacy mutable helper be silently changed? **No.** It is left untouched.
5. Could this approve a production write? **No.** It only prepares the create-only transport for later reviewed use.

## Handoff

```yaml
files_inspected:
  - cms/utils/wordpress/directus.py
  - cms/utils/wordpress/inventory/http.py
  - cms/utils/wordpress/tests/test_directus_inventory.py
  - cms/utils/wordpress/tests/test_inventory_cli.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/specification.md
files_changed:
  - cms/utils/wordpress/directus_create_only.py
  - cms/utils/wordpress/tests/test_directus_create_only.py
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-create-only-directus-client.md
findings:
  - A separate create-only client keeps the mutable legacy helper isolated.
  - POST destination allowlisting is needed even when the method set is already restricted.
  - The create-only client can support future migration writes without enabling update or delete behavior.
verification:
  - Focused directus create-only tests passed.
  - Full wordpress package test suite passed.
production_artifact_impact: none
risks:
  - The client is not yet wired into a production writer.
  - Endpoint allowlists must be kept in sync with future approved write flows.
open_questions:
  - Which future writer should adopt `DirectusCreateOnlyClient` first?
next_action: Wire the create-only client into the future approved writer path instead of the legacy mutable helper.
```
