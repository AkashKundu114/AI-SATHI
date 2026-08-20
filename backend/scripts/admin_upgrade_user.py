import asyncio
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from shared.db.session import get_db_session


async def upgrade_user(phone_number: str, plan_tier: str, months: int = 1) -> None:
    valid_tiers = {"free", "basic", "pro", "unlimited"}
    if plan_tier.lower() not in valid_tiers:
        print(f"Error: Invalid tier '{plan_tier}'. Valid tiers: {', '.join(valid_tiers)}")
        sys.exit(1)

    tier = plan_tier.lower()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30 * months) if tier != "free" else None

    async with get_db_session() as db:
        user_row = (
            await db.execute(
                text("SELECT id FROM users WHERE phone_number = :phone"),
                {"phone": phone_number},
            )
        ).fetchone()

        if not user_row:
            print(f"Error: User with Web number {phone_number} not found.")
            sys.exit(1)

        user_id = user_row[0]

        await db.execute(
            text(),
            {"uid": user_id, "tier": tier, "exp": expires_at},
        )
        await db.commit()

        exp_str = expires_at.strftime("%Y-%m-%d %H:%M UTC") if expires_at else "Never"
        print(f"✅ Successfully upgraded user {phone_number} ({user_id}) to tier '{tier}'. Expires: {exp_str}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/admin_upgrade_user.py <phone_number> <free|basic|pro|unlimited> [months]")
        sys.exit(1)

    phone = sys.argv[1]
    plan = sys.argv[2]
    m = int(sys.argv[3]) if len(sys.argv) > 3 else 1

    asyncio.run(upgrade_user(phone, plan, m))
