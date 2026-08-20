import asyncio
from datetime import datetime, timezone

from sqlalchemy import text

from shared.db.session import get_db_session


async def generate_usage_report() -> None:
    month_bucket = datetime.now(timezone.utc).strftime("%Y-%m")

    async with get_db_session() as db:
        rows = (
            await db.execute(
                text(),
                {"month": month_bucket},
            )
        ).fetchall()

        summary = (
            await db.execute(
                text(),
                {"month": month_bucket},
            )
        ).fetchall()

    print("==================================================")
    print(f"📊 AI-SATHI API Usage Report for {month_bucket}")
    print("==================================================")

    if not summary:
        print("No API usage recorded yet for this month.")
        return

    print("\n--- Provider Breakdown ---")
    for provider, total_calls in summary:
        print(f"  • {provider:<18}: {total_calls} calls")

    print("\n--- Per-User Breakdown ---")
    current_user = None
    for phone, tier, provider, count in rows:
        if phone != current_user:
            current_user = phone
            print(f"\n📱 {phone} (Tier: {tier})")
        print(f"    - {provider:<16}: {count} calls")


if __name__ == "__main__":
    asyncio.run(generate_usage_report())
