import parser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import directus
import polars as pl
import typer
import wordpress
from joblib import cpu_count
from loguru import logger

cores = cpu_count()

app = typer.Typer(
    help="WordPress Utility Tool",
    add_completion=False,
    no_args_is_help=True,
)


def get_workers() -> int:
    return cpu_count()


@app.command("delete")
def delete_feeds(id: Optional[int] = 15):
    """
    Delete feeds from Directus.
    """
    logger.info(f"Deleting feeds from Directus id={id or 0}...")
    directus.delete_items("feeds", id)
    logger.info(f"Deleting folders from News folder...")
    directus.delete_folders(directus.NEWS_FOLDER_ID)


@app.command("import")
def import_data(category: int, new_category: str):
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

    df = df.drop("categories")
    df = df.with_columns(pl.lit(new_category, dtype=pl.Utf8).alias("category"))

    posts = map(lambda p: directus.DirectusPost(**p), df.to_dicts())

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = executor.map(parser.process_post, list(posts))
        _ = [f for f in futures]


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
