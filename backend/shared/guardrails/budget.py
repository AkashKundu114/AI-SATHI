from __future__ import annotations

import time
from sqlalchemy import text
from shared.db.session import get_db_session
from shared.config.feature_caps import (
    BUDGET_DEGRADE_THRESHOLD,
    BUDGET_HARD_STOP_THRESHOLD,
    MIN_SECONDS_BETWEEN_REQUESTS,
)

_status_cache: dict[str, dict] = {}
_STATUS_CACHE_TTL_SECONDS = 15.0

_last_request_at: dict[str, float] = {}


async def charge_credits(vendor: str, credits: float, call_type: str, user_id: str | None = None) -> dict:
    async with get_db_session() as db:
        row = (
            await db.execute(
                text(
                    """
                    UPDATE credit_budget
                    SET used = used + :credits,
                        degraded_mode = (used + :credits) >= (total_budget * :degrade_threshold),
                        hard_stopped = (used + :credits) >= (total_budget * :hard_stop_threshold),
                        updated_at = NOW()
                    WHERE vendor = :vendor
                    RETURNING used, total_budget, degraded_mode, hard_stopped
                    """
                ),
                {
                    "vendor": vendor,
                    "credits": credits,
                    "degrade_threshold": BUDGET_DEGRADE_THRESHOLD,
                    "hard_stop_threshold": BUDGET_HARD_STOP_THRESHOLD,
                },
            )
        ).fetchone()
        await db.execute(
            text(
                "INSERT INTO credit_usage_log (vendor, call_type, credits_charged, user_id) "
                "VALUES (:vendor, :call_type, :credits, :user_id)"
            ),
            {"vendor": vendor, "call_type": call_type, "credits": credits, "user_id": user_id},
        )
        await db.commit()

    status = {
        "used": float(row[0]), "total_budget": float(row[1]),
        "degraded_mode": bool(row[2]), "hard_stopped": bool(row[3]),
    }
    _status_cache[vendor] = {"status": status, "cached_at": time.monotonic()}
    return status


async def get_budget_status(vendor: str) -> dict:
    cached = _status_cache.get(vendor)
    if cached and (time.monotonic() - cached["cached_at"]) < _STATUS_CACHE_TTL_SECONDS:
        return cached["status"]

    try:
        async with get_db_session() as db:
            row = (
                await db.execute(
                    text(
                        "SELECT used, total_budget, degraded_mode, hard_stopped "
                        "FROM credit_budget WHERE vendor = :vendor"
                    ),
                    {"vendor": vendor},
                )
            ).fetchone()
    except Exception:
        return {"used": 0.0, "total_budget": 1.0, "degraded_mode": False, "hard_stopped": False}

    if row is None:
        return {"used": 0.0, "total_budget": 1.0, "degraded_mode": False, "hard_stopped": False}

    status = {
        "used": float(row[0]), "total_budget": float(row[1]),
        "degraded_mode": bool(row[2]), "hard_stopped": bool(row[3]),
    }
    _status_cache[vendor] = {"status": status, "cached_at": time.monotonic()}
    return status


async def is_degraded(vendor: str) -> bool:
    status = await get_budget_status(vendor)
    return status["degraded_mode"]


async def is_hard_stopped(vendor: str) -> bool:
    status = await get_budget_status(vendor)
    return status["hard_stopped"]


def check_min_request_gap(user_id: str, min_seconds: float = MIN_SECONDS_BETWEEN_REQUESTS) -> bool:
    now = time.monotonic()
    last = _last_request_at.get(user_id)
    _last_request_at[user_id] = now
    if last is None:
        return True
    return (now - last) >= min_seconds


def reset_for_tests() -> None:
    _status_cache.clear()
    _last_request_at.clear()
