from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from inventory.models import InventoryScope
from inventory.wxr import WordPressWXRMediaInventoryClient, WordPressWXRInventoryError


class WordPressWXRMediaInventoryTests(unittest.TestCase):
    def test_inventory_reads_attachment_records_without_network(self) -> None:
        with TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "cap.WordPress.2026-06-19.xml"
            export_path.write_text(self.sample_wxr(), encoding="utf-8")

            snapshot = WordPressWXRMediaInventoryClient(
                export_path=export_path
            ).inventory()
            manifest = snapshot.to_manifest(
                environment="synthetic",
                observed_at=datetime(2026, 6, 19, 16, 36, tzinfo=timezone.utc),
            )

        self.assertEqual(snapshot.base_url, "https://www.clubaviazionepopolare.org")
        self.assertEqual(len(snapshot.records), 2)
        self.assertEqual(snapshot.issues, ())
        self.assertEqual(
            [record.identity for record in snapshot.records],
            ["wordpress:media:3308", "wordpress:media:3309"],
        )
        self.assertEqual(snapshot.records[0].source_url, "https://example.test/slide-1.jpg")
        self.assertEqual(snapshot.records[0].data["post_parent"], 2961)
        self.assertEqual(manifest.scope, InventoryScope.SOURCE)
        self.assertEqual(manifest.metadata["source_format"], "wordpress_wxr")
        self.assertEqual(manifest.metadata["attachment_count"], 2)

    def test_invalid_attachment_id_is_an_issue_and_skipped(self) -> None:
        xml = self.sample_wxr().replace("<wp:post_id>3308</wp:post_id>", "<wp:post_id>bad</wp:post_id>")
        with TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "export.xml"
            export_path.write_text(xml, encoding="utf-8")

            snapshot = WordPressWXRMediaInventoryClient(
                export_path=export_path
            ).inventory()

        self.assertEqual(len(snapshot.records), 1)
        self.assertEqual(snapshot.issues[0].code, "invalid_wxr_attachment_id")

    def test_missing_attachment_url_is_warning_and_record_is_kept(self) -> None:
        xml = self.sample_wxr().replace(
            "<link>https://www.clubaviazionepopolare.org/?attachment_id=3308</link>",
            "<link></link>",
        ).replace(
            "<wp:attachment_url>https://example.test/slide-1.jpg</wp:attachment_url>",
            "<wp:attachment_url></wp:attachment_url>",
        )
        with TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "export.xml"
            export_path.write_text(xml, encoding="utf-8")

            snapshot = WordPressWXRMediaInventoryClient(
                export_path=export_path
            ).inventory()

        self.assertEqual(len(snapshot.records), 2)
        self.assertEqual(snapshot.records[0].identity, "wordpress:media:3308")
        self.assertIsNone(snapshot.records[0].source_url)
        self.assertEqual(snapshot.issues[0].code, "missing_wxr_attachment_url")
        self.assertEqual(snapshot.issues[0].identity, "wordpress:media:3308")

    def test_missing_export_fails_closed(self) -> None:
        with self.assertRaises(WordPressWXRInventoryError):
            WordPressWXRMediaInventoryClient(export_path="/tmp/does-not-exist.xml").inventory()

    def test_cli_writes_manifest_and_checksum(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            export_path = tmp_path / "cap.WordPress.2026-06-19.xml"
            export_path.write_text(self.sample_wxr(), encoding="utf-8")
            output_dir = tmp_path / "run"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "inventory",
                    "wordpress-wxr-media",
                    "--input",
                    str(export_path),
                    "--output-dir",
                    str(output_dir),
                    "--filename",
                    "wordpress-wxr-media.jsonl",
                    "--environment",
                    "synthetic",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            manifest_path = output_dir / "wordpress-wxr-media.jsonl"
            checksum_path = output_dir / "wordpress-wxr-media.jsonl.sha256"
            self.assertEqual(Path(summary["manifest"]), manifest_path)
            self.assertEqual(Path(summary["checksum"]), checksum_path)
            self.assertTrue(manifest_path.exists())
            self.assertTrue(checksum_path.exists())
            header = json.loads(manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(header["record_count"], 2)
            self.assertEqual(header["metadata"]["inventory_type"], "wordpress_wxr_media")

    @staticmethod
    def sample_wxr() -> str:
        return """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
  xmlns:wp="http://wordpress.org/export/1.2/">
  <channel>
    <title>CAP</title>
    <link>https://www.clubaviazionepopolare.org</link>
    <wp:base_site_url>https://www.clubaviazionepopolare.org</wp:base_site_url>
    <item>
      <title>slide-1</title>
      <link>https://www.clubaviazionepopolare.org/?attachment_id=3308</link>
      <wp:post_id>3308</wp:post_id>
      <wp:post_date>2020-02-11 14:14:45</wp:post_date>
      <wp:post_date_gmt>2020-02-11 13:14:45</wp:post_date_gmt>
      <wp:post_modified>2020-02-11 14:14:45</wp:post_modified>
      <wp:post_modified_gmt>2020-02-11 13:14:45</wp:post_modified_gmt>
      <wp:post_parent>2961</wp:post_parent>
      <wp:post_type>attachment</wp:post_type>
      <wp:status>inherit</wp:status>
      <wp:attachment_url>https://example.test/slide-1.jpg</wp:attachment_url>
    </item>
    <item>
      <title>regular post</title>
      <wp:post_id>99</wp:post_id>
      <wp:post_type>post</wp:post_type>
    </item>
    <item>
      <title>slide-2</title>
      <link>https://www.clubaviazionepopolare.org/?attachment_id=3309</link>
      <wp:post_id>3309</wp:post_id>
      <wp:post_parent>2961</wp:post_parent>
      <wp:post_type>attachment</wp:post_type>
      <wp:status>inherit</wp:status>
      <wp:attachment_url>https://example.test/slide-2.jpg</wp:attachment_url>
    </item>
  </channel>
</rss>
"""
