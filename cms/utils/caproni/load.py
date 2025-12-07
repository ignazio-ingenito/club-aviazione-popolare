import re
from pathlib import Path

import httpx
import typer
import yaml
from loguru import logger

app = typer.Typer(help="Load data to a collection")

DIRECTUS_URL = "http://localhost:8055"


def get_client():
    return httpx.Client(
        base_url=DIRECTUS_URL,
        timeout=30,
    )


def lookup_asset_id(client, filename):
    """
    Returns Directus file ID for a given filename_download.
    """
    logger.debug(f"Searching asset for filename: {filename}")

    r = client.get(
        "/files", params={"filter[filename_download][_eq]": filename, "fields": "id"}
    )
    r.raise_for_status()
    data = r.json().get("data", [])

    if not data:
        logger.warning(f"No asset found for filename: {filename}")
        return None

    return data[0]["id"]


# ------------------------------------------------------------
# CLI command
# ------------------------------------------------------------
# @app.command()
def load_items(file: str):

    path = Path(__file__).parent / Path(file)
    logger.info(f"Fetching data from {path}...")

    data = yaml.safe_load(path.read_text())
    with get_client() as client:
        for row in data:
            r = client.post(
                f"items/{path.stem}",
                json={
                    "year": row.get("anno"),
                    "year": row.get("modello"),
                    "year": row.get("sigla"),
                    "year": row.get("costruttore"),
                },
            )
            r.raise_for_status()

    logger.success(f"All {len(data)} records were loaded")


if __name__ == "__main__":
    # app()
    load_items("caproni.yaml")
