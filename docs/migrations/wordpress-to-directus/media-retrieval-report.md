# WordPress media retrieval report

Status: read-only planning report

Date: 2026-06-22

## Purpose

This report summarizes the media scale discovered from the WordPress database
export and defines a retrieval strategy for the next migration activities.

It is intentionally aggregate-only. It does not contain WordPress file lists,
private content, credentials, user data, or binary media.

## Source evidence

- Encrypted source export:
  `secrets/migration/wordpress-db.20260622.sql.sops.yaml`
- Plaintext working copy during analysis:
  `/tmp/cap-migration-runs/20260622-members-only-source/wordpress-db.sql`
- Historical importer evidence:
  `cms/utils/wordpress/parser.yaml`

`parser.yaml` is historical corroboration only. It can indicate what the legacy
script probably imported, but it cannot prove current Directus state and must
not authorize writes or deletions.

## Aggregate findings

### WordPress media scale

| Scope | Count |
| --- | ---: |
| WordPress attachment posts | 1,444 |
| Distinct `_wp_attached_file` original paths | 1,444 |
| Generated derivative file references in attachment metadata | 6,191 |
| Estimated physical files if copying originals plus derivatives | 7,600+ |

The migration should not copy WordPress thumbnails and generated derivatives by
default. Directus should receive source originals and generate its own image
variants.

### Attachment MIME distribution

| MIME/type group | Count |
| --- | ---: |
| PDF | 685 |
| JPG/JPEG | 683 |
| DOCX | 65 |
| ODT | 52 |
| PNG | 12 |
| GIF | 4 |
| DOC | 3 |
| BMP | 3 |
| XLSX | 3 |
| TIFF | 2 |
| ODS | 1 |
| MP4 | 1 |

### Attachment parent distribution

| Parent content type | Attachment count |
| --- | ---: |
| `articoli-tecnici` | 432 |
| no current parent or missing parent | 412 |
| `dt_gallery` | 289 |
| `post` | 221 |
| `page` | 82 |
| `dt_slideshow` | 8 |

### Legacy importer coverage signal

| WordPress content type | Published count | Historical `parser.yaml` mappings |
| --- | ---: | ---: |
| `post` | 323 | 313 |
| `articoli-tecnici` | 415 | 0 |
| `page` | 108 | 0 |
| `dt_gallery` | 7 | 0 |

This supports the operating assumption that most standard public article media
were already handled by the legacy import, while galleries, technical/member
content, pages, and a small number of unmapped posts still require review.

## Candidate retrieval scopes

### Scope A: `articoli-tecnici`

Likely first members-only or technical-document scope.

| Metric | Count |
| --- | ---: |
| Published records | 415 |
| Child attachment original paths | 432 |
| Inline upload references | 0 |
| Required original paths | 432 |

File-type distribution:

| Type | Count |
| --- | ---: |
| PDF | 380 |
| DOCX | 49 |
| XLSX | 3 |

This is the recommended first media retrieval batch.

### Scope B: `dt_gallery`

Public gallery scope not covered by the legacy article importer.

| Metric | Count |
| --- | ---: |
| Published records | 7 |
| Child attachment original paths | 289 |
| Required original paths | 289 |

All discovered gallery attachments are JPEG images.

### Scope C: unmapped public posts

The database contains 323 published standard `post` records. The historical
mapping contains 313 mapped standard posts, leaving about 10 published posts
that need reconciliation.

These should be reviewed separately before retrieving media, because some may
already exist in Directus through manual edits or a later migration run.

### Scope D: pages

The database contains 108 published WordPress pages and 455 normalized media
references when child attachments and inline references are combined.

Pages are not currently the primary members-only migration scope. Treat them as
a later content-model decision unless a specific `/soci` page dependency is
identified.

## Recommended strategy

Use targeted media retrieval, not a full `wp-content/uploads` copy, for the
migration path.

1. Generate a required-media manifest outside Git for one approved scope at a
   time.
2. Start with `articoli-tecnici`.
3. Compare the required WordPress filenames and, where possible, checksums
   against a fresh read-only Directus file inventory.
4. Classify each required media item as:
   - already present with strong evidence;
   - candidate filename match requiring review;
   - missing and eligible for retrieval;
   - unresolved because source or target evidence is incomplete.
5. Retrieve only missing or unresolved source originals into a run directory
   outside Git.
6. Compute local SHA-256 and size for every downloaded file.
7. Use those files as inputs to the later additive-only Directus import.

Do not use filename equality alone to mutate, reuse, move, or delete Directus
files. Existing Directus files remain protected production artifacts.

## Transfer tooling

`rclone` is available locally and is the preferred retrieval tool if FTP/SFTP
access is provided.

Recommended shape:

```bash
rclone copy wordpress-ftp:wp-content/uploads \
  /tmp/cap-migration-runs/<run-id>/media/uploads \
  --files-from /tmp/cap-migration-runs/<run-id>/required-media-articoli-tecnici.txt \
  --progress \
  --transfers 4 \
  --checkers 8 \
  --retries 3 \
  --low-level-retries 10
```

Operational notes:

- Store rclone remotes, FTP credentials, transfer logs, file manifests, and
  downloaded media outside the repository.
- Prefer SFTP if the provider supports it; use FTP only when SFTP is not
  available.
- Keep transfer concurrency moderate to avoid provider throttling.
- Run a verification pass after copy with size/checksum evidence where the
  remote supports it.

## Full-copy alternative

A full copy of `wp-content/uploads` may still be useful as a preservation or
forensic backup, but it is not the recommended import input.

Full copy trade-offs:

- Pros: captures orphans and unexpected plugin files.
- Cons: copies thousands of generated derivatives, increases storage/noise, and
  does not answer which files are actually needed for Directus migration.

If a full copy is required, keep it as a separate archival operation with its
own run directory and do not feed it directly into the Directus importer.

## Required next activities

1. Build a SQL-export media manifest command that emits required-media lists
   outside Git.
2. Generate the `articoli-tecnici` required-media list.
3. Capture a fresh read-only Directus file inventory.
4. Reconcile `articoli-tecnici` media against Directus files.
5. Retrieve only missing `articoli-tecnici` originals with `rclone`.
6. Repeat the same flow for `dt_gallery`.
7. Separately reconcile the about 10 unmapped standard posts before deciding
   whether any of their media need retrieval.

## Stop conditions

Stop before retrieval or import when:

- the source manifest cannot resolve required media paths deterministically;
- Directus inventory is unavailable or incomplete;
- a file appears to match only by ambiguous filename;
- the transfer would require committing plaintext media lists, credentials, or
  downloaded files;
- an import path would update, move, rename, replace, or delete an existing
  Directus artifact;
- a gallery import cannot preserve source image order.

## Current recommendation

Proceed with `articoli-tecnici` first. It is small enough for targeted
retrieval, likely outside the legacy import coverage, and directly relevant to
the members-only migration.

Then process `dt_gallery` as a separate batch because gallery ordering and
rendering have different target-model requirements.
