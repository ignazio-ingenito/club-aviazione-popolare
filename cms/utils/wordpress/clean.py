import re
from urllib.parse import urlparse

import cache
from bs4 import BeautifulSoup
from directus import get_feed, get_folder_from_src
from loguru import logger

BASEURL = "https://www.clubaviazionepopolare.org"
FORMAT_PATTERN = "ddd, DD MMM YYYY HH:mm:ss ZZ"

DIRECTUS_URL = "http://localhost:8055"
DIRECTUS_ITEMS = f"{DIRECTUS_URL}/items"
DIRECTUS_FILES = f"{DIRECTUS_URL}/files"
DIRECTUS_ASSETS = f"{DIRECTUS_URL}/assets"
DIRECTUS_FOLDERS = f"{DIRECTUS_URL}/folders"
NEWS_FOLDER = "032e5563-7527-4f0d-8659-c8717f7f82ef"


def tag_clean(html: str):
    soup = BeautifulSoup(html, "html.parser")
    tags = (
        "border",
        "class",
        "data-canvas-width",
        "height",
        "margin",
        "style",
        "width",
    )
    for tag in tags:
        for item in soup.select(f"[{tag}]"):
            del item.attrs[tag]

    out: str = str(soup).replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", out, re.MULTILINE)


def get_srcs(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    srcs = (urlparse(item.attrs["src"]) for item in set(soup.select(f"img")))
    srcs = (
        re.sub(r"^\/*assets\/*|\.\w+$", "", u.path)
        for u in srcs
        if u.hostname == "localhost"
    )
    return list(srcs)


if __name__ == "__main__":
    ids = cache.get_feed_ids()
    logger.info(f"{len(ids)} feeds have been found")

    df = cache.from_db("attivita")
    for id in ids:
        feed = get_feed(f"{id}")

        srcs = get_srcs(feed.content)
        if not srcs:
            logger.info(f"No src have been found for {id}")
            continue

        id_folder = get_folder_from_src(srcs[0])

        df.loc[df.pub_id == id, "id_folder"] = id_folder
        # logger.info(f"Processing {id} - {feed.title}")
        # feed.content = html_clean(feed.content)
        # feed.title = feed.title.title()
        # patch_feed(feed)
    cache.save("attivita", df)
