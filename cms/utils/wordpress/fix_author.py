#!/usr/bin/env python3
"""Fix author field for posts signed by Sergio Barlocchetti."""

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from loguru import logger
from dotenv import dotenv_values

AUTHOR_NAME = "Sergio Barlocchetti"
SCRIPT_DIR = Path(__file__).resolve().parent

# directus.py reads environment values at import time, so load the local .env first.
os.chdir(SCRIPT_DIR)
env_values = dotenv_values(SCRIPT_DIR / ".env")
if "DIRECTUS_TOKEN" not in env_values:
    os.environ.pop("DIRECTUS_TOKEN", None)
for key, value in env_values.items():
    if value is not None:
        os.environ[key] = value
os.environ.setdefault("DIRECTUS_API_URL", "https://cap-cms.skunklabs.uk")
os.environ.setdefault("DIRECTUS_COLLECTION", "feeds")

# Add the script directory to the path so we can import directus when executed elsewhere.
sys.path.append(str(SCRIPT_DIR))

from directus import DIRECTUS_COLLECTION_URL, client


def get_all_feeds():
    """Get all feeds from Directus"""
    logger.info("Fetching all feeds from Directus...")
    logger.info(f"Using URL: {DIRECTUS_COLLECTION_URL}")
    response = client.get(
        DIRECTUS_COLLECTION_URL,
        params={
            "fields": "id,title,content,author",
            "limit": -1,
        },
    )
    response.raise_for_status()
    data = response.json()
    return data.get("data", [])


def has_author_signature(content: str) -> bool:
    """Return True when the author name appears at the end of the post content."""
    if not content:
        return False

    # The imported content can end in plain text or HTML, for example:
    # "Sergio Barlocchetti", "<p>Sergio Barlocchetti</p>", or with trailing tags.
    tail = content.strip()[-500:]
    return bool(
        re.search(
            rf"{re.escape(AUTHOR_NAME)}(?:\s|&nbsp;|</?[^>]+>)*$",
            tail,
            flags=re.IGNORECASE,
        )
    )


def update_author(item_id, author_name):
    """Update the author field for a specific item"""
    url = urljoin(DIRECTUS_COLLECTION_URL + "/", str(item_id))
    payload = {"author": author_name}

    logger.info(f"Updating item {item_id} with author '{author_name}'")
    response = client.patch(url, json=payload)
    response.raise_for_status()

    logger.info(f"Successfully updated item {item_id}")
    return response.json()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List matching feed IDs without updating Directus.",
    )
    return parser.parse_args()


def main():
    """Main function to fix author fields"""
    args = parse_args()
    logger.info("Starting author fix script...")

    # Get all feeds
    feeds = get_all_feeds()
    logger.info(f"Found {len(feeds)} total feeds")

    # Filter feeds that contain "Sergio Barlocchetti" near the end
    feeds_to_update = []
    for feed in feeds:
        if feed.get("author") == AUTHOR_NAME:
            continue
        if has_author_signature(feed.get("content", "")):
            feeds_to_update.append(feed)

    logger.info(f"Found {len(feeds_to_update)} feeds that need author update")
    if args.dry_run:
        for feed in feeds_to_update:
            logger.info(f"Would update item {feed.get('id')}: {feed.get('title')}")
        return

    # Update each feed
    updated_count = 0
    for feed in feeds_to_update:
        try:
            update_author(feed["id"], AUTHOR_NAME)
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed to update item {feed['id']}: {e}")

    logger.info(f"Script completed. Updated {updated_count} items.")

if __name__ == "__main__":
    main()
