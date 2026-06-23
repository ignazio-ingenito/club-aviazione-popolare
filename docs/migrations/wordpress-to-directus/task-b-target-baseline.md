# Task B slice 9.1 - Authenticated target baseline review

Status: reviewed, pending explicit human approval

Date: 2026-06-20

## Scope

This review consumes the authenticated Directus baseline inventory and the
duplicate-file evidence already captured outside Git. It does not mutate the
target or approve any write action.

Reviewed:

- authenticated Directus core inventory captured from the live target;
- directus version `11.13.2`;
- `feeds`, `categories`, `files`, and `folders` counts from the authenticated
  read-only run;
- duplicate file groups in the target inventory;
- WordPress source and WXR media corroboration for duplicate file usage;
- the 2020 webinar pair where the same binary was uploaded twice under two
  different Directus folder paths.

## Findings

- The authenticated Directus inventory is materially richer than the anonymous
  public-view snapshot and is the right candidate for baseline review.
- The directus version observed in the live read-only run is `11.13.2`.
- The authenticated inventory captured `1327` records and `0` issues.
- The target read-only reconciliation against WordPress still yields
  `483 already_imported`, `1267 create_candidate`, `28 manual_review`,
  `12 conflict`, and `836 target_only_count`.
- The duplicate file review found `40` duplicate filename groups in the target.
- `37` of those groups have WordPress evidence, `11` also have a WordPress
  media record, and `3` are orphans in the accessible evidence set.
- `WebinarWEBcap.jpg` is duplicated in Directus, but both records map to the
  same WordPress featured media for `webinar-motori` and
  `webinar-ripresa-volo`.
- The three orphan groups currently visible are:
  - `locandina ER 2018.jpg`
  - `Locandina T 2019 finale.jpg`
  - `Volantino 2019 CAP Piemonte.jpg`

## Safety properties

- No target baseline object was mutated, replaced, renamed, or deleted.
- No production write endpoint was called.
- Duplicate analysis is evidentiary only; it does not authorize cleanup.
- The orphan conclusion is limited to the current accessible inventories and
  should not be treated as an instruction to delete protected target artifacts.

## Files changed

```text
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/task-b-target-baseline.md
```

## Verification

Required from the documentation review path:

```bash
sed -n '1,220p' docs/migrations/wordpress-to-directus/README.md
sed -n '1,220p' docs/migrations/wordpress-to-directus/plan.md
sed -n '1,220p' docs/migrations/wordpress-to-directus/task-b-target-baseline.md
```

## Reviewer checklist

1. Could this change update or delete a protected feed, file, folder, or relation? **No.** It only updates documentation.
2. Could any runtime path emit `POST`, `PATCH`, `PUT`, or `DELETE`? **No.** No code path changed.
3. Could duplicate-file evidence be mistaken for a deletion instruction? **No.** The handoff says it is evidentiary only.
4. Could the baseline be treated as approved without explicit human signoff? **No.** The status remains pending approval.
5. Could the orphan conclusion be overgeneralized beyond the accessible evidence set? **No.** The scope is explicitly limited.

## Handoff

```yaml
files_inspected:
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-target-baseline.md
  - /tmp/cap-migration-runs/20260619T203243Z-resume/directus-authenticated.jsonl
  - /tmp/cap-migration-runs/20260619T203243Z-resume/wordpress-source.jsonl
  - /tmp/cap-migration-runs/20260619T203243Z-resume/wordpress-wxr-media.jsonl
files_changed:
  - docs/migrations/wordpress-to-directus/README.md
  - docs/migrations/wordpress-to-directus/plan.md
  - docs/migrations/wordpress-to-directus/task-b-target-baseline.md
findings:
  - The authenticated Directus baseline is the correct read-only snapshot to review next.
  - Duplicate webinar media are exact binary duplicates and are not deletion candidates.
  - Three duplicate filename groups remain orphans in the accessible evidence set.
verification:
  - Documentation-only review of the new baseline handoff and supporting inventories.
production_artifact_impact: none
risks:
  - The baseline is still not explicitly approved by the human reviewer.
  - The orphan conclusion depends on the current accessible inventory set.
open_questions:
  - Does the operator want the authenticated baseline frozen as the approved reuse hash?
  - Should the three orphan filename groups be quarantined conceptually rather than deleted?
next_action: Obtain explicit human approval for the authenticated baseline before any write-manifest work.
```
