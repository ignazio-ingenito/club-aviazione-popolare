# WordPress -> Directus utility

This tool imports WordPress posts into Directus.

## Commands

From `cms/utils/wordpress`:

```bash
uv run main.py import <wordpress_category_id> <directus_category_slug>
```

Example:

```bash
uv run main.py import 5 corsi
```

## Directus target

By default the tool calls local Directus (`http://localhost:8055`).
If your backend moved (for example to `cap-cms`), set these env vars:

```bash
export DIRECTUS_API_URL="https://cap-cms.your-domain.tld"
# Optional, if API requires auth:
export DIRECTUS_TOKEN="<directus_static_token>"
# Optional, if your target collection is not "feeds":
export DIRECTUS_COLLECTION="<collection_name>"
```

Then run:

```bash
uv run main.py import 5 corsi
```
