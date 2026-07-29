from __future__ import annotations

import logging
from datetime import datetime, timezone
from sqlalchemy import text

from shared.config.usage_limits import TIER_LIMITS
from shared.db.session import get_db_session

logger = logging.getLogger("usage_tracker")


class UsageLimitExceededError(Exception):
    def __init__(self, provider: str, limit: int, current: int):
        self.provider = provider
        self.limit = limit
        self.current = current
        super().__init__(f"Monthly usage limit for {provider} exceeded ({current}/{limit})")


async def get_user_plan_tier(user_id: str) -> str:
    """Fetch user's current active plan tier from database."""
    if not user_id:
        return "free"
    
    async with get_db_session() as db:
        try:
            row = (
                await db.execute(
                    text(
                        """
                        SELECT plan_tier, plan_expires
                        FROM user_plans
                        WHERE user_id = :uid
                        """
                    ),
                    {"uid": user_id},
                )
            ).fetchone()

            if not row:
                return "free"
            
            plan_tier, plan_expires = row[0], row[1]
            if plan_expires and plan_expires < datetime.now(timezone.utc):
                logger.info("User %s plan expired at %s, falling back to free tier", user_id, plan_expires)
                return "free"
            
            return plan_tier or "free"
        except Exception:
            logger.exception("Failed to fetch user plan for %s, falling back to free tier", user_id)
            return "free"


async def check_and_increment_api_usage(
    user_id: str | None, provider: str
) -> tuple[bool, int, int]:
    """
    Checks if user is under their monthly API limit for `provider` and increments count.
    Returns: (allowed: bool, current_usage: int, max_limit: int)
    """
    if not user_id:
        return True, 1, 999999

    plan_tier = await get_user_plan_tier(user_id)
    limits = TIER_LIMITS.get(plan_tier, TIER_LIMITS["free"])
    max_limit = limits.get(provider, 999999)

    month_bucket = datetime.now(timezone.utc).strftime("%Y-%m")

    async with get_db_session() as db:
        try:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO api_usage_monthly (user_id, provider, month_bucket, call_count)
                        VALUES (:uid, :provider, :month, 1)
                        ON CONFLICT (user_id, provider, month_bucket)
                        DO UPDATE SET call_count = api_usage_monthly.call_count + 1
                        RETURNING call_count
                        """
                    ),
                    {"uid": user_id, "provider": provider, "month": month_bucket},
                )
            ).fetchone()
            await db.commit()
            
            current_usage = row[0]
            if current_usage > max_limit:
                logger.warning(
                    "User %s exceeded %s monthly limit (%d/%d) on tier %s",
                    user_id, provider, current_usage, max_limit, plan_tier,
                )
                return False, current_usage, max_limit

            return True, current_usage, max_limit

        except Exception:
            logger.exception("Failed to check/increment usage for user %s provider %s", user_id, provider)
            return True, 1, max_limit
