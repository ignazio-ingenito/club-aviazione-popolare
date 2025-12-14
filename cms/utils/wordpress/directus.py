import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import date
from io import BytesIO
from os import cpu_count
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urljoin

import httpx
import pendulum
import polars as pl
from glom import glom
from loguru import logger

BASEURL = "https://www.clubaviazionepopolare.org"
NEWS_FOLDER = "032e5563-7527-4f0d-8659-c8717f7f82ef"

DIRECTUS_URL = "http://localhost:8055"
DIRECTUS_ITEMS = f"{DIRECTUS_URL}/items"
DIRECTUS_FILES = f"{DIRECTUS_URL}/files"
DIRECTUS_ASSETS = f"{DIRECTUS_URL}/assets"
DIRECTUS_FOLDERS = f"{DIRECTUS_URL}/folders"

TO_PRESERVE_FOLDERS = [
    "83ea26db-2677-404a-9f92-ff5cfc397741",  # corsi
    "032e5563-7527-4f0d-8659-c8717f7f82ef",  # news
    "a76309b7-1a90-4161-866d-190e42cef116",  # storia-dei-soci
]


@dataclass(slots=True)
class Post:
    post_id: Optional[int] = None
    slug: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    pub_date: Optional[pendulum.DateTime] = None
    status: Optional[str] = None
    folder_id: Optional[str] = None
    folder: Optional[str] = None
    hrefs: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)


@dataclass
class Feed:
    id: str
    author: str | None
    category: str | None
    content: str | None
    date_created: str | None
    date_updated: str | None
    date: str | None
    featured: str | None
    slug: str | None
    sort: str | None
    status: str | None
    title: str | None
    user_created: str | None
    user_updated: str | None


def create_folder(folder: str) -> str:
    if folder is None or folder == "":
        raise ValueError(f"Invalid folder value: {folder}")
    try:
        resp = httpx.post(
            DIRECTUS_FOLDERS,
            json={"name": folder, "parent": NEWS_FOLDER},
        )
        resp.raise_for_status()
        folder: str = glom(resp.json(), "data.name", default=None)
        logger.info(f"{folder} has been created")
        return glom(resp.json(), "data.id", default=None)
    except Exception as e:
        logger.error(f"{folder}: {e}")
        return None


def create_folders(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df

    rows = df.select(pl.struct(["folder_id", "images", "slug"])).to_series().to_list()

    cores: int | None = cpu_count()
    with ThreadPoolExecutor(max_workers=cores) as executor:
        ids = list(
            executor.map(
                lambda row: (
                    create_folder(row["images"], row["slug"])
                    if not row["folder_id"]
                    else row["folder_id"]
                ),
                rows,
            )
        )

    count = len(set(ids) - set([glom(r, "folder_id") for r in rows]))
    logger.info(f"{count} folders created")
    return df.with_columns(pl.Series("folder_id", ids))


def download(url) -> tuple[BytesIO, Path]:
    resp = httpx.get(url=urljoin(BASEURL, url))
    resp.raise_for_status()
    return BytesIO(resp.content), Path(url).name


def get_feed(id_post: str) -> Feed:
    try:
        resp = httpx.get(f"{DIRECTUS_ITEMS}/feeds/{id_post}")
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return Feed(**data)
    except Exception as e:
        logger.error(e)


def get_folder_from_src(id_src: str) -> str:
    try:
        resp = httpx.get(f"{DIRECTUS_FILES}/{id_src}")
        resp.raise_for_status()
        return resp.json().get("data", {}).get("folder")
    except Exception as e:
        logger.error(e)


def patch_feed(feed: Feed):
    data = asdict(feed)
    resp = httpx.patch(f"{DIRECTUS_ITEMS}/feeds/{feed.id}", json=data)
    resp.raise_for_status()


def remove_empty_folders():
    folders = glom(httpx.get(DIRECTUS_FOLDERS).json(), "data")
    files = glom(httpx.get(DIRECTUS_FILES).json(), "data")

    ids_folders = pl.DataFrame(folders).select("id").unique()
    ids_files = pl.concat(
        [
            pl.DataFrame(files)
            .filter(pl.col("folder").is_not_null())
            .select("folder")
            .rename({"folder": "id"})
            .unique(),
            pl.DataFrame(folders)
            .filter(pl.col("parent").is_null())
            .select("id")
            .unique(),
            pl.DataFrame(TO_PRESERVE_FOLDERS, schema=pl.Schema({"id": pl.String}))
            .filter(pl.col("id").is_not_null())
            .select("id")
            .unique(),
        ]
    )
    empty_folders = ids_folders.join(ids_files, on="id", how="anti").select("id")

    if empty_folders.is_empty():
        logger.info("No empty folders to delete")
        return

    cores: int = cpu_count()
    with ThreadPoolExecutor(max_workers=cores) as executor:
        res = executor.map(remove_folder, empty_folders.to_series().to_list())

    resp = pl.DataFrame(res)
    ok = resp.filter(pl.col(resp.columns[0]) == True).shape[0]
    ko = resp.filter(pl.col(resp.columns[0]) == False).shape[0]

    logger.warning(f"{ok} empty folders deleted - {ko} erros")
    return resp.filter(pl.col(resp.columns[0]) == True).to_series().to_list()


def remove_folder(folder_id: str) -> Tuple[str, bool]:
    try:
        resp: httpx.Response = httpx.delete(
            f"{DIRECTUS_FOLDERS}/{folder_id}",
        )
        resp.raise_for_status()
        return folder_id, resp.is_success
    except Exception as e:
        logger.error(e)
        return folder_id, False


def submit_post(
    slug: str,
    title: str,
    content: str,
    pub_date: date,
) -> str:
    # upload the post
    resp = httpx.post(
        url=f"{DIRECTUS_ITEMS}/feeds",
        json={
            "author": "Club Aviazione Popolare",
            "category": "news",
            "content": content,
            "date": pub_date.isoformat(),
            "slug": slug,
            "status": "published",
            "title": title,
        },
    )
    resp.raise_for_status()

    id_post = glom(resp.json(), "data.id")
    logger.info(f"New post submitted: {id_post}")


def upload(folder_id: str, bytes: BytesIO, filename: str, mimetype: str) -> str:
    resp = httpx.post(
        DIRECTUS_FILES,
        files={"file": (filename, bytes, mimetype)},
        data={"folder": folder_id, "title": filename},
    )
    resp.raise_for_status()
    return glom(resp.json(), "data.id")
