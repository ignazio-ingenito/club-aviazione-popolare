from io import StringIO
from pathlib import Path

from directus import Post
from glom import glom
from orjson import dumps, loads
from pendulum import from_format
from wpparser import parse

FORMAT_PATTERN = "ddd, DD MMM YYYY HH:mm:ss ZZ"


def clean(text: str) -> StringIO:
    """Clean the file before parsing and return a readable buffer (in memory)."""
    cleaned: str = "".join(
        [
            line
            for i, line in enumerate(text.splitlines(keepends=True))
            if i > 0 or line.strip() != ""
        ]
    )
    return StringIO(cleaned)


def from_json(file: Path) -> dict:
    return loads(file.read_text())


def to_json(file_in: Path, file_out: Path) -> list:
    text: str = file_in.read_text()
    text: str = clean(text)
    text = parse(text)
    file_out.write_text(dumps(text).decode("utf-8"))


def to_posts(rows: list):
    return [
        Post(
            title=glom(row, "title"),
            content=glom(row, "content"),
            pub_date=from_format(glom(row, "pub_date"), FORMAT_PATTERN),
            status=glom(row, "status"),
        )
        for row in rows
    ]
