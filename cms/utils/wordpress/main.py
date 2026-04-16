import asyncio
from dataclasses import asdict
import re
import shutil
from urllib.parse import urlparse

import parser
import ai

import directus
import polars as pl
import typer
import wordpress
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich import box

app = typer.Typer(
    help="WordPress Utility Tool",
    add_completion=False,
    no_args_is_help=True,
)


def normalize_notiziari_post(post: dict) -> dict:
    if str(post.get("category", "")).lower().strip() != "notiziari":
        return post

    slug = post.get("slug")
    if isinstance(slug, str):
        post["slug"] = re.sub(
            r"^cari-soci-notiziario-",
            "notiziario-",
            slug,
            flags=re.IGNORECASE,
        )

    title = post.get("title")
    if isinstance(title, str):
        title = re.sub(
            r"^\s*cari-soci-notiziario-",
            "notiziario-",
            title,
            flags=re.IGNORECASE,
        )
        post["title"] = re.sub(
            r"^\s*cari\s+soci\s*[-\u2013\u2014]\s*",
            "",
            title,
            flags=re.IGNORECASE,
        )

    return post


def post_matches_selector(post: dict, selector: str) -> bool:
    selector = selector.strip().rstrip("/")
    if not selector:
        return False
    if "://" in selector:
        selector = urlparse(selector).path.strip("/").split("/")[-1]
    return selector in {
        str(post.get("id_wordpress", "")),
        str(post.get("slug", "")),
        str(post.get("link", "")).rstrip("/").split("/")[-1],
    }


def resolve_post_selector(selector: str) -> str:
    selector = selector.strip()
    if not selector or not selector.isdigit():
        return selector

    item = directus.get_item(selector, fields="id,original_uri,slug,title")
    if not item:
        return selector

    original_uri = item.get("original_uri")
    if original_uri:
        logger.info(
            f"Resolved Directus item {selector} to WordPress URL '{original_uri}'."
        )
        return original_uri

    slug = item.get("slug")
    if slug:
        logger.info(
            f"Directus item {selector} has no original_uri; falling back to slug '{slug}'."
        )
        return slug

    return selector


def find_existing_directus_id(post: directus.DirectusPost) -> str | None:
    cached_id = parser.cache.get_directus_id(post.id_wordpress)
    if cached_id:
        return cached_id

    if post.original_uri:
        existing_id = directus.find_item("original_uri", post.original_uri)
        if existing_id:
            return existing_id

    return directus.find_item("slug", post.slug)


@app.command("delete")
def delete_feeds(category: int):
    """
    Delete feeds from Directus.
    """
    logger.info(
        f"Deleting items from Directus collection '{directus.DIRECTUS_COLLECTION}' id>{category}..."
    )
    directus.delete_items(directus.DIRECTUS_COLLECTION, category)
    logger.info("Deleting folders from News folder...")
    directus.delete_folders(directus.NEWS_FOLDER_ID)


@app.command("import")
def import_data(
    category: int,
    new_category: str,
    limit: int = None,
    dry_run: bool = False,
    ai_format: bool = False,
    overwrite: bool = False,
    overwrite_media: bool = False,
    post: str = None,
):
    """
    Import data from WordPress to Directus.

    category_id: Category ID.
    """
    logger.info("Getting data from WordPress...")
    wp_posts = wordpress.get_posts()
    df = pl.from_dicts(wp_posts).sort("date")
    logger.info(f"Fetched {len(wp_posts)} feeds from Directus.")

    df = df.filter(pl.col("categories").list.contains(category))
    logger.info(f"{df.shape[0]} posts for '{wordpress.CATEGORIES.get(str(category))}'")

    if post:
        post = resolve_post_selector(post)
        df = df.filter(
            pl.struct(["id_wordpress", "slug", "link"]).map_elements(
                lambda row: post_matches_selector(row, post),
                return_dtype=pl.Boolean,
            )
        )
        logger.info(f"{df.shape[0]} posts matched selector '{post}'")

    if dry_run:
        # For dry run, apply limit and show results
        if limit:
            df = df.head(limit)
            logger.info(f"Limiting to {limit} posts.")
        print_results_from_dataframe(df)
        logger.info("Dry run mode enabled. No data will be imported.")
        return

    df = df.drop("categories")
    df = df.with_columns(pl.lit(new_category, dtype=pl.Utf8).alias("category"))

    posts_dicts = df.to_dicts()
    posts_dicts = [normalize_notiziari_post(p) for p in posts_dicts]
    posts_list = [directus.DirectusPost(**p) for p in posts_dicts]
    effective_overwrite = overwrite or overwrite_media

    if overwrite_media and ai_format:
        logger.warning("--overwrite-media disables AI formatting for this run.")
        ai_format = False

    if ai_format:
        logger.info(f"AI formatter model: {ai.AI_FORMATTER_MODEL}")
        logger.info(f"AI formatter URL: {ai.AI_FORMATTER_URL}")

    if effective_overwrite:
        for item in posts_list:
            existing_id = find_existing_directus_id(item)
            if existing_id:
                item.id_directus = existing_id

    # Filter out posts that already exist in Directus unless overwrite is True
    if not effective_overwrite:
        logger.info("Checking for existing posts in Directus...")
        filtered_posts = []
        for post in posts_list:
            if limit and len(filtered_posts) >= limit:
                break  # Stop once we have enough posts to process
            try:
                existing_id = find_existing_directus_id(post)
                if existing_id:
                    logger.info(f"Skipping post {post.id_wordpress} '{post.title}' - already exists in Directus (ID: {existing_id})")
                    continue
                else:
                    filtered_posts.append(post)
            except Exception as e:
                logger.warning(f"Could not check if post {post.id_wordpress} exists: {e}. Proceeding with import.")
                filtered_posts.append(post)
        posts_list = filtered_posts
        logger.info(f"Processing {len(posts_list)} new posts")

    elif limit:
        # When overwrite=True/overwrite_media=True, still apply the limit
        posts_list = posts_list[:limit]
        logger.info(f"Limiting to {limit} posts (overwrite mode)")

    posts_list = [
        directus.DirectusPost(**wordpress.strip_unwanted_images(asdict(post)))
        for post in posts_list
    ]

    async def process_all():
        for post in posts_list:
            await parser.process_post(
                post,
                ai_format=ai_format,
                overwrite=effective_overwrite,
                overwrite_media=overwrite_media,
            )

    asyncio.run(process_all())



def print_results_from_dataframe(df, columns=None):
    if not columns:
        columns = [
            "id_wordpress",
            "id_directus",
            "title",
            "link",
        ]
    console = Console(width=shutil.get_terminal_size().columns)
    table = Table(
        box=box.SIMPLE_HEAD,
        expand=True,
        show_edge=False,
        header_style="bold",
    )
    for col_name in df.columns:
        table.add_column(col_name)
    for row in df[columns].iter_rows():
        # Convert all elements to strings so Rich can render them
        table.add_row(*[str(item) for item in row][:5])

    console.print(table)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    WordPress Utility.
    """
    # If the user didn't type a subcommand (like 'import'), show help
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
