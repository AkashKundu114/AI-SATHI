from __future__ import annotations

import asyncio
import logging
import uuid

from shared.storage.blob_client import upload_bytes, download_bytes, generate_read_url
from services.orchestrator.state import ConversationState
from services.vision_service.rembg_processor import process_product_image
from services.vision_service.vision_router import analyze_product_image, generate_captions
from services.vision_service.poster_composer import generate_poster
from services.orchestrator.model_router import ModelUnavailableError
from services.market_service.aggregator import block_sales_trend, classify_trend
from shared.catalog.local_products import category_keywords, find_local_product_by_slug
from shared.db.dedup import check_and_increment_daily_feature_cap
from shared.config.feature_caps import MAX_CATALOG_CREATIONS_PER_DAY
from shared.metering.usage_tracker import UsageLimitExceededError

logger = logging.getLogger("catalog_node")

MAX_IMAGE_BYTES = 5 * 1024 * 1024

CAP_REACHED_MSG = "আজকের জন্য ছবি প্রসেসিংয়ের সীমা শেষ হয়ে গেছে। কাল আবার চেষ্টা করুন।"

_CATEGORY_KEYWORDS = category_keywords()

LIMIT_EXCEEDED_MSG = (
    "এই মাসের জন্য আপনার ফ্রি ব্যবহারের সীমা শেষ হয়ে গেছে।\n"
    "অতিরিক্ত সুবিধা পেতে প্রিমিয়াম প্ল্যানে আপগ্রেড করুন! 'আপগ্রেড' লিখে মেসেজ পাঠান।"
)


async def catalog_node(state: ConversationState) -> dict:
    user_id = state.get("user_id")
    if user_id:
        under_cap = await check_and_increment_daily_feature_cap(
            user_id, "catalog", MAX_CATALOG_CREATIONS_PER_DAY
        )
        if not under_cap:
            return {
                "outbound_messages": [{"type": "text", "body": CAP_REACHED_MSG}],
                "trace": ["catalog_node:daily_cap_reached"],
            }

    raw_key = state.get("raw_image_s3_key")  
    if not raw_key:
        return {
            "outbound_messages": [{"type": "text", "body": "ছবিটা পেলাম না। আবার পাঠান।"}],
            "trace": ["catalog_node:no_image_key"],
        }

    try:
        raw_bytes = await asyncio.to_thread(download_bytes, raw_key)
    except Exception:
        return {
            "outbound_messages": [{"type": "text", "body": "ছবিটা লোড করতে সমস্যা হয়েছে। আবার পাঠান।"}],
            "trace": ["catalog_node:s3_fetch_failed"],
        }

    if len(raw_bytes) > MAX_IMAGE_BYTES:
        return {
            "outbound_messages": [{"type": "text", "body": "ছবিটা অনেক বড়। একটু ছোট সাইজে পাঠান।"}],
            "trace": ["catalog_node:oversized_image"],
        }

    processed_bytes, quality_error = await asyncio.to_thread(process_product_image, raw_bytes)
    if quality_error:
        return {
            "outbound_messages": [{"type": "text", "body": quality_error}],
            "trace": ["catalog_node:quality_check_failed"],
        }

    try:
        product_info = await analyze_product_image(raw_bytes, user_id=user_id)
        captions, (price_min, price_max) = await generate_captions(product_info, shg_name=_shg_name(state), user_id=user_id)
    except UsageLimitExceededError:
        return {
            "outbound_messages": [{"type": "text", "body": LIMIT_EXCEEDED_MSG}],
            "trace": ["catalog_node:usage_limit_exceeded"],
        }
    except ModelUnavailableError:
        return {
            "outbound_messages": [{"type": "text", "body": "এই মুহূর্তে ছবি প্রসেস করতে সমস্যা হচ্ছে। একটু পরে আবার পাঠান।"}],
            "trace": ["catalog_node:model_unavailable"],
        }

    agreed_price = state.get("agreed_price")
    state_clears: dict = {}
    if agreed_price is not None:
        price_min, price_max = agreed_price, agreed_price
        state_clears = {"agreed_price": None, "pending_price_chat": None}

    market_note = await _market_note(state, product_info.get("category", "other"))

    processed_key = f"catalog/{state.get('user_id', 'unknown')}/{uuid.uuid4().hex[:10]}.png"
    try:
        await asyncio.to_thread(upload_bytes, processed_key, processed_bytes, "image/png")
    except Exception:
        return {
            "outbound_messages": [{"type": "text", "body": "ছবি সংরক্ষণ করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।"}],
            "trace": ["catalog_node:s3_upload_failed"],
        }

    outbound_messages, poster_key, poster_tier = await _build_delivery_messages(
        processed_bytes, processed_key, product_info, captions, price_min, price_max,
        market_note, state,
    )

    await _record_creation(state, raw_key, poster_key or processed_key, product_info, captions, price_min, price_max)

    return {
        **state_clears,
        "catalog_result": {
            "product_type": product_info.get("product_type"),
            "caption_bengali": captions["whatsapp_caption"],
            "ad_caption_bengali": captions["ad_caption"],
            "price_min": price_min,
            "price_max": price_max,
            "processed_s3_key": poster_key or processed_key,
        },
        "outbound_messages": outbound_messages,
        "trace": [f"catalog_node:done:{product_info.get('vision_model_used')}:poster={poster_tier}:agreed_price={agreed_price is not None}"],
    }


async def _build_delivery_messages(processed_bytes, processed_key, product_info, captions, price_min, price_max, market_note, state):
    ad_caption_full = captions["ad_caption"] + (f"\n{market_note}" if market_note else "")

    poster_bytes, poster_tier = await generate_poster(
        processed_bytes,
        product_name=_product_label_bengali(product_info),
        ad_caption=ad_caption_full,
        price_min=price_min,
        price_max=price_max,
        shg_name=_shg_name(state),
        user_id=state.get("user_id"),
    )

    if poster_bytes:
        poster_key = processed_key.replace(".png", f"-poster-{poster_tier}.jpg")
        try:
            await asyncio.to_thread(upload_bytes, poster_key, poster_bytes, "image/jpeg")
            poster_url = generate_read_url(poster_key)
            return (
                [
                    {"type": "image", "url": poster_url, "caption": captions["whatsapp_caption"]},
                    {"type": "text", "body": "ইংরেজিতেও ক্যাপশন চান? (শহুরে কাস্টমারদের জন্য) — 'হ্যাঁ' লিখুন।"},
                ],
                poster_key,
                poster_tier,
            )
        except Exception:
            logger.warning("poster upload failed (tier=%s), falling back to plain image delivery", poster_tier)

    try:
        processed_url = generate_read_url(processed_key)
    except Exception:
        return (
            [{"type": "text", "body": "ছবি পাঠাতে একটু সমস্যা হচ্ছে। একটু পরে আবার চেষ্টা করুন।"}],
            None,
            "none",
        )

    messages = [
        {"type": "image", "url": processed_url, "caption": captions["whatsapp_caption"]},
        {"type": "text", "body": "📣 বিজ্ঞাপনের জন্য এই সংক্ষিপ্ত বার্তাটিও ব্যবহার করতে পারেন:\n\n" + ad_caption_full},
        {"type": "text", "body": "ইংরেজিতেও ক্যাপশন চান? (শহুরে কাস্টমারদের জন্য) — 'হ্যাঁ' লিখুন।"},
    ]
    return messages, None, "none"


async def _market_note(state: ConversationState, vision_category: str) -> str | None:
    profile = state.get("user_profile") or {}
    block = profile.get("block")
    keywords = _CATEGORY_KEYWORDS.get(vision_category)
    if not block or not keywords:
        return None

    try:
        rows = await block_sales_trend(block)
    except Exception:
        return None

    by_category: dict[str, list[dict]] = {}
    for row in rows:
        cat = row["category"] or ""
        if any(kw in cat for kw in keywords):
            by_category.setdefault(cat, []).append(row)

    for series in by_category.values():
        series_sorted = sorted(series, key=lambda r: r["week"] or "", reverse=True)
        if classify_trend(series_sorted) == "rising":
            return "📈 আপনার এলাকায় এই ধরনের পণ্যের চাহিদা বাড়ছে — এখনই ভালো সময় বিক্রির জন্য!"
    return None


def _shg_name(state: ConversationState) -> str:
    profile = state.get("user_profile") or {}
    return profile.get("shg_name", "")


def _product_label_bengali(product_info: dict) -> str:
    local_match = find_local_product_by_slug(product_info.get("product_type", ""))
    if local_match:
        return local_match["name_bengali"]
    return product_info.get("product_type") or "পণ্য"


async def _record_creation(state, raw_key, processed_key, product_info, captions, price_min, price_max) -> None:
    user_id = state.get("user_id")
    if not user_id:
        return
    try:
        from shared.db.session import get_db_session
        from shared.db.models import CatalogCreation

        async with get_db_session() as db:
            db.add(
                CatalogCreation(
                    user_id=user_id,
                    raw_image_s3_key=raw_key,
                    processed_image_s3_key=processed_key,
                    product_type=product_info.get("product_type"),
                    caption_bengali=captions["whatsapp_caption"],
                    ad_caption_bengali=captions["ad_caption"],
                    price_suggestion_min=price_min,
                    price_suggestion_max=price_max,
                    vision_model_used=product_info.get("vision_model_used"),
                )
            )
            await db.commit()
    except Exception:
        pass
