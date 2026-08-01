from __future__ import annotations

import logging
from datetime import datetime, timezone
from sqlalchemy import text
from shared.db.session import get_db_session

logger = logging.getLogger("metrics_collector")


async def collect_system_metrics() -> dict:
    
    now = datetime.now(timezone.utc)
    month_bucket = now.strftime("%Y-%m")

    metrics: dict = {
        "collected_at": now.isoformat(),
        "month_bucket": month_bucket,
        "users": {
            "total": 0,
            "onboarded": 0,
            "new_24h": 0,
            "tiers": {"free": 0, "basic": 0, "pro": 0, "unlimited": 0},
        },
        "product": {
            "ledger_entries_total": 0,
            "total_income_inr": 0.0,
            "total_expense_inr": 0.0,
            "catalog_creations_total": 0,
            "seller_profiles_total": 0,
        },
        "api_usage": {
            "sarvam_chat": 0,
            "sarvam_vision": 0,
            "sarvam_stt": 0,
            "sarvam_translate": 0,
            "flux": 0,
            "total_calls": 0,
            "estimated_cost_inr": 0.0,
            "estimated_cost_usd": 0.0,
        },
        "security": {
            "rate_limited_numbers_24h": 0,
            "total_webhook_dedup_records": 0,
        },
    }

    async with get_db_session() as db:
        try:
            user_count = (await db.execute(text("SELECT COUNT(*) FROM users"))).scalar() or 0
            onboarded_count = (
                await db.execute(
                    text("SELECT COUNT(*) FROM users WHERE consent_given = TRUE")
                )
            ).scalar() or 0
            new_24h = (
                await db.execute(
                    text("SELECT COUNT(*) FROM users WHERE onboarded_at >= NOW() - INTERVAL '24 hours'")
                )
            ).scalar() or 0

            metrics["users"]["total"] = user_count
            metrics["users"]["onboarded"] = onboarded_count
            metrics["users"]["new_24h"] = new_24h

            tier_rows = (
                await db.execute(
                    text("SELECT COALESCE(plan_tier, 'free') as tier, COUNT(*) FROM user_plans GROUP BY plan_tier")
                )
            ).fetchall()
            for tier_name, count in tier_rows:
                if tier_name in metrics["users"]["tiers"]:
                    metrics["users"]["tiers"][tier_name] = count

            configured_plans = sum(metrics["users"]["tiers"].values())
            metrics["users"]["tiers"]["free"] += max(0, user_count - configured_plans)

            ledger_count = (await db.execute(text("SELECT COUNT(*) FROM ledger_entries"))).scalar() or 0
            income_sum = (
                await db.execute(
                    text("SELECT COALESCE(SUM(amount_inr), 0) FROM ledger_entries WHERE entry_type = 'income'")
                )
            ).scalar() or 0.0
            expense_sum = (
                await db.execute(
                    text("SELECT COALESCE(SUM(amount_inr), 0) FROM ledger_entries WHERE entry_type = 'expense'")
                )
            ).scalar() or 0.0

            catalog_count = (await db.execute(text("SELECT COUNT(*) FROM catalog_creations"))).scalar() or 0
            seller_count = (await db.execute(text("SELECT COUNT(*) FROM seller_profiles"))).scalar() or 0

            metrics["product"]["ledger_entries_total"] = ledger_count
            metrics["product"]["total_income_inr"] = float(income_sum)
            metrics["product"]["total_expense_inr"] = float(expense_sum)
            metrics["product"]["catalog_creations_total"] = catalog_count
            metrics["product"]["seller_profiles_total"] = seller_count

            usage_rows = (
                await db.execute(
                    text("SELECT provider, SUM(call_count) FROM api_usage_monthly WHERE month_bucket = :m GROUP BY provider"),
                    {"m": month_bucket},
                )
            ).fetchall()

            total_calls = 0
            for provider, count in usage_rows:
                if provider in metrics["api_usage"]:
                    metrics["api_usage"][provider] = count
                    total_calls += count

            metrics["api_usage"]["total_calls"] = total_calls

            sarvam_cost_inr = (
                (metrics["api_usage"]["sarvam_chat"] * 0.012)
                + (metrics["api_usage"]["sarvam_vision"] * 0.50)
                + (metrics["api_usage"]["sarvam_stt"] * 0.25)
                + (metrics["api_usage"]["sarvam_translate"] * 0.01)
            )
            flux_cost_usd = metrics["api_usage"]["flux"] * 0.04
            flux_cost_inr = flux_cost_usd * 83.5

            metrics["api_usage"]["estimated_cost_inr"] = round(sarvam_cost_inr + flux_cost_inr, 2)
            metrics["api_usage"]["estimated_cost_usd"] = round(
                (sarvam_cost_inr / 83.5) + flux_cost_usd, 2
            )

            active_rate_limits = (
                await db.execute(
                    text("SELECT COUNT(DISTINCT phone_number) FROM rate_limit_counters WHERE hour_bucket >= (EXTRACT(EPOCH FROM NOW()) / 3600 - 24)::BIGINT")
                )
            ).scalar() or 0
            dedup_count = (await db.execute(text("SELECT COUNT(*) FROM webhook_dedup"))).scalar() or 0

            metrics["security"]["rate_limited_numbers_24h"] = active_rate_limits
            metrics["security"]["total_webhook_dedup_records"] = dedup_count

        except Exception:
            logger.exception("Failed to collect complete system metrics")

    return metrics
