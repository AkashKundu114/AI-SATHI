from __future__ import annotations

import logging

from sqlalchemy import text

from shared.db.session import get_db_session

logger = logging.getLogger("storefront")


async def get_seller_catalog_storefront(user_id: str, base_url: str = "https://kothakhata.app") -> dict:

    if not user_id:
        return {"items": [], "storefront_url": ""}

    async with get_db_session() as db:
        rows = (
            await db.execute(
                text(),
                {"uid": str(user_id)},
            )
        ).fetchall()

        user_row = (
            await db.execute(
                text("SELECT block, district FROM users WHERE id = :uid"),
                {"uid": str(user_id)},
            )
        ).fetchone()

    items = []
    for r in rows:
        items.append(
            {
                "id": str(r[0]),
                "product_type": r[1],
                "caption": r[2],
                "ad_caption": r[3],
                "price_range": f"₹{r[4]:.0f} - ₹{r[5]:.0f}" if r[4] and r[5] else f"₹{r[4]:.0f}",
                "image_url": r[6],
            }
        )

    storefront_url = f"{base_url}/s/{user_id[:8]}"
    location = f"{user_row[0]}, {user_row[1]}" if user_row and user_row[0] else "পশ্চিমবঙ্গ"

    share_message = (
        f"🛍️ *আমাদের ডিজিটাল ক্যাটালগ ও নতুন স্টক*\n"
        f"📍 স্থান: {location}\n\n"
        f"আমাদের সব সাম্প্রতিক পণ্য এক জায়গায় দেখতে এবং অর্ডার করতে নিচের লিঙ্কে ক্লিক করুন:\n"
        f"👉 {storefront_url}\n\n"
        f"ধন্যবাদ! 🙏"
    )

    return {
        "user_id": user_id,
        "total_products": len(items),
        "items": items,
        "storefront_url": storefront_url,
        "share_message": share_message,
    }
