from __future__ import annotations

from services.orchestrator.model_router import ModelUnavailableError, TaskCriticality, route_completion
from services.orchestrator.state import ConversationState
from shared.guardrails.output_guard import enforce_output_guard
from shared.knowledge.dignity_guidelines import DIGNITY_RULES_BENGALI

CANNED_FALLBACK = "আমি হিসাব রাখতে, পণ্যের বিজ্ঞাপন বানাতে, আর বাজারের পরামর্শ দিতে পারি। কি দরকার আপনার?"

CONVERSATION_SYSTEM = (
    "তুমি AI-সাথী বট, পশ্চিমবঙ্গের স্বনির্ভর গোষ্ঠীর মহিলাদের একজন উষ্ণ, বন্ধুত্বপূর্ণ সহায়ক।\n"
    "ব্যবহারকারী এমন কিছু জিজ্ঞেস করেছেন যা তোমার মূল কাজের বাইরে (হিসাব, পণ্যের বিজ্ঞাপন, বাজারের পরামর্শ)।\n\n"
    f"{DIGNITY_RULES_BENGALI}\n\n"
    "নিয়ম:\n"
    "1. ছোট, উষ্ণ, সম্মানজনক উত্তর দাও - ২-৩ বাক্যের বেশি নয়।\n"
    "2. চিকিৎসা, আইনি, বা আর্থিক পরামর্শ কখনো দিও না - এমন প্রশ্নে বলো এটি তোমার বিশেষজ্ঞতার বাইরে।\n"
    "3. প্রতিটি উত্তরের শেষে নরমভাবে মূল তিনটি কাজের দিকে ফিরিয়ে আনো।\n"
    "4. কোনো ব্যক্তিগত তথ্য (আধার, ব্যাংক অ্যাকাউন্ট, OTP) কখনো চেও না।"
)


async def general_conversation_node(state: ConversationState) -> dict:
    text = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").strip()
    if not text:
        return {
            "outbound_messages": [{"type": "text", "body": CANNED_FALLBACK}],
            "trace": ["general_conversation_node:empty_input"],
        }

    try:
        result = await route_completion(
            system=CONVERSATION_SYSTEM,
            prompt=text,
            criticality=TaskCriticality.ROUTINE,
            confidence_floor=0.0,
            conversational=True,
        )

        reply_raw = result["text"].strip() or CANNED_FALLBACK
        reply = enforce_output_guard(reply_raw, fallback=CANNED_FALLBACK)
        trace_suffix = "" if reply == reply_raw else ":output_guard_triggered"
        return {
            "outbound_messages": [{"type": "text", "body": reply}],
            "trace": [f"general_conversation_node:{result['model_used']}{trace_suffix}"],
        }
    except ModelUnavailableError:
        return {
            "outbound_messages": [{"type": "text", "body": CANNED_FALLBACK}],
            "trace": ["general_conversation_node:model_unavailable"],
        }
