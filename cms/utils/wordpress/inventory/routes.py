"""Filesystem-only Next.js route inventory for migration collision checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import InventoryManifest, InventoryScope, ManifestRecord


NEXT_ROUTE_FILES = frozenset({"page.tsx", "page.ts", "route.ts", "route.tsx"})


@dataclass(frozen=True, slots=True)
class RouteInventoryConfig:
    app_dir: Path | str = "app"

    def __post_init__(self) -> None:
        object.__setattr__(self, "app_dir", Path(self.app_dir))


@dataclass(frozen=True, slots=True)
class RouteInventorySnapshot:
    app_dir: str
    records: tuple[ManifestRecord, ...]

    def to_manifest(
        self,
        *,
        environment: str,
        base_url: str,
        observed_at: datetime,
        metadata: Mapping[str, Any] | None = None,
    ) -> InventoryManifest:
        return InventoryManifest(
            scope=InventoryScope.TARGET,
            environment=environment,
            base_url=base_url,
            observed_at=observed_at,
            records=self.records,
            issues=(),
            metadata={
                "inventory_type": "next_routes",
                "app_dir": self.app_dir,
                **dict(metadata or {}),
            },
        )


class RouteInventoryClient:
    """Inventory repository routes without network access or frontend changes."""

    def __init__(self, *, config: RouteInventoryConfig | None = None) -> None:
        self.config = config or RouteInventoryConfig()

    def inventory(self) -> RouteInventorySnapshot:
        app_dir = self.config.app_dir
        if not app_dir.exists() or not app_dir.is_dir():
            raise FileNotFoundError(f"App directory does not exist: {app_dir}")

        route_files = sorted(
            path
            for path in app_dir.rglob("*")
            if path.is_file() and path.name in NEXT_ROUTE_FILES
        )
        records = tuple(
            ManifestRecord(
                scope=InventoryScope.TARGET,
                entity_type="next_route",
                identity=f"next:route:{route.route}",
                data=route.to_record_data(),
            )
            for route in _routes_from_files(route_files, app_dir=app_dir)
        )
        return RouteInventorySnapshot(app_dir=str(app_dir), records=records)


@dataclass(frozen=True, slots=True)
class NextRoute:
    route: str
    route_type: str
    file: str
    segments: tuple[str, ...]
    dynamic_segments: tuple[str, ...]
    collision_patterns: tuple[str, ...]
    migration_collision_scope: str

    def to_record_data(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "route_type": self.route_type,
            "file": self.file,
            "segments": list(self.segments),
            "dynamic_segments": list(self.dynamic_segments),
            "collision_patterns": list(self.collision_patterns),
            "migration_collision_scope": self.migration_collision_scope,
        }


def _routes_from_files(route_files: Iterable[Path], *, app_dir: Path) -> list[NextRoute]:
    routes = []
    for path in route_files:
        relative = path.relative_to(app_dir)
        if "public" in relative.parts:
            continue
        route_type = "api" if relative.parts[0] == "api" else "page"
        route = _route_path(relative)
        segments = tuple(segment for segment in route.strip("/").split("/") if segment)
        dynamic_segments = tuple(
            segment[1:-1]
            for segment in segments
            if segment.startswith("[") and segment.endswith("]")
        )
        routes.append(
            NextRoute(
                route=route,
                route_type=route_type,
                file=relative.as_posix(),
                segments=segments,
                dynamic_segments=dynamic_segments,
                collision_patterns=_collision_patterns(route, route_type),
                migration_collision_scope=_collision_scope(route, route_type),
            )
        )
    return sorted(
        routes,
        key=lambda route: (
            1 if route.route_type == "api" else 0,
            route.route,
            route.file,
        ),
    )


def _route_path(relative: Path) -> str:
    parts = list(relative.parts[:-1])
    route_parts = [
        part
        for part in parts
        if not (part.startswith("(") and part.endswith(")"))
    ]
    if not route_parts:
        return "/"
    return "/" + "/".join(route_parts)


def _collision_patterns(route: str, route_type: str) -> tuple[str, ...]:
    if route_type == "api":
        return ()
    if route == "/":
        return ("/",)
    segments = tuple(segment for segment in route.strip("/").split("/") if segment)
    patterns = [route]
    for index, segment in enumerate(segments):
        if segment.startswith("[") and segment.endswith("]"):
            patterns.append("/" + "/".join((*segments[:index], "*", *segments[index + 1 :])))
    if any(segment.startswith("[") and segment.endswith("]") for segment in segments):
        patterns.append(
            "/"
            + "/".join(
                "*" if segment.startswith("[") and segment.endswith("]") else segment
                for segment in segments
            )
        )
    return tuple(dict.fromkeys(patterns))


def _collision_scope(route: str, route_type: str) -> str:
    if route_type == "api":
        return "api"
    if route == "/news/[id]":
        return "global_feed_slug_or_numeric_id"
    if route == "/feed/[category]/[slug]":
        return "global_feed_slug"
    if route in {"/efficiency-race", "/trofei/[slug]"}:
        return "global_feed_slug"
    if "[" in route:
        return "dynamic_public_route"
    return "reserved_static_public_route"
