"""Fail-closed selection of a WordPress gallery discovery source."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .errors import ResponseContractError
from .gallery_models import GalleryDiscoveryPlan, GalleryRestCandidate
from .records import ManifestRecord

_EXACT_IDENTIFIERS = {
    "dt_gallery",
    "dt_galleries",
    "gallery",
    "galleries",
}


def _identifier(value: object) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _candidate_score(record: ManifestRecord) -> tuple[int, tuple[str, ...]]:
    type_key = _identifier(record.object_id)
    rest_base = _identifier(record.payload.get("rest_base"))
    slug = _identifier(record.payload.get("slug"))
    name = _identifier(record.payload.get("name"))

    score = 0
    evidence: list[str] = []

    if type_key in _EXACT_IDENTIFIERS or type_key.startswith("dt_gallery"):
        score += 100
        evidence.append(f"type_key={record.object_id}")
    if rest_base in _EXACT_IDENTIFIERS or rest_base.startswith("dt_gallery"):
        score += 90
        evidence.append(f"rest_base={record.payload.get('rest_base')}")
    if slug in _EXACT_IDENTIFIERS or slug.startswith("dt_gallery"):
        score += 80
        evidence.append(f"slug={record.payload.get('slug')}")
    if name in _EXACT_IDENTIFIERS:
        score += 60
        evidence.append(f"name={record.payload.get('name')}")
    elif "gallery" in name:
        score += 20
        evidence.append(f"name_contains_gallery={record.payload.get('name')}")

    return score, tuple(evidence)


def discover_gallery_rest_candidate(
    post_type_records: Sequence[ManifestRecord],
) -> GalleryRestCandidate | None:
    """Return one strong gallery REST candidate or fail on ambiguity."""

    ranked: list[tuple[int, ManifestRecord, tuple[str, ...]]] = []
    for record in post_type_records:
        if record.system != "wordpress" or record.object_type != "post_type":
            continue
        score, evidence = _candidate_score(record)
        if score >= 60:
            ranked.append((score, record, evidence))

    if not ranked:
        return None

    ranked.sort(key=lambda item: (-item[0], item[1].identity))
    top_score = ranked[0][0]
    top = [item for item in ranked if item[0] == top_score]
    if len(top) != 1:
        identities = ", ".join(item[1].identity for item in top)
        raise ResponseContractError(
            f"Gallery REST discovery is ambiguous between: {identities}."
        )

    _, record, evidence = top[0]
    rest_base = record.payload.get("rest_base")
    namespace = record.payload.get("rest_namespace") or "wp/v2"
    if not isinstance(rest_base, str) or not rest_base.strip():
        return None
    if not isinstance(namespace, str) or not namespace.strip():
        return None

    return GalleryRestCandidate(
        type_key=record.object_id,
        rest_base=rest_base.strip().strip("/"),
        rest_namespace=namespace.strip().strip("/"),
        evidence=evidence,
    )


def select_gallery_discovery_plan(
    post_type_records: Sequence[ManifestRecord],
) -> GalleryDiscoveryPlan:
    """Prefer an exposed wp/v2 type and otherwise require HTML fallback."""

    candidate = discover_gallery_rest_candidate(post_type_records)
    if candidate is None:
        return GalleryDiscoveryPlan(
            mode="html",
            reason="No unambiguous REST-enabled gallery post type was discovered.",
        )

    if candidate.rest_namespace != "wp/v2":
        return GalleryDiscoveryPlan(
            mode="html",
            reason=(
                "The gallery type uses a custom REST namespace; the public HTML "
                "fallback remains the supported read-only source."
            ),
            rest_candidate=candidate,
        )

    if not candidate.rest_base or ".." in candidate.rest_base:
        raise ResponseContractError("The gallery REST base is not a safe relative path.")

    return GalleryDiscoveryPlan(
        mode="rest",
        reason="A unique gallery post type is exposed in the wp/v2 namespace.",
        rest_candidate=candidate,
    )
