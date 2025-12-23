from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from typing import Optional
from urllib.parse import urljoin

import httpx
from joblib import Memory, cpu_count
from loguru import logger

DIRECTUS_API_URL = "http://localhost:8055/"
DIRECTUS_ASSETS_URL = "http://localhost:8055/assets/"
DIRECTUS_FEEDS_URL = "http://localhost:8055/items/feeds"
DIRECTUS_FILES_URL = "http://localhost:8055/files/"
DIRECTUS_FOLDERS_URL = "http://localhost:8055/folders/"
NEWS_FOLDER_ID = "032e5563-7527-4f0d-8659-c8717f7f82ef"
DIRECTUS_DEFAULT_COVER = "4f92d286-a525-4f7d-90ba-1dfbf719e04e"

cores = cpu_count()
memory = Memory(".cache", verbose=0)
client = httpx.Client(timeout=120, follow_redirects=True, verify=False)


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
    response = httpx.post(
        DIRECTUS_FOLDERS_URL, json={"name": folder_name, "parent": parent}, timeout=120
    )
    response.raise_for_status()
    data = (response.json()).get("data", {})
    folder_id = data.get("id")
    folder_name = data.get("id")
    parent = data.get("id")
    logger.info(f"Created folder {folder_name} ({folder_id}) in Directus.")
    return folder_id, folder_name, parent


def create_item(post: DirectusPost) -> DirectusPost:
    """Create a new collection item in Directus.

    Args:
        post (DirectusPost): The post to create.
        mappings (Mapping): The mappings to use.
    """
    data: dict = asdict(post)
    res = client.post(DIRECTUS_FEEDS_URL, json=data)
    res.raise_for_status()
    post.id_directus = res.json().get("data", {}).get("id")
    logger.info(f"Created item {post.id_directus} in Directus.")
    return post


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
    with ThreadPoolExecutor() as executor:
        executor.map(delete_file, files)

    # Delete the folder
    url: str = urljoin(DIRECTUS_FOLDERS_URL, f"{folder_id}")
    response = httpx.delete(url, timeout=120)
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
    response = httpx.delete(url, timeout=120)
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
    response = httpx.get(
        DIRECTUS_FOLDERS_URL, params={"filter[parent]": parent_id}, timeout=120
    )
    response.raise_for_status()
    folders = response.json().get("data")

    with ThreadPoolExecutor() as executor:
        executor.map(delete_folder, [f.get("id") for f in folders])


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
    url: str = urljoin(DIRECTUS_FEEDS_URL, f"{collection}/{id}")
    response = httpx.delete(url, timeout=120)
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
        executor.map(
            lambda id: delete_item(collection, id),
            [i.get("id") for i in get_items(collection, id)],
        )


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
    url: str = urljoin(DIRECTUS_FEEDS_URL, collection)
    if id:
        url += f"?filter[id][_gt]={id}"
        logger.info(f"Fetching items with id greater than {id}: {url}")

    response = httpx.get(url, timeout=120)
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
    response = httpx.get(
        DIRECTUS_FILES_URL, params={"filter[folder]": folder_id}, timeout=120
    )
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
    response = httpx.post(
        DIRECTUS_FILES_URL,
        files={"file": (filename, content, content_type)},
        data={"folder": folder_id or NEWS_FOLDER_ID},
        timeout=120,
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
