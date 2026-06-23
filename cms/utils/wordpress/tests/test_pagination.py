from __future__ import annotations

import unittest

from inventory.errors import PaginationContractError
from inventory.pagination import (
    PageMeta,
    PageResult,
    PaginationAccumulator,
    wordpress_page_meta,
)


class PaginationTests(unittest.TestCase):
    def test_wordpress_headers_are_case_insensitive(self) -> None:
        meta = wordpress_page_meta(
            page=2,
            per_page=100,
            headers={"x-wp-total": "250", "X-WP-TOTALPAGES": "3"},
        )
        self.assertEqual(meta.total_items, 250)
        self.assertEqual(meta.total_pages, 3)
        self.assertEqual(meta.expected_item_count(), 100)

    def test_missing_required_header_is_rejected(self) -> None:
        with self.assertRaises(PaginationContractError):
            wordpress_page_meta(
                page=1,
                per_page=100,
                headers={"X-WP-Total": "10"},
            )

    def test_declared_total_pages_must_match_total_items(self) -> None:
        with self.assertRaises(PaginationContractError):
            PageMeta(page=1, per_page=100, total_items=250, total_pages=2)

    def test_page_result_requires_exact_page_size(self) -> None:
        meta = PageMeta(page=1, per_page=100, total_items=150, total_pages=2)
        with self.assertRaises(PaginationContractError):
            PageResult(meta, list(range(99)))

    def test_accumulator_accepts_out_of_order_complete_pages(self) -> None:
        accumulator: PaginationAccumulator[int] = PaginationAccumulator()
        accumulator.add(
            PageResult(
                PageMeta(page=3, per_page=2, total_items=5, total_pages=3),
                [5],
            )
        )
        accumulator.add(
            PageResult(
                PageMeta(page=1, per_page=2, total_items=5, total_pages=3),
                [1, 2],
            )
        )
        accumulator.add(
            PageResult(
                PageMeta(page=2, per_page=2, total_items=5, total_pages=3),
                [3, 4],
            )
        )

        self.assertTrue(accumulator.is_complete)
        self.assertEqual(accumulator.items(), (1, 2, 3, 4, 5))

    def test_missing_page_fails_closed(self) -> None:
        accumulator: PaginationAccumulator[int] = PaginationAccumulator()
        accumulator.add(
            PageResult(
                PageMeta(page=1, per_page=2, total_items=5, total_pages=3),
                [1, 2],
            )
        )
        accumulator.add(
            PageResult(
                PageMeta(page=3, per_page=2, total_items=5, total_pages=3),
                [5],
            )
        )

        self.assertEqual(accumulator.missing_pages(), (2,))
        with self.assertRaises(PaginationContractError):
            accumulator.items()

    def test_totals_cannot_change_between_pages(self) -> None:
        accumulator: PaginationAccumulator[int] = PaginationAccumulator()
        accumulator.add(
            PageResult(
                PageMeta(page=1, per_page=2, total_items=4, total_pages=2),
                [1, 2],
            )
        )
        with self.assertRaises(PaginationContractError):
            accumulator.add(
                PageResult(
                    PageMeta(page=2, per_page=2, total_items=5, total_pages=3),
                    [3, 4],
                )
            )

    def test_duplicate_page_is_rejected(self) -> None:
        accumulator: PaginationAccumulator[int] = PaginationAccumulator()
        result = PageResult(
            PageMeta(page=1, per_page=2, total_items=2, total_pages=1),
            [1, 2],
        )
        accumulator.add(result)
        with self.assertRaises(PaginationContractError):
            accumulator.add(result)

    def test_empty_collection_is_complete_with_page_one(self) -> None:
        accumulator: PaginationAccumulator[int] = PaginationAccumulator()
        accumulator.add(
            PageResult(
                PageMeta(page=1, per_page=100, total_items=0, total_pages=0),
                [],
            )
        )
        self.assertTrue(accumulator.is_complete)
        self.assertEqual(accumulator.items(), ())


if __name__ == "__main__":
    unittest.main()
