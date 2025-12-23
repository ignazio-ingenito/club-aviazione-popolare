from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from html import unescape
from pathlib import Path
from urllib.parse import ParseResult, urljoin, urlparse

import directus
import wordpress
import yaml
from bs4 import BeautifulSoup
from joblib import cpu_count
from loguru import logger


@dataclass(frozen=True, slots=True)
class Mapping:
    download: wordpress.WordpressDownload
    upload: directus.DirectusUpload


class Cache:
    data: dict[str, dict[str, any]]

    def __init__(self) -> None:
        self.data = {}

        if Path("parser.yaml").exists():
            with Path("parser.yaml").open("r") as f:
                self.data = yaml.safe_load(f) or {}

    def add(self, post: directus.DirectusPost) -> None:
        self.data[post.id_wordpress] = {
            "id_wordpress": post.id_wordpress,
            "id_directus": post.id_directus,
            "slug": post.slug,
            "title": post.title,
            "cover": post.cover,
            "date": post.date,
            "wp_link": post.link,
        }
        self.save()

    def save(self) -> None:
        with Path("parser.yaml").open("w") as f:
            yaml.safe_dump(self.data, f)

    def exists(self, id_wordpress: str) -> bool:
        if not self.data:
            return False
        return id_wordpress in self.data.keys()


cache = Cache()


def get_cover(mappings: tuple[Mapping]) -> directus.DirectusUpload:
    """Get the image with the largest size from the mappings upload.

    Args:
        mappings (tuple[Mapping]): A tuple of mappings.

    Returns:
        str: The image with the largest size.
    """
    return max(mappings, key=lambda m: m.upload.directus_size).upload


def process_tags(html: str, remove_empty_tags: bool = False) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # remove any style attributes from any tag
    for tag in soup.select("[style]"):
        tag.attrs["style"] = ""

    # remove any class attributes from any tag
    for tag in soup.select("[class]"):
        tag.attrs["class"] = ""

    # remove all the attrs excepting href,target,title from a
    for tag in soup.select("a"):
        tag.attrs = {
            k: v for k, v in tag.attrs.items() if k in "href,target,title".split(",")
        }
        tag.attrs["rel"] = "noopener noreferrer"

    # remove all the attrs excepting href,target,title from img
    for tag in soup.select("img"):
        tag.attrs = {
            k: v for k, v in tag.attrs.items() if k in "alt,src,title".split(",")
        }
        if not tag.attrs["alt"]:
            tag.attrs["alt"] = Path(tag.attrs["src"]).name

    # Remove empty tags
    if remove_empty_tags:
        for tag in soup.select("a,p,div"):
            if not "".join((f"{c}" for c in tag.contents)).strip():
                tag.unwrap()

    return soup.decode()


def process_title(title: str) -> str:
    return unescape(title).strip()


def upload_media(post: directus.DirectusPost) -> tuple[directus.DirectusPost, Mapping]:
    soup = BeautifulSoup(post.content, "html.parser")
    urls = tuple(
        set(
            tag.attrs[attr]
            for query, attr in (("img", "src"), ("a", "href"))
            for tag in soup.select(query)
            if Path(urlparse(tag.attrs[attr]).path).suffix
        )
    )
    excluded = tuple(
        (
            tag
            for query, attr in (("img", "src"), ("a", "href"))
            for tag in soup.select(query)
            if not Path(urlparse(tag.attrs[attr]).path).suffix
        )
    )
    for e in excluded:
        logger.warning(
            f"{e.prettify().replace('\n', '')} skipped as it's not downloadable"
        )

    cores = cpu_count()
    with ThreadPoolExecutor(max_workers=cores) as executor:
        # Use ThreadPoolExecutor to download from wordpress concurrently
        futures = (executor.submit(wordpress.download, url) for url in urls)
        downloads: tuple[wordpress.WordpressDownload, bytes] = tuple(
            future.result() for future in as_completed(futures)
        )

        if downloads:
            folder_id, _, _ = directus.create_folder(
                post.slug.lower().strip(), directus.NEWS_FOLDER_ID
            )

        # Use ThreadPoolExecutor to upload to Directus concurrently
        futures = (
            executor.submit(
                directus.upload,
                folder_id,
                wp.wordpress_filename,
                wp.wordpress_content_type,
                content,
            )
            for wp, content in downloads
        )
        uploads: list[Mapping] = [future.result() for future in as_completed(futures)]

    assets = zip((d for d, _ in downloads), uploads)
    mappings = tuple(Mapping(upload=u, download=d) for d, u in assets)

    # apply mappings to post content
    content = post.content
    for m in mappings:
        content = content.replace(
            m.download.wordpress_url,
            m.upload.directus_url,
        )

    return content, mappings


def process_post(post: directus.DirectusPost) -> directus.DirectusPost:
    logger.info(f"Processing post ID {post.id_wordpress} with title '{post.title}'")
    # Check if post already exists in Directus
    if cache.exists(post.id_wordpress):
        logger.info(f"Post ID {post.id_wordpress} already processed. Skipping.")
        return

    soup = BeautifulSoup(post.content, "html.parser")
    logger.debug(f"Parsed HTML:\n{soup.prettify()}")
    # Process title
    post.title = process_title(post.title)

    # Process tags
    post.content = process_tags(post.content)

    # Download media from wordpress and upload to Directus
    post.content, mappings = upload_media(post)

    # Set cover image if media exists
    post.cover = get_cover(mappings).directus_id

    # Post to Directus
    post = directus.create_item(post)

    # Save the post as processed
    cache.add(post)

    soup = BeautifulSoup(post.content, "html.parser")
    logger.debug(f"Proceseesd HTML:\n{soup.prettify()}")
    return post
