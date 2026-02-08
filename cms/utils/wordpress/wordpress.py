from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from html import unescape
from itertools import chain
from math import ceil
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urljoin, urlparse

import httpx
import pendulum
from glom import glom
from joblib import Memory, cpu_count
from loguru import logger

WORDPRESS_BASE_URL = "https://www.clubaviazionepopolare.org"
WORDPRESS_API_URL = f"{WORDPRESS_BASE_URL}/wp-json/wp/v2/"

CATEGORIES = {
    # "2": "Area riservata",
    "3": "Eventi - Attività",  # To be imported in News
    # "4": "Consiglieri / Tecnici", -> Not used
    "5": "Corsi di aggiornamento", # -> Completed
    "6": "News",
    # "7": "Presidenti / Vicepresidenti", -> Not used
    "8": "Raduni - Efficiency Race",  # To be imported in News
    # "9": "Soci CAP",  -> Not used
    "14": "Storie dei Soci",
    "15": "Notiziari",
}

cores = cpu_count()
memory = Memory(".cache", verbose=0)
client = httpx.Client(timeout=120, follow_redirects=True, verify=False)


@dataclass(frozen=True, slots=True)
class WordpressDownload:
    wordpress_url: str
    wordpress_size: int
    wordpress_filename: str
    wordpress_content_type: str
    wordpress_redirect_location: Optional[str] = None


def download(url) -> tuple[WordpressDownload, bytes]:
    """
    Download a file from wordpress.

    Args:
        url (str): The url of the file to download.

    Returns:
        tuple[WordpressDownload, bytes]: A tuple of the WordpressDownload and the content of the file.
    """
    _url: str = url if urlparse(url).scheme else urljoin(WORDPRESS_BASE_URL, url)
    resp = client.get(_url)
    resp.raise_for_status()

    redirect_location: str | None = (
        f"{resp.url}" if resp.has_redirect_location else None
    )
    if redirect_location:
        logger.warning(f"Redirecting to {redirect_location}...")

    logger.debug(f"Downloaded {url}...")
    return (
        WordpressDownload(
            wordpress_url=url,
            wordpress_size=int(resp.headers.get("content-length", 0)),
            wordpress_filename=unquote(Path(urlparse(f"{resp.url}").path).name),
            wordpress_content_type=resp.headers.get("content-type"),
            wordpress_redirect_location=redirect_location,
        ),
        resp.content,
    )


def fetch_page(page: int) -> list[dict]:
    logger.debug(f"Fetching page {page} from WordPress...")
    resp = client.get(
        urljoin(WORDPRESS_API_URL, "posts"),
        params={"per_page": 100, "page": page, "_embed": "true"},
    )
    resp.raise_for_status()
    json = resp.json()
    logger.debug(f"Fetched {len(json)} posts from {resp.url.raw_path.decode('utf-8')}")
    return json


@memory.cache
def get_posts() -> list[dict]:
    """
    Fetch all posts.

    Returns:
        list[dict]: A list of posts
    """
    resp = client.head(
        urljoin(WORDPRESS_API_URL, "posts"),
        params={"per_page": 1, "page": 1},
    )
    logger.debug(f"Fetching posts from WordPress... {resp.url}")
    resp.raise_for_status()
    total_pages = ceil(int(resp.headers.get("X-WP-TotalPages", "1")) / 100)
    logger.info(f"Total pages to fetch: {total_pages}")

    with ThreadPoolExecutor(max_workers=cores) as executor:
        futures = [executor.submit(fetch_page, p) for p in range(1, total_pages + 1)]
        posts = [
            {
                "id_directus": None,
                "id_wordpress": str(p.get("id")),
                "date": pendulum.parse(p.get("date_gmt"), tz="Europe/Rome").isoformat(),
                "link": p.get("link"),
                "status": p.get("status"),
                "slug": p.get("slug"),
                "title": unescape(p.get("title", {}).get("rendered", "")),
                "content": unescape(p.get("content", {}).get("rendered", "")),
                "categories": p.get("categories", []),
                "cover": glom(
                    p, "_embedded.wp:featuredmedia.0.source_url", default=None
                ),
            }
            for p in chain.from_iterable([f.result() for f in futures])
        ]

        logger.info(f"Fetched {len(posts)} posts from WordPress.")
        return posts
