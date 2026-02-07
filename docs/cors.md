# Routing & CORS (Next.js + Directus)

Goal: avoid CORS issues by keeping the browser talking only to **one origin** (your Next.js site), and letting Next.js call Directus **server-to-server**.

## Recommended pattern: Next.js as a BFF (no CORS)

- Browser → `https://cap.skunklabs.uk` (Next.js)
- Next.js (server) → `http://<directus-service>:8055` (Directus internal URL)

In this repo, server-to-server calls use:
- `DIRECTUS_INTERNAL_URL` (preferred) or `DIRECTUS_URL` (fallback)

Public URLs rendered into HTML (e.g. image `src`) use:
- `DIRECTUS_PUBLIC_URL` (preferred) or `DIRECTUS_URL` (fallback)

Why this avoids CORS:
- CORS is a **browser** restriction. Server-side requests from Next.js to Directus are not subject to browser CORS.

## Local development against a remote Directus

If you run Next.js locally but want to use your remote Directus:

- Set `DIRECTUS_INTERNAL_URL=https://cap-admin.skunklabs.uk` (API + admin host).
- Set `DIRECTUS_PUBLIC_URL=https://cap-cms.skunklabs.uk` (public assets host).
- Ensure `next.config.mjs` allows those hostnames for images (`images.remotePatterns`).

## Assets (images/files)

You have two good options:

1) **Direct link to Directus assets** (simpler)
   - Render image URLs using `DIRECTUS_PUBLIC_URL` (e.g. `https://cms.example.com/assets/<id>`).
   - Ensure Next Image allows that host (updated in `next.config.mjs` for `cap-cms.skunklabs.uk` / `cap-admin.skunklabs.uk`).

2) **Proxy assets through Next.js** (best if you need auth-protected files)
   - Use `/api/files/[id]` which fetches from `DIRECTUS_INTERNAL_URL`.
   - Browser stays on the Next.js origin, so there’s no CORS.

## When you *do* need CORS in Directus

You only need Directus CORS if the browser will call Directus **directly**, e.g.:
- your frontend does `fetch('https://cms.example.com/items/...')` from the browser

In that case configure Directus to allow your frontend origin, e.g.:
- `CORS_ENABLED=true`
- `CORS_ORIGIN=https://cap.skunklabs.uk`

(Exact env var names depend on your Directus version/config; keep them in your manifests repo or runtime secrets.)

## Common gotchas

- **Mixed internal/public URLs**: use an internal service URL for server calls, and a public hostname for image URLs.
- **Cookies across subdomains**: cookies set by Next.js (like `access_token`) are for the Next.js domain by default; they won’t automatically be sent to `cms.*`. Prefer proxying auth-sensitive calls through Next.js.
