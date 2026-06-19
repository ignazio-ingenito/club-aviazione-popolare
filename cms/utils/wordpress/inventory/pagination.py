"""Strict pagination contracts used by read-only inventory clients."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import ceil
from typing import Any, Generic, TypeVar

from .errors import PaginationContractError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class PageMeta:
    page: int
    per_page: int
    total_items: int
    total_pages: int

    def __post_init__(self) -> None:
        if self.page < 1:
            raise PaginationContractError("page must be at least 1.")
        if self.per_page < 1:
            raise PaginationContractError("per_page must be at least 1.")
        if self.total_items < 0:
            raise PaginationContractError("total_items must not be negative.")
        if self.total_pages < 0:
            raise PaginationContractError("total_pages must not be negative.")

        expected_pages = ceil(self.total_items / self.per_page) if self.total_items else 0
        if self.total_pages != expected_pages:
            raise PaginationContractError(
                f"total_pages={self.total_pages} does not match total_items="
                f"{self.total_items} and per_page={self.per_page}; expected {expected_pages}."
            )
        if self.total_pages == 0 and self.page != 1:
            raise PaginationContractError("An empty collection can only be observed on page 1.")
        if self.total_pages > 0 and self.page > self.total_pages:
            raise PaginationContractError(
                f"page {self.page} exceeds declared total_pages {self.total_pages}."
            )

    def expected_item_count(self) -> int:
        if self.total_items == 0:
            return 0
        if self.page < self.total_pages:
            return self.per_page
        return self.total_items - self.per_page * (self.total_pages - 1)


@dataclass(frozen=True, slots=True)
class PageResult(Generic[T]):
    meta: PageMeta
    items: tuple[T, ...]

    def __init__(self, meta: PageMeta, items: Sequence[T]) -> None:
        object.__setattr__(self, "meta", meta)
        object.__setattr__(self, "items", tuple(items))
        expected = meta.expected_item_count()
        if len(self.items) != expected:
            raise PaginationContractError(
                f"Page {meta.page} contains {len(self.items)} items; expected {expected}."
            )


class PaginationAccumulator(Generic[T]):
    """Collect pages only when totals and page sizes prove completeness."""

    def __init__(self) -> None:
        self._pages: dict[int, PageResult[T]] = {}
        self._contract: tuple[int, int, int] | None = None

    def add(self, result: PageResult[T]) -> None:
        page = result.meta.page
        if page in self._pages:
            raise PaginationContractError(f"Page {page} was added more than once.")

        contract = (
            result.meta.per_page,
            result.meta.total_items,
            result.meta.total_pages,
        )
        if self._contract is None:
            self._contract = contract
        elif contract != self._contract:
            raise PaginationContractError(
                "Pagination totals or per_page changed between responses."
            )
        self._pages[page] = result

    @property
    def is_complete(self) -> bool:
        if self._contract is None:
            return False
        _, _, total_pages = self._contract
        if total_pages == 0:
            return set(self._pages) == {1}
        return set(self._pages) == set(range(1, total_pages + 1))

    def missing_pages(self) -> tuple[int, ...]:
        if self._contract is None:
            return ()
        _, _, total_pages = self._contract
        expected = {1} if total_pages == 0 else set(range(1, total_pages + 1))
        return tuple(sorted(expected - set(self._pages)))

    def items(self) -> tuple[T, ...]:
        if not self.is_complete:
            missing = self.missing_pages()
            detail = f" Missing pages: {missing}." if missing else ""
            raise PaginationContractError(f"Pagination is incomplete.{detail}")

        flattened: list[T] = []
        for page in sorted(self._pages):
            flattened.extend(self._pages[page].items)

        if self._contract is not None:
            _, total_items, _ = self._contract
            if len(flattened) != total_items:
                raise PaginationContractError(
                    f"Collected {len(flattened)} items but expected {total_items}."
                )
        return tuple(flattened)


def _header_int(headers: Mapping[str, Any], name: str) -> int:
    value: Any | None = None
    for key, candidate in headers.items():
        if str(key).lower() == name.lower():
            value = candidate
            break
    if value is None:
        raise PaginationContractError(f"Missing required pagination header {name}.")
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise PaginationContractError(
            f"Pagination header {name} is not an integer: {value!r}."
        ) from exc
    if parsed < 0:
        raise PaginationContractError(
            f"Pagination header {name} must not be negative."
        )
    return parsed


def wordpress_page_meta(
    *, page: int, per_page: int, headers: Mapping[str, Any]
) -> PageMeta:
    """Build strict metadata from WordPress REST pagination headers."""

    total_items = _header_int(headers, "X-WP-Total")
    total_pages = _header_int(headers, "X-WP-TotalPages")
    return PageMeta(
        page=page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
    )
