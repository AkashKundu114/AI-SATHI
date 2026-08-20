from __future__ import annotations

import hashlib
import re

from sqlalchemy import text

from shared.db.session import get_db_session

DEFAULT_TTL_SECONDS = 20 * 60

_WHITESPACE_RE = re.compile(r"\s+")
_BENGALI_DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def normalize_query_text(text_in: str) -> str:
    normalized = text_in.strip().lower().translate(_BENGALI_DIGIT_MAP)
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return " ".join(sorted(normalized.split()))


def build_cache_key(feature: str, query_text: str, *, scope: str = "") -> str:
    normalized = normalize_query_text(query_text)
    digest = hashlib.sha256(f"{feature}:{scope}:{normalized}".encode("utf-8")).hexdigest()[:48]
    return f"{feature}:{digest}"


async def get_cached_response(cache_key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str | None:
    try:
        async with get_db_session() as db:
            row = (
                await db.execute(
                    text(
                        "SELECT response_text FROM response_cache "
                        "WHERE cache_key = :key AND created_at > NOW() - make_interval(secs => :ttl)"
                    ),
                    {"key": cache_key, "ttl": ttl_seconds},
                )
            ).fetchone()
    except Exception:
        return None
    return row[0] if row else None


async def set_cached_response(cache_key: str, response_text: str) -> None:
    try:
        async with get_db_session() as db:
            await db.execute(
                text(),
                {"key": cache_key, "text": response_text},
            )
            await db.commit()
    except Exception:
        pass
