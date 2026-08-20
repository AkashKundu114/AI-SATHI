from __future__ import annotations

import hashlib
import re

from sqlalchemy import text

from shared.db.session import get_db_session

DEFAULT_DEDUP_TTL_SECONDS = 10 * 60
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text_in: str) -> str:
    return _WHITESPACE_RE.sub(" ", text_in.strip().lower())


def build_poster_dedup_key(user_id: str, product_name: str, ad_caption: str) -> str:
    normalized = f"{user_id}:{_normalize(product_name)}:{_normalize(ad_caption)}"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:48]
    return f"poster:{digest}"


async def get_cached_poster(dedup_key: str, ttl_seconds: int = DEFAULT_DEDUP_TTL_SECONDS) -> dict | None:
    try:
        async with get_db_session() as db:
            row = (
                await db.execute(
                    text(
                        "SELECT poster_s3_key, poster_tier FROM poster_dedup_cache "
                        "WHERE dedup_key = :key AND created_at > NOW() - make_interval(secs => :ttl)"
                    ),
                    {"key": dedup_key, "ttl": ttl_seconds},
                )
            ).fetchone()
    except Exception:
        return None
    if row is None:
        return None
    return {"poster_s3_key": row[0], "poster_tier": row[1]}


async def record_poster(dedup_key: str, poster_s3_key: str, poster_tier: str) -> None:
    try:
        async with get_db_session() as db:
            await db.execute(
                text(),
                {"key": dedup_key, "s3_key": poster_s3_key, "tier": poster_tier},
            )
            await db.commit()
    except Exception:
        pass
