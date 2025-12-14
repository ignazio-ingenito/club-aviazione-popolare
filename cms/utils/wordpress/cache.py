import logging
from pathlib import Path

import duckdb
import polars as pl
from loguru import logger

# Initialize logger
logger = logging.getLogger(__name__)


def to_db(path: Path, rows: list[dict]):
    try:
        # Convert rows (list of dicts) to Polars DataFrame
        df = pl.DataFrame(rows)

        # Insert the new column 'folder' (You can specify the column values)
        df = df.with_columns(pl.lit(path.stem).alias("folder"))

        # Establish connection to DuckDB
        conn = duckdb.connect(path)

        # Drop the existing table if it exists
        conn.execute(f"DROP TABLE IF EXISTS {path.stem}")

        # Create a new table from the Polars DataFrame
        conn.execute(f"CREATE TABLE {path.stem} AS SELECT * FROM df")

        # Log the success
        logger.info(f"{df.shape[0]} rows loaded into {path.stem} table.")

    except Exception as e:
        # Log any errors that occur
        logger.error(f"Error: {e}")

    finally:
        # Close the database connection
        conn.close()


def from_db(path: Path) -> pl.DataFrame:
    try:
        con = duckdb.connect(path)
        query = f"""
        SELECT *
        FROM   {path.stem}
        """
        return con.sql(query).pl()
    except Exception as e:
        logger.error(e)
        exit(0)
