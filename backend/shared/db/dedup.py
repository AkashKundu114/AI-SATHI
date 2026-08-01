from __future__ import annotations

import time
from datetime import date

from sqlalchemy import text
from shared.db.session import get_db_session


async def mark_seen_or_skip(message_id: str) -> bool:
    async with get_db_session() as db:
        try:
            await db.execute(
                text("INSERT INTO webhook_dedup (message_id) VALUES (:mid)"),
                {"mid": message_id},
            )
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False


async def check_and_increment_rate_limit(phone_number: str, max_per_hour: int) -> bool:
    hour_bucket = int(time.time() // 3600)
    async with get_db_session() as db:
        row = (
            await db.execute(
                text(
                    
                ),
                {"phone": phone_number, "bucket": hour_bucket},
            )
        ).fetchone()
        await db.commit()
    return row[0] <= max_per_hour


async def check_and_increment_daily_feature_cap(user_id: str, feature: str, max_per_day: int) -> bool:
    day_bucket = date.today().isoformat()
    async with get_db_session() as db:
        row = (
            await db.execute(
                text(
                    
                ),
                {"uid": user_id, "feature": feature, "day": day_bucket},
            )
        ).fetchone()
        await db.commit()
    return row[0] <= max_per_day
