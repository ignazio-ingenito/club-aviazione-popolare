import asyncio
import os
import random
import unicodedata
from pathlib import Path
import re
import yaml

import httpx
from loguru import logger


AI_FORMATTER_URL = os.getenv(
    "AI_FORMATTER_URL", "https://openrouter.ai/api/v1/chat/completions"
)
AI_FORMATTER_MODEL = os.getenv("AI_FORMATTER_MODEL", "openrouter/free")
AI_FORMATTER_TIMEOUT = int(os.getenv("AI_FORMATTER_TIMEOUT", "60"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_FORMATTER_MAX_RETRIES = int(os.getenv("AI_FORMATTER_MAX_RETRIES", "4"))
AI_FORMATTER_BACKOFF_BASE = float(os.getenv("AI_FORMATTER_BACKOFF_BASE", "1.5"))
AI_FORMATTER_BACKOFF_JITTER = float(os.getenv("AI_FORMATTER_BACKOFF_JITTER", "0.3"))
AI_MODELS_FILE = Path(os.getenv("AI_MODELS_FILE", "ai-models.yaml"))


def _load_models() -> tuple[set[str], list[str], list[dict]]:
    if not AI_MODELS_FILE.exists():
        return set(), [], []
    try:
        data = yaml.safe_load(AI_MODELS_FILE.read_text()) or {}
    except Exception:
        return set(), [], []
    bad = data.get("blacklist", [])
    white = data.get("whitelist", [])
    samples = data.get("bad_samples", [])
    bad_set = {str(m).strip() for m in bad if str(m).strip()}
    white_list = [str(m).strip() for m in white if str(m).strip()]
    cleaned_samples: list[dict] = []
    for item in list(samples or []):
        if not isinstance(item, dict):
            continue
        model = str(item.get("model", "")).strip()
        if not model:
            continue
        reason = str(item.get("reason", "")).strip() or "bad_formatting"
        cleaned_samples.append({"model": model, "reason": reason})
    return bad_set, white_list, cleaned_samples


def _save_models(
    bad_models: set[str], white_models: list[str], samples: list[dict]
) -> None:
    cleaned_samples: list[dict] = []
    for item in samples:
        if not isinstance(item, dict):
            continue
        cleaned = dict(item)
        for key in ("start_excerpt", "start_excerpt_ai", "end_excerpt", "end_excerpt_ai"):
            if key in cleaned and isinstance(cleaned[key], str):
                cleaned[key] = _normalize_text(cleaned[key])
        cleaned_samples.append(cleaned)
    payload = {
        "whitelist": white_models,
        "blacklist": sorted(bad_models),
        "bad_samples": cleaned_samples,
    }
    AI_MODELS_FILE.write_text(yaml.safe_dump(payload))


def _ordered_white_models(white_models: list[str], bad_models: set[str]) -> list[str]:
    return [m for m in white_models if m not in bad_models]


def _models_to_try(default_model: str, white_models: list[str]) -> list[str]:
    models = [default_model, *white_models]
    unique_models: list[str] = []
    for model in models:
        if model and model not in unique_models:
            unique_models.append(model)
    return unique_models


def _is_bad_response(html: str) -> bool:
    if not html:
        return True
    text = html.strip()
    if text.startswith("```") or text.endswith("```"):
        return True
    if "```" in text:
        return True
    # If the response has almost no structure and is long, treat as bad.
    has_block = bool(re.search(r"<(p|h2|h3|ul|ol|li)(\\s|>)", text, flags=re.IGNORECASE))
    p_count = len(re.findall(r"<p(\\s|>)", text, flags=re.IGNORECASE))
    if not has_block and len(text) > 800:
        return True
    if p_count <= 1 and len(text) > 1200:
        return True
    if "\n" not in text and len(text) > 1500:
        return True
    return False


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    # Drop control/unprintable chars, normalize whitespace.
    cleaned = "".join(ch for ch in text if ch.isprintable())
    cleaned = unicodedata.normalize("NFKD", cleaned)
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    # Add spaces after punctuation if missing
    cleaned = re.sub(r'([.!?;:,])([^\s])', r'\1 \2', cleaned)
    cleaned = "".join(" " if ch.isspace() else ch for ch in cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


def _content_similarity(original: str, formatted: str, min_overlap: int = 5) -> bool:
    """Check if there's substantial content overlap between texts."""
    orig_words = original.split()
    formatted_words = formatted.split()
    
    if len(orig_words) < min_overlap or len(formatted_words) < min_overlap:
        return original.strip() == formatted.strip()
    
    # Find longest common word sequence
    max_overlap = 0
    for i in range(len(orig_words) - min_overlap + 1):
        for j in range(len(formatted_words) - min_overlap + 1):
            overlap = 0
            while (i + overlap < len(orig_words) and 
                   j + overlap < len(formatted_words) and 
                   orig_words[i + overlap] == formatted_words[j + overlap]):
                overlap += 1
            max_overlap = max(max_overlap, overlap)
    
    return max_overlap >= min_overlap


def _starts_ends_match(
    original_html: str, formatted_html: str
) -> tuple[bool, bool, str, str, str, str]:
    original_text = _strip_tags(original_html)
    formatted_text = _strip_tags(formatted_html)
    if not original_text or not formatted_text:
        return False, False, "", "", "", ""

    # Normalize both texts for comparison
    original_norm = _normalize_text(original_text)
    formatted_norm = _normalize_text(formatted_text)

    if not original_norm or not formatted_norm:
        return False, False, "", "", "", ""

    head = original_norm[:200]
    tail = original_norm[-200:]
    formatted_head = formatted_norm[:200]
    formatted_tail = formatted_norm[-200:]

    # Check if head content is substantially present
    head_ok = _content_similarity(head, formatted_norm, min_overlap=3)
    
    # For tail, check substantial content overlap
    tail_ok = _content_similarity(tail, formatted_norm, min_overlap=3)

    return (
        head_ok,
        tail_ok,
        head,
        tail,
        formatted_head,
        formatted_tail,
    )


def _quality_reasons(original_html: str, formatted_html: str) -> list[dict]:
    reasons: list[dict] = []
    if _is_bad_response(formatted_html):
        reasons.append({"reason": "bad_formatting"})
    _, end_ok, head, tail, formatted_head, formatted_tail = _starts_ends_match(
        original_html, formatted_html
    )
    if not end_ok:
        reasons.append(
            {
                "reason": "end_missing",
                "end_excerpt": tail,
                "end_excerpt_ai": formatted_tail,
            }
        )
    return reasons


async def format_content(html: str, title: str) -> tuple[str, str | None]:
    """Format imported HTML using OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set.")
    prompt = f"""
You are editing an Italian aviation club newsletter/article imported from WordPress.

Rules:
- Preserve the original text.
- Do not add new information.
- Keep all links, images, file links, and existing href/src URLs.
- Remove empty paragraphs and redundant line breaks and repeated spaces.
- Improve readability by splitting long blocks into paragraphs and logical sections.
- Fix grammar, punctuation, capitalization, spacing, and minor typos only.
- Do not rewrite the author's voice or make the text more promotional.
- Use simple HTML tags such as p, h2, h3, ul, ol, li, strong, em, a, img.
- Remove any markdown syntax or backticks, code fences, or non-HTML formatting.
- Return only valid HTML fragment content. Do not wrap it in markdown fences.

Title: {title}

HTML:
{html}
""".strip()

    last_exc: httpx.HTTPError | None = None
    bad_models, white_models, bad_samples = _load_models()
    white_retry_models = _ordered_white_models(white_models, bad_models)
    models_to_try = _models_to_try(AI_FORMATTER_MODEL, white_retry_models)
    for attempt, model_to_use in enumerate(models_to_try, start=1):
        try:
            async with httpx.AsyncClient(timeout=AI_FORMATTER_TIMEOUT) as client:
                if attempt > 1 and model_to_use in white_retry_models:
                    logger.info(
                        f"AI formatter retry will use whitelisted model: {model_to_use}"
                    )
                response = await client.post(
                    AI_FORMATTER_URL,
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                    json={
                        "model": model_to_use,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                    },
                )
                response.raise_for_status()
                data = response.json()
                used_model = data.get("model")
                if used_model:
                    logger.info(f"AI formatter response model: {used_model}")
                    if used_model in bad_models:
                        logger.warning(
                            f"AI formatter model {used_model} is blacklisted. Retrying."
                        )
                        if attempt < len(models_to_try):
                            continue
                        raise ValueError(
                            f"AI formatter returned blacklisted model {used_model}."
                        )
                formatted = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if not formatted:
                    raise ValueError("AI content formatter returned an empty response.")
                reasons = _quality_reasons(html, formatted)
                if reasons:
                    logger.warning(
                        "AI formatter response flagged as low quality "
                        f"(model: {used_model or 'unknown'}, "
                        f"reasons: {', '.join(r.get('reason') for r in reasons)}). "
                        "Review manually before adding the model to the blacklist."
                    )
                if not reasons and used_model and used_model not in bad_models:
                    if used_model not in white_models:
                        white_models.append(used_model)
                        _save_models(bad_models, white_models, bad_samples)
                        logger.info(
                            f"AI formatter model {used_model} added to whitelist."
                        )
                return formatted, used_model
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            status = exc.response.status_code
            if status == 429 and attempt < len(models_to_try):
                retry_after = exc.response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = float(retry_after)
                else:
                    delay = AI_FORMATTER_BACKOFF_BASE ** attempt
                delay += random.uniform(0, AI_FORMATTER_BACKOFF_JITTER)
                logger.warning(
                    f"AI formatter rate limited (429). Retrying in {delay:.2f}s "
                    f"(attempt {attempt}/{len(models_to_try)})."
                )
                await asyncio.sleep(delay)
                continue
            logger.error(f"AI content formatting failed: {exc}")
            raise
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt < len(models_to_try):
                delay = AI_FORMATTER_BACKOFF_BASE ** attempt
                delay += random.uniform(0, AI_FORMATTER_BACKOFF_JITTER)
                logger.warning(
                    f"AI formatter request failed ({exc}). Retrying in {delay:.2f}s "
                    f"(attempt {attempt}/{len(models_to_try)})."
                )
                await asyncio.sleep(delay)
                continue
            logger.error(f"AI content formatting failed: {exc}")
            raise

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("AI content formatter failed without a specific error.")
