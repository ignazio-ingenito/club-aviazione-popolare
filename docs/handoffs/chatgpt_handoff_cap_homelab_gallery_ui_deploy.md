# Handoff ChatGPT — CAP gallery UI/deploy after media migration

## Repo and state

- Source repo: `/home/iingenito/projects/personal/club-avizione-popolare`
- Branch: `develop`
- Latest pushed commit: `afd8904 feat(wordpress): complete gallery media migration`
- Production frontend: `https://cap.skunklabs.uk`
- Production Directus: `https://cap-cms.skunklabs.uk`
- GitOps/deploy repo: `/home/iingenito/projects/personal/homelab`
- Homelab path from CAP docs: `gitops/apps/cap/`

Current CAP checkout still has unrelated local changes that must not be swept
into this deploy work:

```text
 M .gitignore
?? docs/handoffs/codex_handoff_cap_wrodpress_migration_permission_management.md
```

## What is already done

Directus content migration for public galleries is complete.

Created Directus artifacts:

```text
gallery_count: 7
uploaded_file_count: 291
created_folder_count: 6
reused_empty_migration_folder_count: 1
```

The 7 gallery draft feeds already existed before media upload. The frontend
gallery fallback resolves a Directus folder by exact feed slug, then reads files
in that folder.

Files were uploaded with zero-padded filename prefixes to preserve source order
under the current frontend sorting by `title, filename_download`.

## Evidence artifacts

Run artifacts live outside Git:

```text
/home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-token-recovery-20260627T075447Z
/home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-upload-20260627T075707Z
/home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-upload-schema-token-20260627T075818Z
/home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-post-upload-schema-verify-20260627T080043Z
/home/iingenito/cap-migration-runs/20260622T110402Z/gallery-media-public-read-verify-20260627T080104Z
```

Important verification results:

```text
gallery-media-upload-schema-token-20260627T075818Z:
  status: completed
  post_endpoints: /folders, /files
  forbidden_methods_sent: none

gallery-media-post-upload-schema-verify-20260627T080043Z:
  status: approved
  verified_galleries: 7
  verified_files: 291
  live_methods_used: GET, HEAD

gallery-media-public-read-verify-20260627T080104Z:
  status: approved
  credential_used: anonymous
  live_methods_used: GET
```

Artifact hashes recorded in:

```text
docs/migrations/wordpress-to-directus/plan.md
docs/handoffs/codex_handoff_cap_wordpress_migration.md
```

## Important caveat

The final media upload used:

```text
secrets/migration/directus-schema-token.20260622.sops.yaml
```

Reason: the dedicated gallery-media token validated for reads but received
`HTTP 403` on `POST /files`. Upload still used only `GET` and `POST`; no
`PATCH`, `PUT`, `DELETE`, feed update, folder/file update, schema change,
frontend change, or homelab change was performed during media upload.

Do not perform further Directus mutations as part of this handoff.

## Goal for ChatGPT

Publish/deploy the current CAP frontend state and verify the migrated galleries
through the UI.

This is a deploy/UI verification task, not a content migration task.

## Scope

Allowed:

- inspect CAP repo and homelab repo;
- inspect GitHub Actions/build status for `afd8904`;
- determine whether production deploys from `main`, `develop`, `latest`, or a
  pinned image tag;
- update homelab GitOps manifests under `gitops/apps/cap/` if needed;
- commit/push homelab deployment changes if they are the established deploy
  path;
- run read-only production checks against frontend and Directus;
- create a concise deploy/verification handoff.

Forbidden:

- any Directus content, media, folder, file, schema, role, policy, permission,
  user, token, or SOPS-secret mutation;
- deleting or rewriting migration-created folders/files;
- changing CAP migration code outside a small UI/rendering fix;
- changing unrelated homelab apps;
- broad cluster changes;
- destructive kubectl operations;
- publishing drafts/editorial status changes unless explicitly approved.

## Read first

In CAP repo:

```text
CONTEXT.md
docs/handoffs/codex_handoff_cap_wordpress_migration.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/specification.md
components/gallery.tsx
lib/server.ts
.github/workflows/build-and-deploy.yml
docs/images.md
```

In homelab repo:

```text
gitops/apps/cap/
```

## Gallery slugs to verify

```text
foto_recenti
foto-raduno-2001
foto-raduno-2002
foto-fly-in-vichy-2007
49-raduno-cap-ozzano-emilia-10-11-12-settembre-2021
52-raduno-cap-lilh-6-7-8-9-2024
53-raduno-cap-reggio-emilia-5-6-7-9-2025
```

Expected Directus file counts:

```text
foto_recenti: 17
foto-raduno-2001: 10
foto-raduno-2002: 10
foto-fly-in-vichy-2007: 8
49-raduno-cap-ozzano-emilia-10-11-12-settembre-2021: 53
52-raduno-cap-lilh-6-7-8-9-2024: 148
53-raduno-cap-reggio-emilia-5-6-7-9-2025: 45
```

## Suggested execution

1. In CAP repo, confirm:

```bash
git rev-parse HEAD
git status --short
git log -1 --oneline
```

Expected commit:

```text
afd8904 feat(wordpress): complete gallery media migration
```

2. Inspect the image workflow:

```bash
sed -n '1,140p' .github/workflows/build-and-deploy.yml
sed -n '1,80p' docs/images.md
```

Pay attention to whether images are built from `main` only. If yes, determine
whether the deploy task needs a merge/promotion from `develop` to `main`, a
manual workflow run, or a homelab manifest update to an already built image.

3. In homelab repo, inspect current CAP manifests:

```bash
cd /home/iingenito/projects/personal/homelab
git status --short --branch
find gitops/apps/cap -maxdepth 3 -type f | sort
rg -n "club-avizione|club-aviazione|cap|image|sha-|latest|DIRECTUS" gitops/apps/cap
```

4. Apply only the minimum deployment change required by the repo’s existing
GitOps pattern.

5. Verify production UI after deploy:

```text
https://cap.skunklabs.uk
```

Use browser/HTTP checks to confirm gallery pages load and images render. If
draft feeds are not visible publicly, stop and report that publication/editorial
status is the blocker; do not publish drafts without explicit approval.

## Stop conditions

Stop and report if:

- deploy requires publishing draft feeds;
- homelab manifests are not clearly for CAP;
- the required image for `afd8904` does not exist and promotion path is unclear;
- a step would require Directus writes;
- a step would require deleting/replacing existing uploaded media;
- any cluster action is destructive or affects non-CAP apps.

## Handoff output required

Return:

- files inspected;
- files changed;
- exact commit/image deployed or reason deploy did not proceed;
- production UI URLs checked;
- gallery count/file-count evidence;
- whether draft visibility blocks public verification;
- residual risks;
- next concrete action.
