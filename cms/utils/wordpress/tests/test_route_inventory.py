from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from inventory.models import InventoryScope
from inventory.routes import RouteInventoryClient, RouteInventoryConfig


class RouteInventoryClientTests(unittest.TestCase):
    def test_inventory_discovers_pages_and_api_routes_deterministically(self) -> None:
        with TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            self.write(app_dir / "page.tsx")
            self.write(app_dir / "news" / "page.tsx")
            self.write(app_dir / "news" / "[id]" / "page.tsx")
            self.write(app_dir / "feed" / "[category]" / "[slug]" / "page.tsx")
            self.write(app_dir / "api" / "files" / "[id]" / "route.ts")
            self.write(app_dir / "public" / "logo.svg")

            client = RouteInventoryClient(
                config=RouteInventoryConfig(app_dir=app_dir)
            )
            snapshot = client.inventory()

        routes = [record.data["route"] for record in snapshot.records]
        self.assertEqual(
            routes,
            ["/", "/feed/[category]/[slug]", "/news", "/news/[id]", "/api/files/[id]"],
        )
        self.assertEqual(
            [record.identity for record in snapshot.records],
            [
                "next:route:/",
                "next:route:/feed/[category]/[slug]",
                "next:route:/news",
                "next:route:/news/[id]",
                "next:route:/api/files/[id]",
            ],
        )

    def test_collision_contract_marks_global_feed_routes(self) -> None:
        with TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            self.write(app_dir / "news" / "[id]" / "page.tsx")
            self.write(app_dir / "feed" / "[category]" / "[slug]" / "page.tsx")
            self.write(app_dir / "efficiency-race" / "page.tsx")
            self.write(app_dir / "trofei" / "[slug]" / "page.tsx")
            self.write(app_dir / "associazioni" / "[slug]" / "page.tsx")

            records = RouteInventoryClient(
                config=RouteInventoryConfig(app_dir=app_dir)
            ).inventory().records

        by_route = {record.data["route"]: record.data for record in records}
        self.assertEqual(
            by_route["/news/[id]"]["migration_collision_scope"],
            "global_feed_slug_or_numeric_id",
        )
        self.assertEqual(
            by_route["/feed/[category]/[slug]"]["migration_collision_scope"],
            "global_feed_slug",
        )
        self.assertEqual(
            by_route["/efficiency-race"]["migration_collision_scope"],
            "global_feed_slug",
        )
        self.assertEqual(
            by_route["/trofei/[slug]"]["migration_collision_scope"],
            "global_feed_slug",
        )
        self.assertEqual(
            by_route["/associazioni/[slug]"]["migration_collision_scope"],
            "dynamic_public_route",
        )
        self.assertEqual(
            by_route["/feed/[category]/[slug]"]["dynamic_segments"],
            ("category", "slug"),
        )
        self.assertIn(
            "/feed/*/[slug]",
            by_route["/feed/[category]/[slug]"]["collision_patterns"],
        )
        self.assertIn(
            "/feed/*/*",
            by_route["/feed/[category]/[slug]"]["collision_patterns"],
        )
        self.assertTrue(
            self.matches_pattern(
                "/feed/news/example",
                by_route["/feed/[category]/[slug]"]["collision_patterns"],
            )
        )

    def test_manifest_is_target_scoped_and_contains_no_issues(self) -> None:
        with TemporaryDirectory() as tmp:
            app_dir = Path(tmp) / "app"
            self.write(app_dir / "contatti" / "page.tsx")
            snapshot = RouteInventoryClient(
                config=RouteInventoryConfig(app_dir=app_dir)
            ).inventory()

        manifest = snapshot.to_manifest(
            environment="synthetic",
            base_url="https://cap.example.test",
            observed_at=datetime(2026, 6, 19, 16, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(manifest.scope, InventoryScope.TARGET)
        self.assertEqual(manifest.issues, ())
        self.assertEqual(manifest.records[0].identity, "next:route:/contatti")
        self.assertEqual(manifest.metadata["inventory_type"], "next_routes")
        self.assertTrue(manifest.manifest_sha256)

    def test_missing_app_directory_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            client = RouteInventoryClient(
                config=RouteInventoryConfig(app_dir=Path(tmp) / "missing")
            )
            with self.assertRaises(FileNotFoundError):
                client.inventory()

    @staticmethod
    def write(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("export default function Page() { return null }\n")

    @staticmethod
    def matches_pattern(candidate: str, patterns) -> bool:
        candidate_parts = candidate.strip("/").split("/")
        for pattern in patterns:
            pattern_parts = pattern.strip("/").split("/")
            if len(pattern_parts) != len(candidate_parts):
                continue
            if all(
                pattern_part == "*" or pattern_part == candidate_part
                for pattern_part, candidate_part in zip(pattern_parts, candidate_parts)
            ):
                return True
        return False


if __name__ == "__main__":
    unittest.main()
