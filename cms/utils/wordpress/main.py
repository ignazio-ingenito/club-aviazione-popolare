import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

import polars as pl
import typer
from bs4 import BeautifulSoup
from cache import from_db, to_db
from directus import (
    Post,
    create_folder,
    download,
    remove_empty_folders,
    submit_post,
    upload,
)
from loguru import logger
from wordpress import from_json, to_json, to_posts

BASEURL = "https://www.clubaviazionepopolare.org"
FORMAT_PATTERN = "ddd, DD MMM YYYY HH:mm:ss ZZ"

app = typer.Typer()


def make_slug(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        (
            df["pub_date"].dt.strftime("%Y-%m-")
            + df["title"]
            .str.to_lowercase()
            .str.replace_all(r"[^a-z0-9\s]", "", literal=False)
            .str.replace_all(r"\s+", "-", literal=False)
            .str.replace_all(r"-\d{4}$", "", literal=False)
        ).alias("slug")
    )


def sanitize_attrs(df: pl.DataFrame) -> pl.DataFrame:
    # Define the sanitization function
    def _sanitize(_html: str) -> str:
        soup = BeautifulSoup(_html, "html.parser")
        tags = (
            "border",
            "class",
            "data-canvas-width",
            "height",
            "margin",
            "style",
            "width",
        )
        # Remove specified attributes from tags
        for tag in tags:
            for item in soup.select(f"[{tag}]"):
                del item.attrs[tag]

        # Replace &nbsp; with a space, and clean up excess whitespace
        out = str(soup).replace("&nbsp;", " ")
        return re.sub(r"\s+", " ", out, re.MULTILINE)

    # Step 1: Extract the content column to be sanitized
    contents = df["content"].to_list()

    # Step 2: Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        sanitized_contents = list(executor.map(_sanitize, contents))

    # Step 3: Add the sanitized content back to the DataFrame
    return df.with_columns(pl.Series("content", sanitized_contents))


def submit(df: pl.DataFrame):
    EXT_RE = re.compile(r"\.[a-zA-Z0-9]+$")

    assets: dict = {}
    for row in df.iter_rows(named=True):
        soup = BeautifulSoup(row["content"], "html.parser")

        tags: list = soup.select("a[href], img[src]")
        if not tags:
            continue

        # process assets
        urls = []
        id_folder: str = create_folder(row["folder"])
        for tag in tags:
            attr = "href" if tag.name == "a" else "src"
            url = tag.get(attr)
            if not url:
                continue

            parsed = urlparse(url)
            if not EXT_RE.search(parsed.path):
                continue

            urls.append(url)

        for url in set(urls):
            # upload
            bytes, name = download(parsed.path)

            # download
            mime: str = f"image/{Path(url).suffix[1:]}".replace("jpg", "jpeg")
            id_file: str = upload(id_folder, bytes, name, mime)

            assets[url] = id_file

        # process content
        count = 0
        content = row["content"]
        for key, val in assets.items():
            content = content.replace(key, f"/assets/{val}")
            count += 1

        # submit the article
        submit_post(row["slug"], row["title"], content, row["pub_date"])

    return assets


@app.command()
def main(task: str, rebuild: bool = False):
    basedir: Path = Path(__file__).parent / "import"
    xml_file: Path = Path(basedir / f"{task}.xml")
    json_file: Path = Path(basedir / f"{task}.json")
    duck_db: Path = Path(basedir / f"{task}.db")

    if rebuild:
        logger.info(f"Force rebuilding")
        Path(json_file).unlink(missing_ok=True)
        Path(duck_db).unlink(missing_ok=True)

    remove_empty_folders()

    logger.info(f"Loading {task}")
    if not xml_file.exists():
        logger.error(f"{xml_file} missing")
        exit(0)
    if not json_file.exists():
        logger.info(f"Parsing xml to json")
        to_json(xml_file, json_file)
    if not duck_db.exists():
        logger.info(f"Building cache from json")
        rows: list[Post] = to_posts(from_json(json_file).get("posts", {}))
        to_db(duck_db, [asdict(r) for r in rows if r.status == "publish"])

    df: pl.DataFrame = from_db(duck_db)
    # create slug
    df = make_slug(df)
    df = df.with_columns(pl.col("slug").alias("folder"))
    # fix html tags
    df = sanitize_attrs(df)
    # get images from content
    submit(df)

    logger.info("Completed!")


if __name__ == "__main__":
    app()
