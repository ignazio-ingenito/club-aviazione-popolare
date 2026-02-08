-- Fix pages.content editor interface in Directus without breaking field metadata.
-- Safe to run multiple times.
-- Optional check first:
-- SELECT collection, field, interface, special FROM directus_fields
-- WHERE collection = 'pages' AND field = 'content';

UPDATE directus_fields
SET
  interface = 'input-rich-text-html',
  special = COALESCE(special, ARRAY[]::varchar[]),
  hidden = FALSE,
  readonly = FALSE
WHERE collection = 'pages'
  AND field = 'content';
