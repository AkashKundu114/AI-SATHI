from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_DEDUP_RETENTION_DAYS = 7
DEFAULT_RATE_LIMIT_RETENTION_HOURS = 168


async def main_async(dedup_days: int, rate_limit_hours: int, dry_run: bool) -> None:
    from sqlalchemy import text

    from shared.db.session import get_db_session

    async with get_db_session() as db:
        dedup_count = (
            await db.execute(
                text("SELECT COUNT(*) FROM webhook_dedup WHERE created_at < NOW() - (:days || ' days')::interval"),
                {"days": dedup_days},
            )
        ).scalar_one()

        rate_limit_count = (
            await db.execute(
                text(
                    "SELECT COUNT(*) FROM rate_limit_counters "
                    "WHERE hour_bucket < (EXTRACT(EPOCH FROM NOW()) / 3600 - :hours)::BIGINT"
                ),
                {"hours": rate_limit_hours},
            )
        ).scalar_one()

        print(f"webhook_dedup rows older than {dedup_days}d: {dedup_count}")
        print(f"rate_limit_counters rows older than {rate_limit_hours}h: {rate_limit_count}")

        if dry_run:
            print("\n[dry-run] no rows deleted.")
            return

        if dedup_count:
            await db.execute(
                text("DELETE FROM webhook_dedup WHERE created_at < NOW() - (:days || ' days')::interval"),
                {"days": dedup_days},
            )
        if rate_limit_count:
            await db.execute(
                text(
                    "DELETE FROM rate_limit_counters "
                    "WHERE hour_bucket < (EXTRACT(EPOCH FROM NOW()) / 3600 - :hours)::BIGINT"
                ),
                {"hours": rate_limit_hours},
            )
        await db.commit()

    print(f"\n✅ Deleted {dedup_count} webhook_dedup row(s) and {rate_limit_count} rate_limit_counters row(s).")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dedup-days",
        type=int,
        default=DEFAULT_DEDUP_RETENTION_DAYS,
        help=f"Delete webhook_dedup rows older than N days (default: {DEFAULT_DEDUP_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--rate-limit-hours",
        type=int,
        default=DEFAULT_RATE_LIMIT_RETENTION_HOURS,
        help=f"Delete rate_limit_counters rows older than N hours (default: {DEFAULT_RATE_LIMIT_RETENTION_HOURS})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report row counts only; delete nothing")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    asyncio.run(main_async(args.dedup_days, args.rate_limit_hours, args.dry_run))


if __name__ == "__main__":
    main()
