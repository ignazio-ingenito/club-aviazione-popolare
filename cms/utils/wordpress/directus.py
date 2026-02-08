import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from copy import deepcopy
from typing import Optional
from urllib.parse import urljoin

import httpx
from joblib import Memory, cpu_count
from loguru import logger

load_dotenv()

DIRECTUS_API_URL = os.getenv("DIRECTUS_API_URL", "http://localhost:8055").rstrip("/") + "/"
DIRECTUS_ASSETS_URL = urljoin(DIRECTUS_API_URL, "assets/")
DIRECTUS_ITEMS_URL = urljoin(DIRECTUS_API_URL, "items/")
DIRECTUS_COLLECTION = os.getenv("DIRECTUS_COLLECTION", "feeds").strip()
DIRECTUS_COLLECTION_URL = urljoin(DIRECTUS_ITEMS_URL, DIRECTUS_COLLECTION)
DIRECTUS_FILES_URL = urljoin(DIRECTUS_API_URL, "files/")
DIRECTUS_FOLDERS_URL = urljoin(DIRECTUS_API_URL, "folders/")
NEWS_FOLDER_ID = os.getenv("NEWS_FOLDER_ID", "032e5563-7527-4f0d-8659-c8717f7f82ef")
DIRECTUS_DEFAULT_COVER = "b52ad437-35b5-407d-a7b1-6c0f3f8a1c97"

cores = cpu_count()
memory = Memory(".cache", verbose=0)
DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN")
client = httpx.Client(
    timeout=120,
    follow_redirects=True,
    verify=False,
    headers={"Authorization": f"Bearer {DIRECTUS_TOKEN}"} if DIRECTUS_TOKEN else None,
)


@dataclass
class DirectusPost:
    id_directus: str
    id_wordpress: str
    date: str
    link: str
    status: str
    slug: str
    title: str
    content: str
    category: str
    cover: Optional[str] = None
    featured: Optional[bool] = False


@dataclass(frozen=True, slots=True)
class DirectusUpload:
    directus_id: str
    directus_filename: str
    directus_folder: str
    directus_title: str
    directus_content_type: str
    directus_size: int

    @property
    def directus_url(self) -> str:
        return urljoin(DIRECTUS_ASSETS_URL, self.directus_id)


def create_folder(folder_name: str, parent: str) -> tuple[str, str, str]:
    """
    Create a folder in Directus.
    """
    query = client.get(
        DIRECTUS_FOLDERS_URL,
        params={
            "filter[name][_eq]": folder_name,
            "filter[parent][_eq]": parent,
            "limit": 1,
        },
    )
    query.raise_for_status()
    existing = query.json().get("data", [])
    if existing:
        data = existing[0]
        logger.info(f"Reusing folder {data.get('name')} ({data.get('id')}) in Directus.")
        return data.get("id"), data.get("name"), data.get("parent")

    response = client.post(DIRECTUS_FOLDERS_URL, json={"name": folder_name, "parent": parent})
    response.raise_for_status()
    data = (response.json()).get("data", {})
    folder_id = data.get("id")
    created_folder_name = data.get("name")
    folder_parent = data.get("parent")
    logger.info(f"Created folder {created_folder_name} ({folder_id}) in Directus.")
    return folder_id, created_folder_name, folder_parent


def create_item(post: DirectusPost) -> DirectusPost:
    """Create a new collection item in Directus.

    Args:
        post (DirectusPost): The post to create.
        mappings (Mapping): The mappings to use.
    """
    data: dict = asdict(post)
    # Internal tracking field; not part of the Directus payload.
    data.pop("id_directus", None)
    data["status"] = "published"

    category = data.get("category")
    if isinstance(category, str):
        category = category.strip()
        if category.isdigit():
            data["category"] = int(category)
        else:
            logger.warning(
                f"Dropping unsupported category value '{category}' for post '{post.slug}'. Expected numeric ID."
            )
            data.pop("category", None)
    elif isinstance(category, int):
        data["category"] = category
    elif category is not None:
        logger.warning(
            f"Dropping unsupported category type '{type(category).__name__}' for post '{post.slug}'."
        )
        data.pop("category", None)

    # The target collection cover is UUID-backed, so keep cover as-is.
    attempts: list[dict] = [
        data,
        {k: v for k, v in data.items() if k != "cover"},
        {k: v for k, v in data.items() if k != "category"},
        {k: v for k, v in data.items() if k not in {"category", "cover"}},
    ]
    # Remove duplicate payload variants while preserving order.
    unique_attempts: list[dict] = []
    seen: set[str] = set()
    for payload in attempts:
        key = repr(sorted(payload.items()))
        if key in seen:
            continue
        seen.add(key)
        unique_attempts.append(payload)
    attempts = unique_attempts

    last_error: Optional[httpx.HTTPStatusError] = None
    content_fallback_added = False
    for idx, payload in enumerate(attempts, start=1):
        try:
            res = client.post(DIRECTUS_COLLECTION_URL, json=payload)
            res.raise_for_status()
            post.id_directus = res.json().get("data", {}).get("id")
            logger.info(f"Created item {post.id_directus} in Directus (attempt {idx}).")
            return post
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 403:
                logger.error(
                    f"Forbidden while writing to collection '{DIRECTUS_COLLECTION}' at "
                    f"{DIRECTUS_COLLECTION_URL}. Set DIRECTUS_COLLECTION to the right collection "
                    "name and ensure DIRECTUS_TOKEN has create/read permissions."
                )
            # If record already exists (e.g. unique slug/id_wordpress), treat as idempotent.
            if exc.response.status_code == 400 and "RECORD_NOT_UNIQUE" in exc.response.text:
                existing = None
                id_wordpress = payload.get("id_wordpress")
                slug = payload.get("slug")
                if id_wordpress:
                    existing = find_item("id_wordpress", id_wordpress)
                if not existing and slug:
                    existing = find_item("slug", slug)
                if existing:
                    post.id_directus = existing
                    logger.info(
                        f"Item already exists for post '{post.slug}'. Reusing Directus ID {post.id_directus}."
                    )
                    return post

            # Some target schemas enforce short content lengths.
            # Retry once with truncated content and once with content removed.
            if (
                exc.response.status_code == 400
                and "VALUE_TOO_LONG" in exc.response.text
                and '"field":"content"' in exc.response.text
                and "content" in payload
                and not content_fallback_added
            ):
                shorter = deepcopy(payload)
                shorter["content"] = str(shorter["content"])[:255]
                attempts.append(shorter)
                no_content = {k: v for k, v in payload.items() if k != "content"}
                attempts.append(no_content)
                content_fallback_added = True
            last_error = exc
            logger.warning(
                f"Create item failed (attempt {idx}) with {exc.response.status_code}: {exc.response.text[:300]}"
            )

    assert last_error is not None
    logger.error(
        f"Failed to create item for post '{post.slug}' after retries. Response: {last_error.response.text}"
    )
    raise last_error


def find_item(field: str, value: str) -> Optional[str]:
    response = client.get(
        DIRECTUS_COLLECTION_URL, params={f"filter[{field}][_eq]": value, "limit": 1}
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    if not data:
        return None
    return data[0].get("id")


def delete_folder(folder_id: str) -> None:
    # Delete all the files within the folder
    """
    Delete a folder in Directus.

    Args:
        folder_id (str): The id of the folder to delete.

    Notes:
        This function deletes all the files within the folder before deleting the folder itself.
    """
    files: tuple[str] = list_files(folder_id)
    with ThreadPoolExecutor(max_workers=cores) as executor:
        futures = executor.map(delete_file, files)
        _ = [f for f in futures]

    # Delete the folder
    url: str = urljoin(DIRECTUS_FOLDERS_URL, f"{folder_id}")
    response = client.delete(url)
    response.raise_for_status()
    logger.info(f"Deleted folder with ID {folder_id} from Directus.")


def delete_file(file_id: str) -> None:
    # Delete the folder
    """
    Delete a file from Directus.

    Args:
        file_id (str): The id of the file to delete.

    Notes:
        This function deletes a file from Directus.
    """
    url: str = urljoin(DIRECTUS_FILES_URL, f"{file_id}")
    response = client.delete(url)
    response.raise_for_status()
    logger.info(f"Deleted file with ID {file_id} from Directus.")


def delete_folders(parent_id: str) -> None:
    """
    Delete all the folders within a given parent folder.

    Args:
        parent_id (str): The id of the parent folder to delete.

    Notes:
        This function deletes all the folders within the given parent folder.
    """
    response = client.get(DIRECTUS_FOLDERS_URL, params={"filter[parent]": parent_id})
    response.raise_for_status()
    folders = response.json().get("data")

    with ThreadPoolExecutor(max_workers=cores) as executor:
        futures = executor.map(delete_folder, [f.get("id") for f in folders])
        _ = [f for f in futures]


def delete_item(collection: str, id: int) -> None:
    """
    Delete an item from a Directus collection.

    Args:
        collection (str): The collection ID.
        id (int): The item ID.

    Notes:
        This function will skip deletion of items with ID <= 15 to protect essential data.
    """
    if id <= 15:
        logger.warning(
            f"Skipping deletion of item with ID {id} to protect essential data."
        )
        return
    url: str = urljoin(DIRECTUS_ITEMS_URL, f"{collection}/{id}")
    response = client.delete(url)
    response.raise_for_status()
    logger.info(f"Deleted item with ID {id} from collection {collection}.")


def delete_items(collection: str, id: int) -> None:
    """
    Delete items from a Directus collection.

    Args:
        collection (str): The collection ID.
        id (int): The item ID.

    Notes:
        This function will skip deletion of items with ID <= 15 to protect essential data.
    """
    with ThreadPoolExecutor(max_workers=cores) as executor:
        futures = executor.map(
            lambda id: delete_item(collection, id),
            [i.get("id") for i in get_items(collection, id)],
        )
        _ = [f for f in futures]


def get_items(collection: str, id: int) -> list[dict]:
    """
    Fetch items from a Directus collection.

    Args:
        collection (str): The collection ID.
        id (int): The item ID to fetch items with id greater than.

    Returns:
        list[dict]: A list of items in the collection.

    Notes:
        This function will fetch items with id greater than the given id if the id is greater than 0.
    """
    url: str = urljoin(DIRECTUS_ITEMS_URL, collection)
    if id:
        url += f"?filter[id][_gt]={id}"
        logger.info(f"Fetching items with id greater than {id}: {url}")

    response = client.get(url)
    response.raise_for_status()
    data = response.json()
    return data.get("data", [])


def list_files(folder_id: str) -> tuple[str]:
    """
    List files in a given folder.

    Args:
        folder_id (str): The folder ID.

    Returns:
        tuple[str]: A tuple of file IDs.

    Notes:
        This function lists all the files within a given folder.
    """
    response = client.get(DIRECTUS_FILES_URL, params={"filter[folder]": folder_id})
    response.raise_for_status()
    return tuple(f.get("id") for f in response.json().get("data"))


def upload(
    folder_id: str, filename: str, content_type: str, content: bytes
) -> DirectusUpload:
    """
    Upload a file to Directus.

    Args:
        folder_id (str): The ID of the folder to upload the file to.
        filename (str): The filename of the file to upload.
        content_type (str): The content type of the file to upload.
        content (bytes): The content of the file to upload.

    Returns:
        DirectusUpload: A DirectusUpload object containing the details of the uploaded file.

    Notes:
        If the folder ID is not provided, the file will be uploaded to the news folder.
    """
    response = client.post(
        DIRECTUS_FILES_URL,
        files={"file": (filename, content, content_type)},
        data={"folder": folder_id or NEWS_FOLDER_ID},
    )
    response.raise_for_status()
    data: dict = response.json()
    logger.debug(
        f"Uploaded file {filename} with ID {data.get('data', {}).get('id')} to Directus."
    )
    return DirectusUpload(
        directus_id=data.get("data", {}).get("id"),
        directus_filename=data.get("data", {}).get("filename_disk"),
        directus_folder=data.get("data", {}).get("folder"),
        directus_title=data.get("data", {}).get("title"),
        directus_content_type=data.get("data", {}).get("type"),
        directus_size=int(data.get("data", {}).get("filesize", 0)),
    )
