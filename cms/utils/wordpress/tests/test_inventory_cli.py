from __future__ import annotations

from datetime import datetime, timezone
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from inventory import InventoryManifest, InventoryScope, ManifestRecord
import inventory.__main__ as inventory_cli
from inventory.jsonl import manifest_jsonl_sha256
from inventory.writer import write_manifest_jsonl


class InventoryCliTests(unittest.TestCase):
    def test_help_command_has_no_network_and_succeeds(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "inventory", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("wordpress-core", result.stdout)
        self.assertIn("wordpress-wxr-media", result.stdout)
        self.assertIn("directus-core", result.stdout)
        self.assertIn("routes", result.stdout)
        self.assertIn("reconcile", result.stdout)

    def test_reconcile_command_writes_report_and_classifies_states(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_manifest = InventoryManifest(
                scope=InventoryScope.SOURCE,
                environment="synthetic",
                base_url="https://source.example.test",
                observed_at=datetime(2026, 6, 19, 17, 0, tzinfo=timezone.utc),
                records=[
                    ManifestRecord(
                        scope=InventoryScope.SOURCE,
                        entity_type="wordpress_post",
                        identity="wordpress:post:1",
                        source_url="https://example.test/article/",
                        data={"title": "Article"},
                    ),
                    ManifestRecord(
                        scope=InventoryScope.SOURCE,
                        entity_type="wordpress_post",
                        identity="wordpress:post:2",
                        source_url="https://example.test/new-article/",
                        data={"title": "New article"},
                    ),
                    ManifestRecord(
                        scope=InventoryScope.SOURCE,
                        entity_type="wordpress_post",
                        identity="wordpress:post:2582",
                        data={"title": "Historical"},
                    ),
                    ManifestRecord(
                        scope=InventoryScope.SOURCE,
                        entity_type="wordpress_post",
                        identity="wordpress:post:3",
                        source_url="https://example.test/dup/",
                        data={"title": "Duplicate"},
                    ),
                ],
            )
            target_manifest = InventoryManifest(
                scope=InventoryScope.TARGET,
                environment="synthetic",
                base_url="https://target.example.test",
                observed_at=datetime(2026, 6, 19, 17, 0, tzinfo=timezone.utc),
                records=[
                    ManifestRecord(
                        scope=InventoryScope.TARGET,
                        entity_type="directus_feed",
                        identity="directus:feed:10",
                        data={"original_uri": "https://example.test/article"},
                    ),
                    ManifestRecord(
                        scope=InventoryScope.TARGET,
                        entity_type="directus_feed",
                        identity="directus:feed:11",
                        data={"original_uri": "https://example.test/dup"},
                    ),
                    ManifestRecord(
                        scope=InventoryScope.TARGET,
                        entity_type="directus_feed",
                        identity="directus:feed:12",
                        data={"original_uri": "https://example.test/dup/"},
                    ),
                ],
            )
            source_path = tmp_path / "source.jsonl"
            target_path = tmp_path / "target.jsonl"
            write_manifest_jsonl(source_manifest, output_dir=tmp_path, filename="source.jsonl")
            write_manifest_jsonl(target_manifest, output_dir=tmp_path, filename="target.jsonl")
            legacy_map = tmp_path / "parser.yaml"
            legacy_map.write_text(
                "\n".join(
                    [
                        "2582:",
                        "  id_wordpress: \"2582\"",
                        "  id_directus: 175",
                        "  slug: welcome",
                        "  title: Benvenuti sul sito del CAP",
                        "  wp_link: https://example.test/legacy/",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            output_dir = tmp_path / "reconciliation"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "inventory",
                    "reconcile",
                    "--source",
                    str(source_path),
                    "--target",
                    str(target_path),
                    "--legacy-map",
                    str(legacy_map),
                    "--output-dir",
                    str(output_dir),
                    "--filename",
                    "reconciliation.json",
                    "--environment",
                    "synthetic",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            report_path = output_dir / "reconciliation.json"
            checksum_path = output_dir / "reconciliation.json.sha256"
            self.assertEqual(Path(summary["manifest"]), report_path)
            self.assertEqual(Path(summary["checksum"]), checksum_path)
            self.assertTrue(report_path.exists())
            self.assertTrue(checksum_path.exists())
            self.assertIn(summary["sha256"], checksum_path.read_text(encoding="utf-8"))

            report = json.loads(report_path.read_text(encoding="utf-8"))
            states = [item["state"] for item in report["results"]]
            self.assertIn("already_imported", states)
            self.assertIn("create_candidate", states)
            self.assertIn("manual_review", states)
            self.assertIn("conflict", states)
            self.assertEqual(report["metadata"]["historical_mapping_count"], 1)
            self.assertEqual(report["metadata"]["source_record_count"], 4)
            self.assertEqual(report["metadata"]["target_record_count"], 3)
            self.assertEqual(report["summary"]["already_imported"], 1)
            self.assertEqual(report["summary"]["create_candidate"], 1)
            self.assertEqual(report["summary"]["manual_review"], 1)
            self.assertEqual(report["summary"]["conflict"], 1)

    def test_routes_command_writes_jsonl_and_checksum(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app_dir = tmp_path / "app"
            self.write(app_dir / "page.tsx")
            self.write(app_dir / "news" / "[id]" / "page.tsx")
            output_dir = tmp_path / "run"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "inventory",
                    "routes",
                    "--app-dir",
                    str(app_dir),
                    "--output-dir",
                    str(output_dir),
                    "--filename",
                    "routes.jsonl",
                    "--environment",
                    "synthetic",
                    "--base-url",
                    "https://cap.example.test",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            manifest_path = output_dir / "routes.jsonl"
            checksum_path = output_dir / "routes.jsonl.sha256"
            self.assertEqual(Path(summary["manifest"]), manifest_path)
            self.assertEqual(Path(summary["checksum"]), checksum_path)
            self.assertTrue(manifest_path.exists())
            self.assertTrue(checksum_path.exists())
            self.assertIn(summary["sha256"], checksum_path.read_text())

            lines = [
                json.loads(line)
                for line in manifest_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(lines[0]["kind"], "manifest_header")
            self.assertEqual(lines[-1]["kind"], "manifest_trailer")
            self.assertEqual(lines[0]["metadata"]["inventory_type"], "next_routes")
            self.assertEqual(lines[0]["record_count"], 2)

    def test_network_backed_commands_use_inventory_clients_and_write_manifests(self) -> None:
        commands = {
            "wordpress-core": (
                "WordPressInventoryClient",
                "wordpress.jsonl",
                InventoryScope.SOURCE,
            ),
            "gallery": (
                "WordPressGalleryDiscoveryClient",
                "gallery.jsonl",
                InventoryScope.SOURCE,
            ),
            "directus-core": (
                "DirectusInventoryClient",
                "directus-public-view.jsonl",
                InventoryScope.TARGET,
            ),
        }

        for command, (client_name, filename, scope) in commands.items():
            with self.subTest(command=command), TemporaryDirectory() as tmp:
                fake_client = self.fake_client(scope)
                stdout = io.StringIO()
                with patch.object(inventory_cli, client_name, return_value=fake_client):
                    with redirect_stdout(stdout):
                        exit_code = inventory_cli.main(
                            [
                                command,
                                "--output-dir",
                                tmp,
                                "--filename",
                                filename,
                                "--environment",
                                "synthetic",
                            ]
                        )

                self.assertEqual(exit_code, 0)
                self.assertEqual(fake_client.enter_count, 1)
                self.assertEqual(fake_client.exit_count, 1)
                summary = json.loads(stdout.getvalue())
                self.assertEqual(Path(summary["manifest"]), Path(tmp) / filename)
                self.assertEqual(Path(summary["checksum"]), Path(tmp) / f"{filename}.sha256")
                self.assertTrue((Path(tmp) / filename).exists())

    def test_writer_refuses_existing_files_and_records_checksum(self) -> None:
        with TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest = InventoryManifest(
                scope=InventoryScope.TARGET,
                environment="synthetic",
                base_url="https://cap.example.test",
                observed_at=datetime(2026, 6, 19, 17, 0, tzinfo=timezone.utc),
                records=[
                    ManifestRecord(
                        scope=InventoryScope.TARGET,
                        entity_type="next_route",
                        identity="next:route:/",
                        data={"route": "/"},
                    )
                ],
            )
            stale = output_dir / "routes.jsonl"
            stale.write_text("stale\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                write_manifest_jsonl(
                    manifest,
                    output_dir=output_dir,
                    filename="routes.jsonl",
                )

            stale.unlink()
            result = write_manifest_jsonl(
                manifest,
                output_dir=output_dir,
                filename="routes.jsonl",
            )

            self.assertNotEqual(stale.read_text(encoding="utf-8"), "stale\n")
            self.assertEqual(result.sha256, manifest_jsonl_sha256(manifest))
            self.assertEqual(result.byte_count, result.manifest_path.stat().st_size)
            self.assertEqual(
                result.checksum_path.read_text(encoding="utf-8"),
                f"{result.sha256}  routes.jsonl\n",
            )
            self.assertEqual(list(output_dir.glob("*.tmp")), [])

    def test_writer_rejects_repository_local_output_directory(self) -> None:
        manifest = InventoryManifest(
            scope=InventoryScope.TARGET,
            environment="synthetic",
            base_url="https://cap.example.test",
            observed_at=datetime(2026, 6, 19, 17, 0, tzinfo=timezone.utc),
            records=[],
        )
        repository_root = Path(__file__).resolve().parents[4]
        with self.assertRaises(ValueError):
            write_manifest_jsonl(
                manifest,
                output_dir=repository_root / "tmp-run",
                filename="routes.jsonl",
                repository_root=repository_root,
            )

    def test_writer_rejects_unsafe_filename(self) -> None:
        manifest = InventoryManifest(
            scope=InventoryScope.TARGET,
            environment="synthetic",
            base_url="https://cap.example.test",
            observed_at=datetime(2026, 6, 19, 17, 0, tzinfo=timezone.utc),
            records=[],
        )
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_manifest_jsonl(
                    manifest,
                    output_dir=tmp,
                    filename="../routes.jsonl",
                )
            with self.assertRaises(ValueError):
                write_manifest_jsonl(
                    manifest,
                    output_dir=tmp,
                    filename="routes.json",
                )

    @staticmethod
    def write(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("export default function Page() { return null }\n")

    @staticmethod
    def fake_client(scope: InventoryScope):
        class FakeSnapshot:
            def to_manifest(self, *, environment, observed_at, metadata=None):
                return InventoryCliTests.synthetic_manifest(scope, environment)

        class FakeDiscovery:
            def to_manifest(self, *, base_url, environment, observed_at, metadata=None):
                return InventoryCliTests.synthetic_manifest(scope, environment)

        class FakeClient:
            def __init__(self):
                self.enter_count = 0
                self.exit_count = 0

            def __enter__(self):
                self.enter_count += 1
                return self

            def __exit__(self, exc_type, exc, traceback):
                self.exit_count += 1

            def inventory_core(self):
                return FakeSnapshot()

            def discover(self):
                return FakeDiscovery()

        return FakeClient()

    @staticmethod
    def synthetic_manifest(scope: InventoryScope, environment: str) -> InventoryManifest:
        return InventoryManifest(
            scope=scope,
            environment=environment,
            base_url="https://example.test",
            observed_at=datetime(2026, 6, 19, 17, 0, tzinfo=timezone.utc),
            records=[
                ManifestRecord(
                    scope=scope,
                    entity_type="synthetic",
                    identity=f"{scope.value}:synthetic:1",
                    data={"ok": True},
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
