# CAP image name correction summary — 2026-06-27

Canonical spelling for repository and GHCR image names:

```text
club-aviazione-popolare-*
```

Deprecated typo spelling:

```text
club-avizione-popolare-*
```

## Applied changes

### CAP repository

Repository:

```text
ignazio-ingenito/club-aviazione-popolare
```

Updated:

```text
docs/images.md
```

Added:

```text
docs/handoffs/chatgpt_handoff_cap_image_name_correction.md
```

The existing workflow derives image names from `${{ github.repository }}`, so it already aligns with the corrected repository name.

Expected GHCR images:

```text
ghcr.io/ignazio-ingenito/club-aviazione-popolare-web
ghcr.io/ignazio-ingenito/club-aviazione-popolare-cms
```

### Homelab repository

Repository:

```text
ignazio-ingenito/homelab
```

Updated:

```text
gitops/apps/cap/web/deployment.yaml
gitops/apps/cap/cms/deployment.yaml
gitops/apps/cap/README.md
```

Added:

```text
gitops/apps/cap/IMAGE_NAME_CORRECTION.md
```

New runtime image refs:

```text
ghcr.io/ignazio-ingenito/club-aviazione-popolare-web:latest
ghcr.io/ignazio-ingenito/club-aviazione-popolare-cms:latest
```

## Not changed

No Directus content, schema, permission, token, user, media, folder, or secret was changed.

Historical handoffs may still mention the old spelling. Treat this summary and `docs/images.md` as the current decision for image naming.
