import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html import unescape
import hashlib
from pathlib import Path
from urllib.parse import urlparse, urljoin

import directus
import ai
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
            "category": post.category,
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

    def get_directus_id(self, id_wordpress: str) -> str | None:
        cached = self.data.get(id_wordpress)
        if not cached:
            return None
        return cached.get("id_directus")


cores = cpu_count()
# cores = 1
cache = Cache()


def get_cover(mappings: tuple[Mapping, ...] | None) -> str:
    """
    Return the id of the largest image in the mappings.

    If the mappings is empty, return the default cover id.

    The largest image is determined by its size in bytes.

    Args:
        mappings (Mapping): The mappings to use.

    Returns:
        str: The id of the largest image.
    """
    if not mappings:
        return directus.DIRECTUS_DEFAULT_COVER

    blocked_markers = ("logo-cap-300", "logocapazzuro")
    images = []
    for m in mappings:
        if not (m.upload.directus_content_type or "").startswith("image"):
            continue
        wp_name = (m.download.wordpress_filename or "").lower()
        upload_title = (m.upload.directus_title or "").lower()
        if any(marker in wp_name for marker in blocked_markers):
            continue
        if any(marker in upload_title for marker in blocked_markers):
            continue
        images.append(m)
    if not images:
        return directus.DIRECTUS_DEFAULT_COVER

    return max(images, key=lambda m: m.upload.directus_size).upload.directus_id


def process_tags(html: str, remove_empty_tags: bool = False) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.select("div"):
        tag.unwrap()

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
        if not tag.attrs.get("alt"):
            tag.attrs["alt"] = Path(tag.attrs["src"]).name

    # Remove empty tags
    if remove_empty_tags:
        for tag in soup.select("a,p,div"):
            if not "".join((f"{c}" for c in tag.contents)).strip():
                tag.unwrap()

    return soup.decode()


def process_title(title: str) -> str:
    return unescape(title).strip()


def remove_cover(post: directus.DirectusPost, mappings: Mapping) -> str:
    if not mappings:
        return post.content

    cover = next((m for m in mappings if m.upload.directus_id == post.cover), None)
    if not cover:
        return post.content

    soup = BeautifulSoup(post.content, "html.parser")
    for tag in soup.select("img"):
        if tag.attrs["src"] == cover.upload.directus_url:
            logger.info(f"Removing cover from post ID {post.id_wordpress}")
            tag.unwrap()
    return soup.decode()


def media_folder_name(post: directus.DirectusPost) -> str:
    year_month = post.date[:7] if post.date else "unknown-date"
    return f"{year_month}-{post.id_directus}-{post.slug}".lower().strip()


def create_media_folder(post: directus.DirectusPost) -> str:
    if not post.id_directus:
        raise ValueError("Cannot create a media folder before the Directus item exists.")

    category = str(post.category).lower().strip()
    category_id, _, _ = directus.create_folder(category, None)
    folder_id, _, _ = directus.create_folder(media_folder_name(post), category_id)
    return folder_id


def upload_media(post: directus.DirectusPost) -> tuple[str, tuple[Mapping, ...] | None]:
    soup = BeautifulSoup(post.content, "html.parser")
    replacements: dict[str, str] = {}
    thumbnail_names_to_remove: set[str] = set()

    def filename_from_url(value: str) -> str:
        return Path(urlparse(value).path).name

    for tag in soup.select("img"):
        src = tag.attrs.get("src")
        if not src:
            continue
        resolved = wordpress.resolve_fullsize_url(
            src if urlparse(src).scheme else urljoin(wordpress.WORDPRESS_BASE_URL, src)
        )
        if resolved and resolved != src:
            tag.attrs["src"] = resolved
            replacements[src] = resolved
            thumb_name = filename_from_url(src)
            if thumb_name:
                thumbnail_names_to_remove.add(thumb_name)

    post.content = soup.decode()
    if post.cover:
        original_cover = post.cover
        post.cover = wordpress.resolve_fullsize_url(post.cover)
        if post.cover != original_cover:
            thumb_name = filename_from_url(original_cover)
            if thumb_name:
                thumbnail_names_to_remove.add(thumb_name)

    def is_downloadable(url: str) -> bool:
        parsed = urlparse(url)
        # Allow relative URLs and explicit http(s) URLs only.
        if parsed.scheme and parsed.scheme not in {"http", "https"}:
            return False
        return bool(Path(parsed.path).suffix)

    urls = tuple(
        set(
            tag.attrs[attr]
            for query, attr in (("img", "src"), ("a", "href"))
            for tag in soup.select(query)
            if is_downloadable(tag.attrs[attr])
        )
    )
    if post.cover and is_downloadable(post.cover):
        urls = tuple(set([*[post.cover], *urls]))

    excluded = tuple(
        (
            tag.attrs[attr]
            for query, attr in (("img", "src"), ("a", "href"))
            for tag in soup.select(query)
            if not is_downloadable(tag.attrs[attr])
        )
    )
    for e in excluded:
        logger.warning(f"{e} skipped as it's not downloadable")

    with ThreadPoolExecutor(max_workers=cores) as executor:
        futures = (executor.submit(wordpress.download, url) for url in urls)
        downloads: list[tuple[wordpress.WordpressDownload, bytes]] = []
        for f in as_completed(futures):
            try:
                downloads.append(f.result())
            except Exception as exc:
                logger.warning(f"Failed to download media asset: {exc}")
    if downloads:
        folder_id = create_media_folder(post)
    else:
        logger.warning(f"No downloads for post ID {post.id_wordpress}")
        return post.content, None

    existing_files = directus.list_files_in_folder(folder_id)
    existing_by_name = {
        f.get("filename_download") or f.get("filename_disk"): f.get("id")
        for f in existing_files
        if f.get("filename_download") or f.get("filename_disk")
    }
    if thumbnail_names_to_remove:
        for name in list(thumbnail_names_to_remove):
            existing_id = existing_by_name.get(name)
            if existing_id:
                logger.info(
                    f"Replacing thumbnail {name} with full-size image for post ID {post.id_wordpress}."
                )
                directus.delete_file(existing_id)
                existing_by_name.pop(name, None)

    remaining: list[tuple[wordpress.WordpressDownload, bytes]] = []
    mappings: list[Mapping] = []
    for wp, content in downloads:
        existing_id = existing_by_name.get(wp.wordpress_filename)
        if existing_id:
            mappings.append(
                Mapping(
                    download=wp,
                    upload=directus.DirectusUpload(
                        directus_id=existing_id,
                        directus_filename=wp.wordpress_filename,
                        directus_folder=folder_id,
                        directus_title=wp.wordpress_filename,
                        directus_content_type=wp.wordpress_content_type,
                        directus_size=wp.wordpress_size,
                    ),
                )
            )
        else:
            remaining.append((wp, content))

    if remaining:
        with ThreadPoolExecutor(max_workers=cores) as executor:
            future_to_wp = {
                executor.submit(
                    directus.upload,
                    folder_id,
                    wp.wordpress_filename,
                    wp.wordpress_content_type,
                    content,
                ): wp
                for wp, content in remaining
            }
            for future in as_completed(future_to_wp):
                upload = future.result()
                wp = future_to_wp[future]
                mappings.append(Mapping(download=wp, upload=upload))

    mappings_tuple = tuple(mappings) if mappings else None

    # apply mappings to post content
    content = post.content
    if mappings_tuple:
        for m in mappings_tuple:
            content = content.replace(
                m.download.wordpress_url,
                m.upload.directus_url,
            )

    return content, mappings_tuple


async def format_post_with_ai(post: directus.DirectusPost) -> directus.DirectusPost:
    """Format post content using AI."""
    logger.info(f"Formatting content with AI for post ID {post.id_wordpress}")
    try:
        before_hash = hashlib.sha1(post.content.encode("utf-8")).hexdigest()
        before_len = len(post.content)
        formatted, used_model = await ai.format_content(post.content, post.title)
        if used_model:
            post.formatted_by = used_model
        post.content = formatted
        if post.content.strip().startswith("```"):
            post.content = post.content.strip().strip("`")
        post.content = process_tags(post.content)
        after_hash = hashlib.sha1(post.content.encode("utf-8")).hexdigest()
        after_len = len(post.content)
        if before_hash == after_hash:
            logger.warning(
                f"AI formatting returned identical content for post ID {post.id_wordpress} "
                f"(len={before_len})."
            )
        else:
            logger.info(
                f"AI formatting changed content for post ID {post.id_wordpress}: "
                f"{before_len} -> {after_len} chars."
            )
        logger.info(
            f"AI formatting completed for post ID {post.id_wordpress}"
        )
    except Exception as exc:
        logger.error(
            f"Failed to format content with AI for post ID {post.id_wordpress}: {exc}"
        )
        return post
    return post


async def process_post(
    post: directus.DirectusPost,
    ai_format: bool = False,
    overwrite: bool = False,
    overwrite_media: bool = False,
) -> directus.DirectusPost:
    logger.info(f"Processing post ID {post.id_wordpress} with title '{post.title}'")
    if overwrite_media:
        logger.info(f"Refreshing media for post ID {post.id_wordpress}.")
    cached_id = cache.get_directus_id(post.id_wordpress)
    if cached_id:
        if not overwrite:
            logger.info(
                f"Skipping post ID {post.id_wordpress}; already mapped to Directus item "
                f"{cached_id}. Use --overwrite to update it."
            )
            return post
        post.id_directus = cached_id
        logger.info(
            f"Post ID {post.id_wordpress} already mapped to Directus item {cached_id}. Updating."
        )

    existing_id = None
    if not cached_id:
        if post.original_uri:
            existing_id = directus.find_item("original_uri", post.original_uri)
        if not existing_id:
            existing_id = directus.find_item("slug", post.slug)
        if existing_id:
            if not overwrite:
                logger.info(
                    f"Skipping post ID {post.id_wordpress}; already exists in Directus "
                    f"as item {existing_id}. Use --overwrite to update it."
                )
                return post
            post.id_directus = existing_id

    if post.cover:
        logger.info(f"Post ID {post.id_wordpress} already has a cover.")

    # Process title
    post.title = process_title(post.title)

    # Process tags
    post.content = process_tags(post.content)

    if ai_format:
        post = await format_post_with_ai(post)

    # Create/update the article first so media folders can include id_directus.
    original_cover = post.cover
    post.cover = None
    try:
        post = directus.save_item(post)
    except Exception as exc:
        logger.error(f"Failed to save post ID {post.id_wordpress}: {exc}")
        return post
    post.cover = original_cover

    # Download media from wordpress and upload to Directus
    post.content, mappings = upload_media(post)

    # Set cover image if media exists
    post.cover = get_cover(mappings)

    # Remove the cover from the content
    post.content = remove_cover(post, mappings)

    # Post to Directus
    try:
        post = directus.save_item(post)
        # Save the WordPress to Directus mapping.
        cache.add(post)
    except Exception as exc:
        logger.error(f"Failed to import post ID {post.id_wordpress}: {exc}")

    return post
