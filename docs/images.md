# Container images (GHCR)

This repo publishes two images to GitHub Container Registry:

- **Web (Next.js):** `ghcr.io/<owner>/<repo>-web`
- **CMS (Directus + optional extensions):** `ghcr.io/<owner>/<repo>-cms`

The workflow is `Build and Publish Images` in `.github/workflows/build-and-deploy.yml`.

For routing/CORS guidance, see `docs/cors.md`.

## When images are published

- Push to `main` → publishes `linux/amd64` images and updates `latest`.
- Push a tag like `v1.2.3` → publishes a `v1.2.3` tag (and also `sha-...`).
- Pull requests → builds but does **not** push.

## Tags you can use in manifests

- `latest` (only on `main`)
- `sha-<fullsha>` (always)
- `vX.Y.Z` (when you push a `vX.Y.Z` git tag)

## Permissions / secrets

No extra secrets are required to push to GHCR: the workflow uses `secrets.GITHUB_TOKEN`
and requests `packages: write`.

## Optional: notify the manifests repo

If you want this repo to notify your `../homelab` (manifests) repo after publishing images,
set these repository secrets here:

- `HOMELAB_REPO` (example: `your-org/homelab`)
- `HOMELAB_DISPATCH_TOKEN` (a PAT with permission to dispatch events to that repo)

The workflow will send a `repository_dispatch` event named `cap-images-updated` with a payload
containing the published image tags (e.g. `...:sha-<sha>` and `...:latest`).
