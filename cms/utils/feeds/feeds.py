import re
from pathlib import Path

import httpx
import typer
from loguru import logger

app = typer.Typer(
    help="Fix Directus article image src attributes by mapping filenames to asset IDs."
)

DIRECTUS_URL = "http://localhost:8055"
TOKEN = "YOUR_TOKEN_HERE"  # replace or pass via env


def get_client():
    return httpx.Client(
        base_url=DIRECTUS_URL,
        # headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=30,
    )


# ------------------------------------------------------------
# Extract filenames from <img src="...">
# ------------------------------------------------------------
IMG_REGEX = re.compile(r'<img[^>]+src="([^"]+)"')


def extract_filenames(content: str):
    """
    Extracts image *filenames* (last part of path) from img tags.
    """
    matches = IMG_REGEX.findall(content)
    filenames = [Path(url).name for url in matches]
    filenames = [re.sub(r"-\d+x\d+(?=\.\w+$)", "", f) for f in filenames]
    return matches, filenames


# ------------------------------------------------------------
# Query Directus for a file by filename_download
# ------------------------------------------------------------
def lookup_asset_id(client, filename):
    """
    Returns Directus file ID for a given filename_download.
    """
    logger.debug(f"Searching asset for filename: {filename}")

    r = client.get(
        "/files", params={"filter[filename_download][_eq]": filename, "fields": "id"}
    )
    r.raise_for_status()
    data = r.json().get("data", [])

    if not data:
        logger.warning(f"No asset found for filename: {filename}")
        return None

    return data[0]["id"]


# ------------------------------------------------------------
# Replace src URLs with Directus /assets/{id}
# ------------------------------------------------------------
def replace_src(content, original_src_list, filename_list, id_list):
    """
    Rebuilds the HTML/markdown replacing each original <img src="">
    with the new asset ID URL.
    """
    new_content = content

    for original_src, filename, asset_id in zip(
        original_src_list, filename_list, id_list
    ):
        if not asset_id:
            continue
        new_url = f"/assets/{asset_id}"
        new_content = new_content.replace(original_src, new_url)
        logger.info(f"Replaced {original_src} → {new_url}")

    return new_content


# ------------------------------------------------------------
# CLI command
# ------------------------------------------------------------
# @app.command()
def fix_article(article_url: str):
    """
    Fetch article → fix images → update article.
    """

    client = get_client()

    logger.info(f"Fetching article {article_url}...")
    r = client.get(article_url)
    r.raise_for_status()

    article = r.json()["data"]
    content = article.get("content", "")

    if not content:
        logger.error("Article has no content field.")
        raise typer.Exit(1)

    # Extract current <img src="...">
    original_src_list, filename_list = extract_filenames(content)
    logger.info(f"Found {len(filename_list)} image(s) in article.")

    if not filename_list:
        logger.info("No images to replace.")
        raise typer.Exit(0)

    # Look up asset IDs
    id_list = [lookup_asset_id(client, fn) for fn in filename_list]

    # Replace in content
    new_content = replace_src(content, original_src_list, filename_list, id_list)

    if new_content == content:
        logger.error("No modifications were applied")
        return

    # Update the article
    logger.info("Updating article in Directus...")
    r = client.patch(article_url, json={"content": new_content})
    r.raise_for_status()

    logger.success(f"Article {article_url} updated successfully.")


if __name__ == "__main__":
    # app()
    fix_article("/items/feeds/9")
