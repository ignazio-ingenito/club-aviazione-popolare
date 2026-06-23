# ADR 0002: Use Directus auth with a temporary WordPress password bridge

Date: 2026-06-22

## Status

Accepted

## Context

The new `/soci` area requires frontend login, members-only content access, and
password reset. WordPress users must be migrated during the initial bootstrap,
and preserving existing passwords is important when it can be done safely.

The repository already has a frontend login page and a Next.js API route that
authenticate through Directus. Introducing a second long-lived auth provider
would add operational complexity and duplicate user/session management.

WordPress password hashes may use different formats depending on WordPress
version and plugin behavior. The migration must never extract or store plaintext
passwords.

## Decision

Directus is the final authoritative authentication system for `/soci`,
`redazione`, and `pubblicazione` users.

During a 90-day transition window after go-live, the application may use a
temporary WordPress legacy-password bridge implemented first in the Next.js/API
layer.

The bridge works as follows:

- all WordPress users are imported into Directus during bootstrap;
- WordPress password hashes are stored in a private, migration-owned Directus
  collection named `legacy_wordpress_credentials`;
- only backend/service-role code may read or write that collection;
- login first attempts normal Directus authentication;
- when Directus authentication fails and an unused legacy hash exists, the
  backend verifies the submitted password against the WordPress hash;
- on successful verification, the backend updates the user's Directus password,
  marks the legacy credential as consumed, and continues with normal Directus
  login/session handling;
- after 90 days, unconsumed legacy hashes are removed or quarantined and
  remaining users must reset their password.

The first implementation lives in the Next.js/API layer because it is closest to
the existing login route and easier to prototype with synthetic hashes. Moving
the bridge into a Directus extension remains possible after the flow is proven.

## Alternatives Considered

### Directus auth with password reset only

Rejected as the default path because preserving existing WordPress passwords is
important for member adoption. It remains the fallback if safe hash verification
is too complex or risky.

### Keep WordPress as an auth provider during transition

Rejected because WordPress should only be a bootstrap source. Keeping it in the
runtime auth path would preserve legacy operational risk and complicate
decommissioning.

### External auth provider

Rejected for the initial direction because it adds another system to operate and
does not automatically solve WordPress hash compatibility. External auth remains
a fallback only if Directus cannot support the required flow safely.

### Directus extension for the first bridge implementation

Deferred. A Directus extension may be a cleaner final home for centralized auth
logic, but the first prototype should stay in the Next.js/API layer to reduce
iteration cost and avoid changing Directus runtime behavior before the hash flow
is proven.

## Consequences

Benefits:

- Directus remains the only long-lived source of user authentication;
- existing frontend login shape is preserved;
- WordPress passwords can be reused when safe;
- WordPress does not remain in the runtime auth path;
- legacy hashes have an explicit retention window.

Trade-offs:

- the Next.js API layer temporarily handles sensitive hash verification;
- `legacy_wordpress_credentials` needs strict Directus permissions and audit;
- multiple WordPress hash formats must be supported or explicitly rejected;
- users who do not log in during the transition window need password reset.

## Verification

Before production:

- test the bridge with synthetic `$wp`, `$P$`, and unsupported hash examples;
- prove `legacy_wordpress_credentials` is inaccessible to public, member,
  redazione, and pubblicazione roles;
- prove successful legacy login consumes the legacy credential and upgrades the
  Directus password;
- prove failed legacy verification does not leak whether a hash exists;
- prove users without membership evidence have no `/soci` access;
- document the 90-day cleanup/quarantine procedure.
