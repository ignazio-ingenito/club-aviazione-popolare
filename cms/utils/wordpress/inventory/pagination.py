"""Pagination contracts shared by WordPress and Directus read-only clients."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Generic, Iterable, TypeVar


T = TypeVar("T")


class PaginationError(ValueError):
    """Raised when a paginated response is incomplete or internally inconsistent."""


@dataclass(frozen=True, slots=True)
class PageMetadata:
    page: int
    per_page: int
    total_items: int
    total_pages: int

    def __post_init__(self) -> None:
        if self.page < 1:
            raise PaginationError("page must be at least 1.")
        if self.per_page < 1:
            raise PaginationError("per_page must be at least 1.")
        if self.total_items < 0:
            raise PaginationError("total_items cannot be negative.")
        if self.total_pages < 0:
            raise PaginationError("total_pages cannot be negative.")

        expected_pages = ceil(self.total_items / self.per_page) if self.total_items else 0
        if self.total_pages != expected_pages:
            raise PaginationError(
                f"total_pages={self.total_pages} does not match "
                f"total_items={self.total_items} and per_page={self.per_page}; "
                f"expected {expected_pages}."
            )

        if self.total_pages == 0:
            if self.page != 1:
                raise PaginationError("An empty result must be represented as page 1.")
        elif self.page > self.total_pages:
            raise PaginationError(
                f"page={self.page} exceeds total_pages={self.total_pages}."
            )

    @property
    def expected_item_count(self) -> int:
        if self.total_pages == 0:
            return 0
        if self.page < self.total_pages:
            return self.per_page
        return self.total_items - (self.per_page * (self.total_pages - 1))


@dataclass(frozen=True, slots=True)
class InventoryPage(Generic[T]):
    metadata: PageMetadata
    items: tuple[T, ...]

    def __init__(self, metadata: PageMetadata, items: Iterable[T]) -> None:
        object.__setattr__(self, "metadata", metadata)
        object.__setattr__(self, "items", tuple(items))

        if len(self.items) != metadata.expected_item_count:
            raise PaginationError(
                f"Page {metadata.page} contains {len(self.items)} items; "
                f"expected {metadata.expected_item_count}."
            )


def merge_complete_pages(pages: Iterable[InventoryPage[T]]) -> tuple[T, ...]:
    """Validate a complete page sequence and return the flattened items."""

    page_list = tuple(pages)
    if not page_list:
        raise PaginationError("At least one page result is required.")

    first = page_list[0].metadata
    expected_numbers = (
        (1,) if first.total_pages == 0 else tuple(range(1, first.total_pages + 1))
    )
    actual_numbers = tuple(page.metadata.page for page in page_list)

    if actual_numbers != expected_numbers:
        raise PaginationError(
            f"Expected contiguous pages {expected_numbers}, got {actual_numbers}."
        )

    for page in page_list:
        metadata = page.metadata
        if (
            metadata.per_page != first.per_page
            or metadata.total_items != first.total_items
            or metadata.total_pages != first.total_pages
        ):
            raise PaginationError("Pagination totals changed between page responses.")

    merged = tuple(item for page in page_list for item in page.items)
    if len(merged) != first.total_items:
        raise PaginationError(
            f"Merged result contains {len(merged)} items; expected {first.total_items}."
        )
    return merged
