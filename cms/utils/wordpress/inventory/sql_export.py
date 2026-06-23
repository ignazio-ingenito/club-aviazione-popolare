"""Local phpMyAdmin SQL export inventory helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import hashlib
from pathlib import Path
import re
from typing import Any, Iterable, Iterator, Mapping
from urllib.parse import urlparse

from .models import InventoryManifest, InventoryScope, ManifestRecord


WORDPRESS_BASE_URL = "https://www.clubaviazionepopolare.org"
TECHNICAL_POST_TYPE = "articoli-tecnici"
SPORT_AVIATION_SLUG = "sport-aviation"
SIZE_SUFFIX_RE = re.compile(r"-\d+x\d+(?=\.[A-Za-z0-9]{1,8}$)")
UPLOAD_PATH_RE = re.compile(r"/uploads/(\d{4}/\d{2}/[^?#]+)")


class WordPressSQLExportInventoryError(RuntimeError):
    """Raised when a local SQL export cannot be inventoried safely."""


@dataclass(frozen=True, slots=True)
class WordPressSQLExportSnapshot:
    base_url: str
    source_filename: str
    records: tuple[ManifestRecord, ...]
    metadata: Mapping[str, Any]

    def to_manifest(
        self,
        *,
        environment: str,
        observed_at: datetime,
    ) -> InventoryManifest:
        return InventoryManifest(
            scope=InventoryScope.SOURCE,
            environment=environment,
            base_url=self.base_url,
            observed_at=observed_at,
            records=self.records,
            metadata={
                "source_format": "phpmyadmin_sql",
                "inventory_type": "wordpress_sql_export",
                "source_filename": self.source_filename,
                **dict(self.metadata),
            },
        )


@dataclass(frozen=True, slots=True)
class _Post:
    post_id: int
    post_type: str
    status: str
    slug: str
    title: str
    content: str
    date: str
    modified: str
    parent: int
    guid: str
    mime_type: str
    password_set: bool


@dataclass(frozen=True, slots=True)
class _TermTaxonomy:
    term_taxonomy_id: int
    term_id: int
    taxonomy: str
    parent: int
    count: int


class WordPressSQLExportInventoryClient:
    """Inventory migration-relevant records from a local phpMyAdmin SQL dump."""

    def __init__(
        self,
        *,
        export_path: str | Path,
        table_prefix: str = "cap_",
    ) -> None:
        self.export_path = Path(export_path)
        self.table_prefix = table_prefix

    def inventory(self) -> WordPressSQLExportSnapshot:
        if not self.export_path.is_file():
            raise WordPressSQLExportInventoryError(
                f"WordPress SQL export does not exist: {self.export_path}"
            )

        posts = self._posts()
        postmeta = self._postmeta()
        terms = self._terms()
        taxonomies = self._term_taxonomies()
        relationships = self._term_relationships()
        options = self._options()
        user_roles = self._user_role_counts()
        approval_counts = self._approval_counts()

        technical_posts = {
            post_id: post
            for post_id, post in posts.items()
            if post.post_type == TECHNICAL_POST_TYPE and post.status == "publish"
        }
        child_attachments = {
            post_id: post
            for post_id, post in posts.items()
            if post.post_type == "attachment" and post.parent in technical_posts
        }

        taxonomy_records, taxonomy_summary = self._taxonomy_records(
            technical_post_ids=set(technical_posts),
            relationships=relationships,
            taxonomies=taxonomies,
            terms=terms,
        )
        required_media = self._required_media_records(
            child_attachments=child_attachments,
            attachment_paths={
                post_id: value
                for post_id, values in postmeta.items()
                for value in values.get("_wp_attached_file", ())
            },
        )
        records = [
            self._summary_record(
                posts=posts,
                technical_posts=technical_posts,
                child_attachments=child_attachments,
                options=options,
                user_roles=user_roles,
                approval_counts=approval_counts,
                taxonomy_summary=taxonomy_summary,
            ),
            *self._technical_post_records(
                technical_posts,
                relationships,
                taxonomies,
                terms,
            ),
            *required_media,
            *taxonomy_records,
        ]

        return WordPressSQLExportSnapshot(
            base_url=WORDPRESS_BASE_URL,
            source_filename=self.export_path.name,
            records=tuple(records),
            metadata={
                "table_prefix": self.table_prefix,
                "source_sha256": _file_sha256(self.export_path),
                "technical_post_type": TECHNICAL_POST_TYPE,
                "recommended_route_slug": SPORT_AVIATION_SLUG,
                "record_count": len(records),
                "technical_post_count": len(technical_posts),
                "required_media_count": len(required_media),
                "taxonomy_record_count": len(taxonomy_records),
                "member_rule": "soci_cap + pw_user_status=approved",
            },
        )

    def _posts(self) -> dict[int, _Post]:
        posts: dict[int, _Post] = {}
        for row in self._iter_insert_rows(f"{self.table_prefix}posts"):
            if len(row) < 23 or not _is_positive_int(row[0]):
                continue
            parent = int(row[17]) if _is_int(row[17]) else 0
            posts[int(row[0])] = _Post(
                post_id=int(row[0]),
                post_type=row[20],
                status=row[7],
                slug=row[11],
                title=row[5],
                content=row[4],
                date=row[2],
                modified=row[14],
                parent=parent,
                guid=row[18],
                mime_type=row[21],
                password_set=bool(row[10]),
            )
        return posts

    def _postmeta(self) -> dict[int, dict[str, list[str]]]:
        values: dict[int, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        for row in self._iter_insert_rows(f"{self.table_prefix}postmeta"):
            if len(row) >= 4 and _is_positive_int(row[1]):
                values[int(row[1])][row[2]].append(row[3])
        return values

    def _terms(self) -> dict[int, tuple[str, str]]:
        terms: dict[int, tuple[str, str]] = {}
        for row in self._iter_insert_rows(f"{self.table_prefix}terms"):
            if len(row) >= 3 and _is_positive_int(row[0]):
                terms[int(row[0])] = (row[1], row[2])
        return terms

    def _term_taxonomies(self) -> dict[int, _TermTaxonomy]:
        taxonomies: dict[int, _TermTaxonomy] = {}
        for row in self._iter_insert_rows(f"{self.table_prefix}term_taxonomy"):
            if len(row) < 6 or not _is_positive_int(row[0]):
                continue
            taxonomies[int(row[0])] = _TermTaxonomy(
                term_taxonomy_id=int(row[0]),
                term_id=int(row[1]) if _is_int(row[1]) else 0,
                taxonomy=row[2],
                parent=int(row[4]) if _is_int(row[4]) else 0,
                count=int(row[5]) if _is_int(row[5]) else 0,
            )
        return taxonomies

    def _term_relationships(self) -> dict[int, list[int]]:
        relationships: dict[int, list[int]] = defaultdict(list)
        for row in self._iter_insert_rows(f"{self.table_prefix}term_relationships"):
            if len(row) >= 2 and _is_positive_int(row[0]) and _is_positive_int(row[1]):
                relationships[int(row[0])].append(int(row[1]))
        return relationships

    def _options(self) -> dict[str, str]:
        options: dict[str, str] = {}
        for row in self._iter_insert_rows(f"{self.table_prefix}options"):
            if len(row) >= 3:
                options[row[1]] = row[2]
        return options

    def _user_role_counts(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        for row in self._iter_insert_rows(f"{self.table_prefix}usermeta"):
            if len(row) >= 4 and row[2] == f"{self.table_prefix}capabilities":
                counts.update(_serialized_role_names(row[3]))
        return counts

    def _approval_counts(self) -> Counter[str]:
        counts: Counter[str] = Counter()
        for row in self._iter_insert_rows(f"{self.table_prefix}usermeta"):
            if len(row) >= 4 and row[2] == "pw_user_status":
                counts[row[3] or "(empty)"] += 1
        return counts

    def _technical_post_records(
        self,
        technical_posts: Mapping[int, _Post],
        relationships: Mapping[int, list[int]],
        taxonomies: Mapping[int, _TermTaxonomy],
        terms: Mapping[int, tuple[str, str]],
    ) -> tuple[ManifestRecord, ...]:
        records: list[ManifestRecord] = []
        for post in technical_posts.values():
            topic_slugs: list[str] = []
            for term_taxonomy_id in relationships.get(post.post_id, ()):
                taxonomy = taxonomies.get(term_taxonomy_id)
                if taxonomy is None or taxonomy.taxonomy != "argomento":
                    continue
                _, slug = terms.get(taxonomy.term_id, ("", ""))
                if slug:
                    topic_slugs.append(slug)
            records.append(
                ManifestRecord(
                    scope=InventoryScope.SOURCE,
                    entity_type="wordpress_sql_articoli_tecnici",
                    identity=f"wordpress:articoli-tecnici:{post.post_id}",
                    source_url=_absolute_url(post.guid),
                    data={
                        "id": post.post_id,
                        "slug": post.slug,
                        "status": post.status,
                        "post_type": post.post_type,
                        "date": post.date,
                        "modified": post.modified,
                        "title": post.title,
                        "content_sha256": hashlib.sha256(
                            post.content.encode("utf-8")
                        ).hexdigest(),
                        "content_length": len(post.content),
                        "topic_slugs": sorted(set(topic_slugs)),
                        "route_slug": SPORT_AVIATION_SLUG,
                    },
                )
            )
        return tuple(records)

    def _required_media_records(
        self,
        *,
        child_attachments: Mapping[int, _Post],
        attachment_paths: Mapping[int, str],
    ) -> tuple[ManifestRecord, ...]:
        records: list[ManifestRecord] = []
        for post_id, attachment in child_attachments.items():
            upload_path = _normalize_upload_path(
                attachment_paths.get(post_id) or _upload_path_from_url(attachment.guid)
            )
            if not upload_path:
                continue
            records.append(
                ManifestRecord(
                    scope=InventoryScope.SOURCE,
                    entity_type="wordpress_sql_required_media",
                    identity=f"wordpress:media:{post_id}",
                    source_url=f"{WORDPRESS_BASE_URL}/wp-content/uploads/{upload_path}",
                    data={
                        "id": post_id,
                        "parent": attachment.parent,
                        "upload_path": upload_path,
                        "filename": Path(upload_path).name,
                        "mime_type": attachment.mime_type,
                        "route_slug": SPORT_AVIATION_SLUG,
                    },
                )
            )
        return tuple(records)

    def _taxonomy_records(
        self,
        *,
        technical_post_ids: set[int],
        relationships: Mapping[int, list[int]],
        taxonomies: Mapping[int, _TermTaxonomy],
        terms: Mapping[int, tuple[str, str]],
    ) -> tuple[tuple[ManifestRecord, ...], dict[str, Any]]:
        counts: Counter[tuple[str, str, str]] = Counter()
        for post_id in technical_post_ids:
            for term_taxonomy_id in relationships.get(post_id, ()):
                taxonomy = taxonomies.get(term_taxonomy_id)
                if taxonomy is None:
                    continue
                name, slug = terms.get(taxonomy.term_id, ("", ""))
                counts[(taxonomy.taxonomy, name, slug)] += 1

        records = tuple(
            ManifestRecord(
                scope=InventoryScope.SOURCE,
                entity_type="wordpress_sql_taxonomy_term",
                identity=f"wordpress:taxonomy:{taxonomy}:{slug}",
                data={
                    "taxonomy": taxonomy,
                    "name": name,
                    "slug": slug,
                    "technical_post_count": count,
                },
            )
            for (taxonomy, name, slug), count in sorted(counts.items())
            if taxonomy and slug
        )
        summary = {
            "relationship_count": sum(counts.values()),
            "unique_term_count": len(counts),
            "top_terms": [
                {
                    "taxonomy": taxonomy,
                    "name": name,
                    "slug": slug,
                    "count": count,
                }
                for (taxonomy, name, slug), count in counts.most_common(10)
            ],
        }
        return records, summary

    def _summary_record(
        self,
        *,
        posts: Mapping[int, _Post],
        technical_posts: Mapping[int, _Post],
        child_attachments: Mapping[int, _Post],
        options: Mapping[str, str],
        user_roles: Counter[str],
        approval_counts: Counter[str],
        taxonomy_summary: Mapping[str, Any],
    ) -> ManifestRecord:
        return ManifestRecord(
            scope=InventoryScope.SOURCE,
            entity_type="wordpress_sql_summary",
            identity="wordpress:sql:summary",
            data={
                "post_type_counts": dict(Counter(post.post_type for post in posts.values()).most_common()),
                "status_counts": dict(Counter(post.status for post in posts.values()).most_common()),
                "technical_post_type": TECHNICAL_POST_TYPE,
                "technical_post_count": len(technical_posts),
                "technical_post_password_count": sum(
                    1 for post in technical_posts.values() if post.password_set
                ),
                "technical_attachment_count": len(child_attachments),
                "recommended_route_slug": SPORT_AVIATION_SLUG,
                "sport_aviation_route_signal_count": _route_signal_count(posts.values()),
                "default_role": options.get("default_role"),
                "membership_rule": "soci_cap + pw_user_status=approved",
                "user_role_counts": dict(user_roles.most_common()),
                "approval_status_counts": dict(approval_counts.most_common()),
                "taxonomy_summary": taxonomy_summary,
            },
        )

    def _iter_insert_rows(self, table: str) -> Iterator[list[str]]:
        statement: list[str] = []
        with self.export_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not statement and not line.startswith(f"INSERT INTO `{table}`"):
                    continue
                statement.append(line)
                if line.rstrip().endswith(";"):
                    yield from _split_insert_rows(_insert_values("".join(statement)))
                    statement = []


def _insert_values(statement: str) -> str:
    if " VALUES\n" in statement:
        return statement.split(" VALUES\n", 1)[1].rstrip().rstrip(";")
    if " VALUES " in statement:
        return statement.split(" VALUES ", 1)[1].rstrip().rstrip(";")
    raise WordPressSQLExportInventoryError("INSERT statement has no VALUES block.")


def _split_insert_rows(values: str) -> Iterator[list[str]]:
    row: list[str] = []
    value: list[str] = []
    in_string = False
    escaped = False
    in_row = False

    for char in values:
        if in_string:
            if escaped:
                value.append(_unescape_mysql_char(char))
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                in_string = False
            else:
                value.append(char)
            continue

        if char == "'":
            in_string = True
        elif char == "(":
            if in_row:
                value.append(char)
            else:
                in_row = True
                row = []
                value = []
        elif char == ")" and in_row:
            row.append(_normalize_sql_scalar("".join(value).strip()))
            yield row
            in_row = False
            row = []
            value = []
        elif char == "," and in_row:
            row.append(_normalize_sql_scalar("".join(value).strip()))
            value = []
        elif in_row:
            value.append(char)


def _normalize_sql_scalar(value: str) -> str:
    return "" if value == "NULL" else value


def _unescape_mysql_char(char: str) -> str:
    return {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "0": "\0",
        "\\": "\\",
        "'": "'",
        '"': '"',
    }.get(char, char)


def _serialized_role_names(value: str) -> list[str]:
    return re.findall(r's:\d+:"([^"]+)";b:1;', value)


def _normalize_upload_path(value: str) -> str:
    cleaned = value.strip().split("?", 1)[0].split("#", 1)[0].lstrip("/")
    return SIZE_SUFFIX_RE.sub("", cleaned)


def _upload_path_from_url(value: str) -> str:
    match = UPLOAD_PATH_RE.search(value)
    return match.group(1) if match else ""


def _absolute_url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value.rstrip("/")
    return None


def _route_signal_count(posts: Iterable[_Post]) -> int:
    return sum(1 for post in posts if SPORT_AVIATION_SLUG in post.slug)


def _is_positive_int(value: str) -> bool:
    return value.isdigit() and int(value) > 0


def _is_int(value: str) -> bool:
    return value.isdigit() or (value.startswith("-") and value[1:].isdigit())


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
