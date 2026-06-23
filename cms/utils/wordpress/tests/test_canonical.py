from __future__ import annotations

import math
import unittest
from datetime import datetime, timedelta, timezone

from inventory.canonical import canonical_json, sha256_hex
from inventory.errors import CanonicalizationError


class CanonicalJsonTests(unittest.TestCase):
    def test_mapping_order_and_unicode_are_stable(self) -> None:
        left = {"z": 1, "à": "volo", "nested": {"b": 2, "a": 1}}
        right = {"nested": {"a": 1, "b": 2}, "à": "volo", "z": 1}

        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertIn("à", canonical_json(left))
        self.assertEqual(sha256_hex(left), sha256_hex(right))

    def test_timezone_aware_datetimes_are_normalized_to_utc(self) -> None:
        value = datetime(2026, 6, 19, 12, 30, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(
            canonical_json({"at": value}),
            '{"at":"2026-06-19T10:30:00.000000Z"}',
        )

    def test_naive_datetime_is_rejected(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonical_json({"at": datetime(2026, 6, 19, 12, 30)})

    def test_non_finite_float_is_rejected(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(CanonicalizationError):
                    canonical_json({"value": value})

    def test_sets_are_rejected_instead_of_implicitly_reordered(self) -> None:
        with self.assertRaises(CanonicalizationError):
            canonical_json({"categories": {3, 6}})


if __name__ == "__main__":
    unittest.main()
