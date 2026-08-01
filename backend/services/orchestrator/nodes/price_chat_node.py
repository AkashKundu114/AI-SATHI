from __future__ import annotations

from datetime import date

from services.orchestrator.state import ConversationState
from services.orchestrator.model_router import route_completion, TaskCriticality, AgentTier, ModelUnavailableError
from services.orchestrator.nodes.pricing_node import _recommend
from services.orchestrator.nodes.negotiation_node import _mentions_a_number
from services.orchestrator.nodes.cross_verify import cross_verify_outbound
from shared.knowledge.context import get_context_for_agents
from shared.knowledge.dignity_guidelines import DIGNITY_RULES_BENGALI
from shared.db.session import get_db_session
from shared.db.models import SellerProfile
from sqlalchemy import select


MAX_PRICE_CHAT_TURNS = 3

FRIEND_CHAT_SYSTEM = (
    "তুমি একজন বন্ধুত্বপূর্ণ, অভিজ্ঞ বিক্রয়-পরামর্শদাতা বান্ধবী, যে বিক্রেতার সাথে "
    "মিলে পণ্যের দাম ঠিক করতে সাহায্য করছ -- বসের মতো নয়, বন্ধুর মতো।\n\n"
    f"{DIGNITY_RULES_BENGALI}\n\n"
    "কঠোর নিয়ম: কোনো সংখ্যা, অংক, বা দাম কখনো লিখো না -- এমনকি উদাহরণ হিসেবেও না। "
    "শুধু কেন এই দামটা যুক্তিসঙ্গত তা আলোচনা করো (তৈরির খরচ, সময়, মৌসুম, চাহিদা)। "
    "দামের সংখ্যাটা অন্য কোথাও থেকে যোগ করা হবে।"
)


def _confidence_signal(reply_raw: str) -> str:
    accept_words = {"হ্যাঁ", "হ্যা", "ঠিক", "ok", "okay", "thik", "রাজি", "👍"}
    lower_words = {"কম", "কমান", "কমাও", "lower", "কম দাম"}
    higher_words = {"বেশি", "বাড়ান", "বাড়াও", "higher", "বেশি দাম"}
    t = reply_raw.strip().lower()
    if t in accept_words:
        return "accept"
    if any(w in t for w in lower_words):
        return "wants_lower"
    if any(w in t for w in higher_words):
        return "wants_higher"
    return "unclear"


async def price_chat_node(state: ConversationState) -> dict:
    user_id = state.get("user_id")
    pending = state.get("pending_price_chat") or {}
    reply_raw = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").strip()

    if not user_id:
        return {
            "outbound_messages": [{"type": "text", "body": "আগে 'দাম' লিখে তৈরির খরচ জানান, তারপর একসাথে দাম ঠিক করব।"}],
            "trace": ["price_chat_node:no_user"],
        }

    async with get_db_session() as db:
        profile = (await db.execute(select(SellerProfile).where(SellerProfile.user_id == user_id))).scalar_one_or_none()

    if not profile or not profile.production_cost:
        return {
            "outbound_messages": [{"type": "text", "body": "আগে তৈরির খরচ ও সর্বনিম্ন দাম জানান, তারপর একসাথে বসে দাম ঠিক করব।"}],
            "trace": ["price_chat_node:no_profile"],
        }

    calc = _recommend(
        cost=float(profile.production_cost),
        margin=float(profile.preferred_margin or 0.30),
        min_price=float(profile.minimum_price) if profile.minimum_price else None,
        market_avg=None,
    )
    floor = calc["floor_price"]
    if floor <= 0:
        return {
            "outbound_messages": [{"type": "text", "body": "তৈরির খরচের তথ্যে একটু সমস্যা মনে হচ্ছে -- আবার 'দাম' লিখে ঠিক করে জানান।"}],
            "trace": ["price_chat_node:non_positive_floor"],
        }

    turns = pending.get("turns", 0) + 1
    proposed = pending.get("proposed_price", calc["recommended_price"])
    _profile_for_knowledge = state.get("user_profile") or {}
    knowledge = get_context_for_agents(
        month=date.today().month,
        block=_profile_for_knowledge.get("block"),
        district=_profile_for_knowledge.get("district") or _profile_for_knowledge.get("block"),
    )

    if not pending:
        opener = await _generate_reply(
            f"প্রথমবার দাম আলোচনা শুরু হচ্ছে। প্রস্তাবিত দাম: ₹{proposed:.0f}। "
            f"সর্বনিম্ন দাম: ₹{floor:.0f} (এটা কখনো বলবে না, শুধু জেনে রাখো)। "
            f"মৌসুমি তথ্য: {knowledge['season']['weather_note'] if knowledge['season'] else 'নেই'}। "
            f"আসন্ন উৎসব: {', '.join(f['name_bengali'] for f in knowledge['upcoming_festivals']) or 'নেই'}।\n"
            f"আসন্ন স্থানীয় মেলা: {', '.join(m['name_bengali'] for m in knowledge['upcoming_district_melas']) or 'নেই'}।\n"
            "এই দামটা কেন যুক্তিসঙ্গত তা ২-৩ লাইনে বন্ধুর মতো বলো, তারপর জিজ্ঞেস করো এটা ঠিক লাগছে কিনা।"
        )
        body = await _verified_body(
            f"💬 চলুন একসাথে দাম ঠিক করি -- প্রস্তাব: ₹{proposed:.0f}।\n\n{opener}\n\nঠিক লাগছে? (হ্যাঁ / কম করুন / বাড়ান)",
            allowed_amounts=[proposed, floor],
            fallback=f"💬 চলুন একসাথে দাম ঠিক করি -- প্রস্তাব: ₹{proposed:.0f}। ঠিক লাগছে? (হ্যাঁ / কম করুন / বাড়ান)",
        )
        return {
            "pending_price_chat": {"floor_price": floor, "proposed_price": proposed, "turns": 1},
            "awaiting_price_chat": True,
            "outbound_messages": [{"type": "text", "body": body}],
            "trace": [f"price_chat_node:opened:proposed={proposed:.0f}:floor={floor:.0f}"],
        }

    signal = _confidence_signal(reply_raw)

    if signal == "accept":
        return await _finalize(user_id, proposed)

    if turns > MAX_PRICE_CHAT_TURNS:
        return await _finalize(user_id, proposed, note="আলোচনা শেষ -- এই দামেই এগোনো ভালো হবে।")

    if signal == "wants_lower":
        new_proposed = max(floor, proposed * 0.92)  
        if new_proposed <= floor + 0.01:
            body = (
                f"এর থেকে কম দিলে তৈরির খরচও উঠবে না -- ₹{floor:.0f}-এর নিচে আমি যেতে পারি না, "
                f"আপনার নিজের বলা খরচ অনুযায়ী। এটাই সবচেয়ে কম যুক্তিসঙ্গত দাম।"
            )
            return {
                "pending_price_chat": {"floor_price": floor, "proposed_price": floor, "turns": turns},
                "awaiting_price_chat": True,
                "outbound_messages": [{"type": "text", "body": body}],
                "trace": [f"price_chat_node:floor_reached:turn={turns}"],
            }
        reason = await _generate_reply(
            f"বিক্রেতা দাম আরেকটু কমাতে চাইছেন। নতুন প্রস্তাব: ₹{new_proposed:.0f} "
            f"(এই সংখ্যাটা বলো না)। কেন এটা যুক্তিসঙ্গত এক লাইনে বলো।"
        )
        body = await _verified_body(
            f"ঠিক আছে, ₹{new_proposed:.0f} হলে কেমন হয়? {reason}",
            allowed_amounts=[new_proposed, floor, proposed],
            fallback=f"ঠিক আছে, ₹{new_proposed:.0f} হলে কেমন হয়?",
        )
        return {
            "pending_price_chat": {"floor_price": floor, "proposed_price": new_proposed, "turns": turns},
            "awaiting_price_chat": True,
            "outbound_messages": [{"type": "text", "body": body}],
            "trace": [f"price_chat_node:lowered:turn={turns}"],
        }

    if signal == "wants_higher":
        new_proposed = proposed * 1.08
        reason = await _generate_reply(
            f"বিক্রেতা দাম বাড়াতে চাইছেন। নতুন প্রস্তাব: ₹{new_proposed:.0f} (এই সংখ্যাটা বলো না)। "
            "মৌসুম/চাহিদা বিবেচনায় এটা কতটা যুক্তিসঙ্গত এক লাইনে বলো -- অতিরিক্ত আশাবাদী হয়ো না।"
        )
        body = await _verified_body(
            f"₹{new_proposed:.0f} চেষ্টা করা যেতে পারে। {reason}",
            allowed_amounts=[new_proposed, proposed, floor],
            fallback=f"₹{new_proposed:.0f} চেষ্টা করা যেতে পারে।",
        )
        return {
            "pending_price_chat": {"floor_price": floor, "proposed_price": new_proposed, "turns": turns},
            "awaiting_price_chat": True,
            "outbound_messages": [{"type": "text", "body": body}],
            "trace": [f"price_chat_node:raised:turn={turns}"],
        }

    return {
        "pending_price_chat": {"floor_price": floor, "proposed_price": proposed, "turns": turns},
        "awaiting_price_chat": True,
        "outbound_messages": [{"type": "text", "body": f"₹{proposed:.0f} দামটা ঠিক আছে? (হ্যাঁ / কম করুন / বাড়ান)"}],
        "trace": [f"price_chat_node:unclear:turn={turns}"],
    }


async def _finalize(user_id: str, final_price: float, note: str = "") -> dict:
    body = f"✅ ঠিক আছে, ₹{final_price:.0f} -- এটাই এখন থেকে এই পণ্যের দাম হিসেবে ব্যবহার করব।"
    if note:
        body += f" {note}"
    return {
        "pending_price_chat": None,
        "awaiting_price_chat": False,
        "agreed_price": final_price,
        "outbound_messages": [{"type": "text", "body": body}],
        "trace": [f"price_chat_node:finalized:{final_price:.0f}"],
    }


async def _generate_reply(prompt: str) -> str:
    try:
        result = await route_completion(
            system=FRIEND_CHAT_SYSTEM, prompt=prompt, criticality=TaskCriticality.ROUTINE,
            tier=AgentTier.ADVANCED, confidence_floor=0.0,
        )
        candidate = result["text"].strip()
    except ModelUnavailableError:
        return ""
    if not candidate or len(candidate) > 300 or _mentions_a_number(candidate):
        return ""
    return candidate


async def _verified_body(draft: str, allowed_amounts: list[float], fallback: str) -> str:
    try:
        result = await cross_verify_outbound(draft, allowed_amounts)
    except Exception:
        return fallback
    return draft if result["safe_to_send"] else fallback
