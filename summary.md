# Summary

Executed `prompt.md` for the CAP WordPress-to-Directus migration permission
planning slice.

## What changed

- Created `docs/migrations/wordpress-to-directus/task-b-directus-permission-implementation-plan.md`.
- Created `docs/migrations/wordpress-to-directus/directus-content-migration-permission-plan.example.json`.
- Updated `docs/migrations/wordpress-to-directus/README.md`.
- Updated `docs/migrations/wordpress-to-directus/plan.md`.

## Key decisions captured

- The read-only content migration identity remains read-only for baseline,
  fresh absence, route collision, and invariant checks.
- The create-only content migration identity remains limited to draft
  `feeds.create` for this stage.
- The planned `feeds.create` permission includes:
  - `validation.status._eq = draft`;
  - `presets.status = draft`;
  - a minimal fields allowlist matching the current executor payload:
    `status`, `slug`, `title`, `content`, `description`, `date`,
    `original_uri`, `gallery`.
- Directus policy behavior is additive, so live approval must verify that no
  other policy broadens effective access.
- Executor-side `status = draft` enforcement remains mandatory even with
  Directus validation and presets configured.

## Safety result

- Production artifact impact: none.
- No Directus role, policy, permission, user, token, schema, content, or media
  change was performed.
- No `--execute` run was performed.
- No production `POST` was performed.
- No secret value was printed.

## Checks run

- `python -m json.tool docs/migrations/wordpress-to-directus/directus-content-migration-permission-plan.example.json`
- `git status --short`
- `git diff --check`
- `git diff --cached --check`
- `cd cms/utils/wordpress && uv run python -m unittest discover -s tests -p 'test_*.py' -v`
- `cd cms/utils/wordpress && uv run python -m compileall .`

## Remaining blockers

- Future live evidence must prove the actual policy graph is not broadened by
  additional Directus policies.
- A future script/command is still needed to generate credential-free detailed
  policy graph evidence for the planned `feeds.create` permission object.
- Real roles, policies, users, tokens, and gate artifacts still require
  separate explicit approval.
