from __future__ import annotations

import httpx


def json_response(
    request: httpx.Request,
    payload: object,
    *,
    headers: dict[str, str] | None = None,
    status_code: int = 200,
) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers=headers,
        json=payload,
        request=request,
    )


def post_record(
    post_id: int,
    *,
    slug: str | None = None,
    title: str | None = None,
) -> dict[str, object]:
    normalized_slug = slug if slug is not None else f"post-{post_id}"
    normalized_title = title if title is not None else f"Post {post_id}"
    return {
        "id": post_id,
        "type": "post",
        "slug": normalized_slug,
        "link": f"https://example.test/{normalized_slug}/",
        "date": "2025-01-01T10:00:00",
        "date_gmt": "2025-01-01T09:00:00",
        "modified": "2025-01-02T10:00:00",
        "modified_gmt": "2025-01-02T09:00:00",
        "status": "publish",
        "author": 1,
        "featured_media": 9,
        "categories": [3, 6],
        "tags": [11],
        "guid": {"rendered": f"https://example.test/?p={post_id}"},
        "title": {"rendered": normalized_title},
        "excerpt": {"rendered": "<p>Excerpt</p>"},
        "content": {
            "rendered": (
                '<p><img src="https://example.test/image.jpg" alt="Image"></p>'
                '<p><a href="https://example.test/file.pdf" rel="attachment">PDF</a></p>'
            )
        },
        "_embedded": {
            "wp:featuredmedia": [
                {
                    "id": 9,
                    "date": "2025-01-01T10:00:00",
                    "slug": "image",
                    "link": "https://example.test/image/",
                    "source_url": "https://example.test/uploads/image.jpg",
                    "alt_text": "Featured",
                    "media_type": "image",
                    "mime_type": "image/jpeg",
                    "title": {"rendered": "Image"},
                    "caption": {"rendered": ""},
                    "media_details": {"width": 1000, "height": 800},
                }
            ]
        },
    }


def category_record() -> dict[str, object]:
    return {
        "id": 6,
        "count": 3,
        "description": "",
        "link": "https://example.test/category/news/",
        "name": "News",
        "slug": "news",
        "taxonomy": "category",
        "parent": 0,
    }


def types_payload() -> dict[str, object]:
    return {
        "attachment": {
            "name": "Media",
            "slug": "attachment",
            "rest_base": "media",
            "rest_namespace": "wp/v2",
            "taxonomies": [],
            "viewable": True,
            "hierarchical": False,
        },
        "post": {
            "name": "Posts",
            "slug": "post",
            "rest_base": "posts",
            "rest_namespace": "wp/v2",
            "taxonomies": ["category", "post_tag"],
            "viewable": True,
            "hierarchical": False,
        },
    }
