"""Read-only inventory CLI for WordPress-to-Directus migration artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Callable
import yaml

from .directus import DirectusInventoryClient, DirectusInventoryConfig
from .gallery import WordPressGalleryDiscoveryClient
from .routes import RouteInventoryClient, RouteInventoryConfig
from .reconciliation import (
    historical_mappings_from_parser_yaml,
    reconcile_manifest_files,
)
from .reconciliation_writer import ReconciliationWriteResult, write_reconciliation_report_json
from .wordpress import WordPressInventoryClient, WordPressInventoryConfig
from .writer import ManifestWriteResult, write_manifest_jsonl
from .wxr import WordPressWXRMediaInventoryClient


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler: Callable[[argparse.Namespace], object] = args.handler
    result = handler(args)
    artifact_path = getattr(result, "manifest_path", None) or getattr(
        result, "report_path", None
    )
    print(
        json.dumps(
            {
                "manifest": str(artifact_path) if artifact_path is not None else None,
                "checksum": str(result.checksum_path),
                "sha256": result.sha256,
                "bytes": result.byte_count,
            },
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m inventory",
        description="Generate read-only migration inventory manifests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    routes = subparsers.add_parser(
        "routes",
        help="Inventory Next.js App Router routes from the repository filesystem.",
    )
    _add_common_output_args(routes, default_filename="routes.jsonl")
    routes.add_argument("--app-dir", default="app", help="Path to the Next.js app directory.")
    routes.add_argument(
        "--base-url",
        default="https://cap.skunklabs.uk",
        help="Frontend base URL recorded in the manifest metadata.",
    )
    routes.set_defaults(handler=_run_routes)

    wordpress = subparsers.add_parser(
        "wordpress-core",
        help="Inventory WordPress REST types, categories, posts, and media.",
    )
    _add_common_output_args(wordpress, default_filename="wordpress.jsonl")
    wordpress.add_argument(
        "--base-url",
        default="https://www.clubaviazionepopolare.org",
        help="WordPress base URL.",
    )
    wordpress.add_argument("--per-page", type=int, default=100)
    wordpress.set_defaults(handler=_run_wordpress_core)

    wxr_media = subparsers.add_parser(
        "wordpress-wxr-media",
        help="Inventory WordPress attachment records from a local WXR admin export.",
    )
    _add_common_output_args(wxr_media, default_filename="wordpress-wxr-media.jsonl")
    wxr_media.add_argument(
        "--input",
        required=True,
        help="Path to the local WordPress WXR XML export.",
    )
    wxr_media.set_defaults(handler=_run_wordpress_wxr_media)

    gallery = subparsers.add_parser(
        "gallery",
        help="Inventory WordPress galleries through REST discovery or public HTML fallback.",
    )
    _add_common_output_args(gallery, default_filename="gallery.jsonl")
    gallery.add_argument(
        "--base-url",
        default="https://www.clubaviazionepopolare.org",
        help="WordPress base URL.",
    )
    gallery.add_argument("--per-page", type=int, default=100)
    gallery.set_defaults(handler=_run_gallery)

    directus = subparsers.add_parser(
        "directus-core",
        help="Inventory Directus runtime, schema metadata, feeds, categories, files, and folders.",
    )
    _add_common_output_args(directus, default_filename="directus-public-view.jsonl")
    directus.add_argument(
        "--base-url",
        default="https://cap-cms.skunklabs.uk",
        help="Directus base URL.",
    )
    directus.add_argument("--limit", type=int, default=100)
    directus.set_defaults(handler=_run_directus_core)

    reconcile = subparsers.add_parser(
        "reconcile",
        help="Classify source inventory against target inventory without writing to WordPress or Directus.",
    )
    _add_common_output_args(reconcile, default_filename="reconciliation.json")
    reconcile.add_argument(
        "--source-manifest",
        "--source",
        dest="source_manifest",
        required=True,
        help="Path to the source inventory JSONL file.",
    )
    reconcile.add_argument(
        "--target-manifest",
        "--target",
        dest="target_manifest",
        required=True,
        help="Path to the target inventory JSONL file.",
    )
    reconcile.add_argument(
        "--legacy-map",
        help="Optional parser.yaml evidence file for historical corroboration.",
    )
    reconcile.set_defaults(handler=_run_reconcile)

    return parser


def _add_common_output_args(
    parser: argparse.ArgumentParser, *, default_filename: str
) -> None:
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Controlled run directory outside Git where artifacts are written.",
    )
    parser.add_argument(
        "--filename",
        default=default_filename,
        help="JSONL filename to create inside --output-dir.",
    )
    parser.add_argument(
        "--environment",
        default="production",
        help="Environment label recorded in the manifest.",
    )


def _run_routes(args: argparse.Namespace) -> ManifestWriteResult:
    snapshot = RouteInventoryClient(
        config=RouteInventoryConfig(app_dir=args.app_dir)
    ).inventory()
    manifest = snapshot.to_manifest(
        environment=args.environment,
        base_url=args.base_url,
        observed_at=_now_utc(),
    )
    return _write(args, manifest)


def _run_wordpress_core(args: argparse.Namespace) -> ManifestWriteResult:
    with WordPressInventoryClient(
        config=WordPressInventoryConfig(
            base_url=args.base_url,
            per_page=args.per_page,
        )
    ) as client:
        snapshot = client.inventory_core()
    manifest = snapshot.to_manifest(
        environment=args.environment,
        observed_at=_now_utc(),
    )
    return _write(args, manifest)


def _run_wordpress_wxr_media(args: argparse.Namespace) -> ManifestWriteResult:
    snapshot = WordPressWXRMediaInventoryClient(export_path=args.input).inventory()
    manifest = snapshot.to_manifest(
        environment=args.environment,
        observed_at=_now_utc(),
    )
    return _write(args, manifest)


def _run_gallery(args: argparse.Namespace) -> ManifestWriteResult:
    with WordPressGalleryDiscoveryClient(
        config=WordPressInventoryConfig(
            base_url=args.base_url,
            per_page=args.per_page,
        )
    ) as client:
        discovery = client.discover()
    manifest = discovery.to_manifest(
        base_url=args.base_url,
        environment=args.environment,
        observed_at=_now_utc(),
    )
    return _write(args, manifest)


def _run_directus_core(args: argparse.Namespace) -> ManifestWriteResult:
    with DirectusInventoryClient(
        config=DirectusInventoryConfig(
            base_url=args.base_url,
            limit=args.limit,
        )
    ) as client:
        snapshot = client.inventory_core()
    manifest = snapshot.to_manifest(
        environment=args.environment,
        observed_at=_now_utc(),
    )
    return _write(args, manifest)


def _run_reconcile(args: argparse.Namespace) -> ReconciliationWriteResult:
    historical_mappings = None
    if args.legacy_map:
        with open(args.legacy_map, "r", encoding="utf-8") as handle:
            legacy_map = yaml.safe_load(handle) or {}
        if not isinstance(legacy_map, dict):
            raise ValueError("--legacy-map must contain a mapping at the top level.")
        historical_mappings = historical_mappings_from_parser_yaml(legacy_map)

    report = reconcile_manifest_files(
        args.source_manifest,
        args.target_manifest,
        historical_mappings=historical_mappings,
    )
    return _write_reconciliation(args, report)


def _write(args: argparse.Namespace, manifest) -> ManifestWriteResult:
    return write_manifest_jsonl(
        manifest,
        output_dir=Path(args.output_dir),
        filename=args.filename,
        repository_root=_repository_root(),
    )


def _write_reconciliation(
    args: argparse.Namespace, report
) -> ReconciliationWriteResult:
    return write_reconciliation_report_json(
        report,
        output_dir=Path(args.output_dir),
        filename=args.filename,
        repository_root=_repository_root(),
    )


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


if __name__ == "__main__":
    raise SystemExit(main())
