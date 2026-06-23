from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from inventory.models import InventoryScope
from inventory.sql_export import (
    WordPressSQLExportInventoryClient,
    WordPressSQLExportInventoryError,
)


class WordPressSQLExportInventoryTests(unittest.TestCase):
    def test_inventory_reads_technical_posts_media_terms_and_membership(self) -> None:
        with TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "wordpress.sql"
            export_path.write_text(self.sample_sql(), encoding="utf-8")

            snapshot = WordPressSQLExportInventoryClient(export_path=export_path).inventory()
            manifest = snapshot.to_manifest(
                environment="synthetic",
                observed_at=datetime(2026, 6, 22, 8, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(manifest.scope, InventoryScope.SOURCE)
        self.assertEqual(manifest.metadata["inventory_type"], "wordpress_sql_export")
        self.assertEqual(manifest.metadata["technical_post_count"], 1)
        self.assertEqual(manifest.metadata["required_media_count"], 1)
        self.assertEqual(manifest.metadata["recommended_route_slug"], "sport-aviation")

        by_type = {}
        for record in snapshot.records:
            by_type.setdefault(record.entity_type, []).append(record)

        summary = by_type["wordpress_sql_summary"][0].data
        self.assertEqual(summary["default_role"], "soci_cap")
        self.assertEqual(summary["approval_status_counts"], {"approved": 1})
        self.assertEqual(summary["user_role_counts"], {"soci_cap": 1})
        self.assertEqual(summary["technical_post_password_count"], 0)
        self.assertEqual(summary["sport_aviation_route_signal_count"], 1)

        article = by_type["wordpress_sql_articoli_tecnici"][0]
        self.assertEqual(article.identity, "wordpress:articoli-tecnici:101")
        self.assertEqual(article.data["slug"], "wing-ribs")
        self.assertEqual(article.data["route_slug"], "sport-aviation")
        self.assertEqual(list(article.data["topic_slugs"]), ["costruzione"])
        self.assertIn("content_sha256", article.data)
        self.assertNotIn("content", article.data)

        media = by_type["wordpress_sql_required_media"][0]
        self.assertEqual(media.identity, "wordpress:media:201")
        self.assertEqual(media.data["upload_path"], "2024/09/wing-ribs.pdf")
        self.assertEqual(media.data["filename"], "wing-ribs.pdf")

        term = by_type["wordpress_sql_taxonomy_term"][0]
        self.assertEqual(term.data["taxonomy"], "argomento")
        self.assertEqual(term.data["slug"], "costruzione")
        self.assertEqual(term.data["technical_post_count"], 1)

    def test_missing_export_fails_closed(self) -> None:
        with self.assertRaises(WordPressSQLExportInventoryError):
            WordPressSQLExportInventoryClient(export_path="/tmp/does-not-exist.sql").inventory()

    def test_cli_writes_manifest_and_checksum(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            export_path = tmp_path / "wordpress.sql"
            export_path.write_text(self.sample_sql(), encoding="utf-8")
            output_dir = tmp_path / "run"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "inventory",
                    "wordpress-sql-export",
                    "--input",
                    str(export_path),
                    "--output-dir",
                    str(output_dir),
                    "--filename",
                    "wordpress-sql-export.jsonl",
                    "--environment",
                    "synthetic",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            manifest_path = output_dir / "wordpress-sql-export.jsonl"
            checksum_path = output_dir / "wordpress-sql-export.jsonl.sha256"
            self.assertEqual(Path(summary["manifest"]), manifest_path)
            self.assertEqual(Path(summary["checksum"]), checksum_path)
            self.assertTrue(manifest_path.exists())
            self.assertTrue(checksum_path.exists())

            header = json.loads(manifest_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(header["metadata"]["inventory_type"], "wordpress_sql_export")
            self.assertEqual(header["metadata"]["technical_post_count"], 1)

    @staticmethod
    def sample_sql() -> str:
        return """INSERT INTO `cap_posts` (`ID`, `post_author`, `post_date`, `post_date_gmt`, `post_content`, `post_title`, `post_excerpt`, `post_status`, `comment_status`, `ping_status`, `post_password`, `post_name`, `to_ping`, `pinged`, `post_modified`, `post_modified_gmt`, `post_content_filtered`, `post_parent`, `guid`, `menu_order`, `post_type`, `post_mime_type`, `comment_count`) VALUES
(101,1,'2024-09-01 10:00:00','2024-09-01 08:00:00','<p>Preserved HTML</p>','Wing ribs','','publish','closed','closed','','wing-ribs','','','2024-09-02 10:00:00','2024-09-02 08:00:00','',0,'https://www.clubaviazionepopolare.org/articoli-tecnici/wing-ribs/',0,'articoli-tecnici','',0),
(102,1,'2024-09-01 10:00:00','2024-09-01 08:00:00','','Sport Aviation list','','publish','closed','closed','','elenco-articoli-tecnici-tradotti-da-sport-aviation-1','','','2024-09-01 10:00:00','2024-09-01 08:00:00','',0,'https://www.clubaviazionepopolare.org/sport-aviation/',0,'page','',0),
(201,1,'2024-09-01 10:00:00','2024-09-01 08:00:00','','wing-ribs','','inherit','closed','closed','','wing-ribs','','','2024-09-01 10:00:00','2024-09-01 08:00:00','',101,'https://www.clubaviazionepopolare.org/wp-content/uploads/2024/09/wing-ribs.pdf',0,'attachment','application/pdf',0);
INSERT INTO `cap_postmeta` (`meta_id`, `post_id`, `meta_key`, `meta_value`) VALUES
(1,201,'_wp_attached_file','2024/09/wing-ribs.pdf');
INSERT INTO `cap_terms` (`term_id`, `name`, `slug`, `term_group`) VALUES
(5,'Costruzione','costruzione',0);
INSERT INTO `cap_term_taxonomy` (`term_taxonomy_id`, `term_id`, `taxonomy`, `description`, `parent`, `count`) VALUES
(7,5,'argomento','',0,1);
INSERT INTO `cap_term_relationships` (`object_id`, `term_taxonomy_id`, `term_order`) VALUES
(101,7,0);
INSERT INTO `cap_options` (`option_id`, `option_name`, `option_value`, `autoload`) VALUES
(1,'default_role','soci_cap','yes');
INSERT INTO `cap_usermeta` (`umeta_id`, `user_id`, `meta_key`, `meta_value`) VALUES
(1,10,'cap_capabilities','a:1:{s:8:\"soci_cap\";b:1;}'),
(2,10,'pw_user_status','approved');
"""
