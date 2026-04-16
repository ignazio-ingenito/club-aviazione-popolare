from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from html import unescape
from itertools import chain
from math import ceil
from pathlib import Path
import re
from typing import Optional
from urllib.parse import unquote, urljoin, urlparse

import httpx
import pendulum
from glom import glom
from joblib import Memory, cpu_count
from loguru import logger
from bs4 import BeautifulSoup
import directus

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
    # "14": "Storie dei Soci",
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
    resolved_url = resolve_fullsize_url(_url)
    if resolved_url != _url:
        logger.info(f"Using full-size image for {url}: {resolved_url}")
    resp = client.get(resolved_url)
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


def get_full_size_via_api(url: str) -> str:
    """
    Try to find the full-size image via WordPress API search.
    """
    parsed = urlparse(url)
    filename = Path(parsed.path).name
    # Remove known size suffixes
    base = filename
    for suffix in ['-thumbnail', '-medium', '-large']:
        if suffix in base.lower():
            base = re.sub(re.escape(suffix), '', base, flags=re.IGNORECASE)
            break
    # Remove -123x456
    base = re.sub(r'-\d+x\d+', '', base)
    # Now base should be name.ext
    search = Path(base).stem  # without extension
    try:
        resp = client.get(urljoin(WORDPRESS_API_URL, "media"), params={"search": search, "per_page": 5})
        resp.raise_for_status()
        medias = resp.json()
        for media in medias:
            source_url = media.get("source_url")
            if source_url:
                media_filename = Path(urlparse(source_url).path).name
                scaled_base = f"{Path(base).stem}-scaled{Path(base).suffix}"
                if media_filename.lower() in {base.lower(), scaled_base.lower()}:
                    # Found the attachment
                    media_details = media.get("media_details", {})
                    sizes = media_details.get("sizes", {})
                    full = sizes.get("full")
                    if full and "source_url" in full:
                        return full["source_url"]
    except Exception as e:
        logger.warning(f"Failed to get full size for {url} via API: {e}")
    return url


def resolve_fullsize_url(url: str) -> str:
    """
    For WordPress thumbnail URLs like name-225x300.jpg, try to find the full-size
    name.jpg and return it if it exists and is larger.
    """
    parsed = urlparse(url)
    filename = Path(parsed.path).name
    match = re.match(r"^(.*)-\d+x\d+(\.[^.]+)$", filename)
    if not match:
        return get_full_size_via_api(url)
    full_name = f"{match.group(1)}{match.group(2)}"
    if full_name == filename:
        return get_full_size_via_api(url)
    full_path = str(Path(parsed.path).with_name(full_name))
    full_url = parsed._replace(path=full_path).geturl()

    try:
        full_head = client.head(full_url)
        full_head.raise_for_status()
        if not (full_head.headers.get("content-type") or "").startswith("image"):
            return url
    except httpx.HTTPError:
        return url

    try:
        base_head = client.head(url)
        base_head.raise_for_status()
    except httpx.HTTPError:
        return full_url

    base_len = int(base_head.headers.get("content-length", 0))
    full_len = int(full_head.headers.get("content-length", 0))
    if full_len > base_len and full_len > 0:
        return full_url
    # If not larger, try API
    return get_full_size_via_api(url)


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
                "original_uri": p.get("link"),
            }
            for p in chain.from_iterable([f.result() for f in futures])
        ]

        logger.info(f"Fetched {len(posts)} posts from WordPress.")
        return posts


def strip_unwanted_images(post: dict) -> dict:
    """
    Remove any image whose filename matches known logo markers.
    Replace thumbnails with higher resolution versions if available.
    If the cover matches those markers, replace it with the default cover.
    """
    content = post.get("content")
    if content:
        soup = BeautifulSoup(content, "html.parser")
        unwanted_markers = ("logo-cap-300", "logocapazzuro")

        for tag in soup.select("img"):
            src = tag.attrs.get("src", "")
            if not src:
                continue
            logger.debug(f"Processing image: {src}")
            filename = Path(urlparse(src).path).name
            if any(marker in filename.lower() for marker in unwanted_markers):
                logger.info(f"Removing unwanted image: {src}")
                tag.unwrap()
            else:
                # Try to resolve to full-size
                full_src = resolve_fullsize_url(src)
                if full_src != src:
                    logger.info(f"Replacing thumbnail {src} with full-size {full_src}")
                    tag.attrs["src"] = full_src

        post["content"] = soup.decode()

    cover = post.get("cover")
    if cover:
        logger.debug(f"Processing cover: {cover}")
        filename = Path(urlparse(cover).path).name
        if any(marker in filename.lower() for marker in unwanted_markers):
            logger.info(f"Replacing unwanted cover {cover} with default")
            post["cover"] = directus.DIRECTUS_DEFAULT_COVER
        else:
            full_cover = resolve_fullsize_url(cover)
            if full_cover != cover:
                logger.info(f"Replacing cover thumbnail {cover} with full-size {full_cover}")
                post["cover"] = full_cover
    else:
        post["cover"] = directus.DIRECTUS_DEFAULT_COVER

    return post
