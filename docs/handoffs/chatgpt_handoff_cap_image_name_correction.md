# Handoff — CAP image name correction

## Decision

Use the corrected spelling everywhere for repository/image references:

```text
club-aviazione-popolare-*
```

The old spelling `club-avizione-popolare-*` is deprecated and should not be used for new manifests, docs, or image tags.

## GitHub / image build implication

The CAP repository is `ignazio-ingenito/club-aviazione-popolare`.

The existing GitHub Actions workflow derives image names from `${{ github.repository }}`, so it naturally publishes:

```text
ghcr.io/ignazio-ingenito/club-aviazione-popolare-web
ghcr.io/ignazio-ingenito/club-aviazione-popolare-cms
```

No workflow change is required for the corrected image spelling.

## Homelab changes already applied

Repository: `ignazio-ingenito/homelab`
Branch: `main`

Updated CAP deployments:

```text
gitops/apps/cap/web/deployment.yaml
gitops/apps/cap/cms/deployment.yaml
```

New image references:

```text
ghcr.io/ignazio-ingenito/club-aviazione-popolare-web:latest
ghcr.io/ignazio-ingenito/club-aviazione-popolare-cms:latest
```

Commits:

```text
664b1109690cf32f7bad962cdf21cb52fe67b51a  fix(cap): use corrected CAP image name for web
7fb2fdd6bff774cc281a6676a5e5961560d5576a  fix(cap): preserve web security context key
c62143c1773090b1700c8e30bf2a861427340063  fix(cap): use corrected CAP image name for cms
```

Note: the first web manifest commit briefly introduced a typo in `allowPrivilegeEscalation`; it was immediately corrected in the second commit before this handoff.

## Not done

- No Directus content, schema, media, permission, user, token, or secret mutation.
- No CAP source code change.
- No production UI verification performed from ChatGPT because deploy state/image availability still depends on a successful GHCR build and ArgoCD reconciliation.

## Next concrete action

Run or trigger the CAP image publishing workflow for the corrected repository/image names, then verify that Homelab/ArgoCD pulls:

```text
ghcr.io/ignazio-ingenito/club-aviazione-popolare-web:latest
ghcr.io/ignazio-ingenito/club-aviazione-popolare-cms:latest
```

After ArgoCD reconciles, verify:

```text
https://cap.skunklabs.uk
https://cap-cms.skunklabs.uk
```

and the seven migrated gallery routes once their feed visibility is confirmed.
