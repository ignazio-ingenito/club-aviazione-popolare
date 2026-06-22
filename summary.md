# Summary

Executed `prompt.md` for the next non-destructive Directus permission evidence
slice.

## What changed

- Created `docs/migrations/wordpress-to-directus/task-c-directus-policy-graph-evidence-plan.md`.
- Created `docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json`.
- Updated `docs/migrations/wordpress-to-directus/README.md`.
- Updated `docs/migrations/wordpress-to-directus/plan.md`.

## Key decisions captured

- Future policy evidence must inspect the complete additive Directus policy
  graph for `directus-createonly-content-migration`.
- A static JSON example is documentation only and cannot satisfy a live
  production gate.
- The future collector must have a credential-free `render-example` mode and a
  separately approved `collect-live` mode.
- `collect-live` must be GET-only for policy graph evidence and must not perform
  production `POST`, `PATCH`, `PUT`, or `DELETE`.
- If Directus does not expose the full policy graph to the create-only identity,
  evidence must combine a redacted operator export with a create-only probe
  artifact that refers to the same redacted subject fingerprint.
- Executor-side `status = draft` enforcement remains mandatory.

## Safety result

- Production artifact impact: none.
- No Directus role, policy, permission, user, token, schema, content, or media
  change was performed.
- No production `POST` was performed.
- No migration `--execute` run was performed.
- No secret value was printed or committed.

## Checks run

- `python -m json.tool docs/migrations/wordpress-to-directus/directus-policy-graph-evidence.example.json`
- `git diff --check`
- `git diff --cached --check`
- Staged-diff secret pattern scan for the known leaked token value, bearer
  tokens, authorization headers, and long JSON token-like values.

## Remaining blockers

- Live policy graph evidence still requires explicit operator approval before
  any `collect-live` run.
- Real roles, policies, users, tokens, and permission changes remain separate
  approval-gated production actions.
- A future implementation task is needed if we want an executable
  `directus_policy_graph_evidence.py` collector instead of the current
  documentation-only plan.
