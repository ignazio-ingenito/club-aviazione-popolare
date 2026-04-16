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

To format imported content with a free AI model via OpenRouter:

```bash
export AI_FORMATTER_URL="https://openrouter.ai/api/v1/chat/completions"
export AI_FORMATTER_MODEL="openrouter/free"
export OPENROUTER_API_KEY="<your_openrouter_key>"
uv run main.py import 15 notiziari --limit=2 --ai-format
```

The formatter asks the model to return an HTML fragment, improve pagination and
readability, and fix grammar without changing the meaning or adding information.

To rerun a single post and overwrite the existing Directus item:

```bash
uv run main.py import 15 notiziari --post guardiamoci-dentro-non-soltanto-agli-aeroplani-notiziario-gennaio-2024 --overwrite
```

`--post` accepts a Directus ID, WordPress ID, WordPress slug, or full WordPress URL.

To refresh media and cover assets for existing imported posts without AI formatting:

```bash
uv run main.py import 6 news --limit=10 --overwrite-media
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
