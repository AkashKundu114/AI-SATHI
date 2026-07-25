from __future__ import annotations

import json

from services.orchestrator.state import ConversationState
from services.orchestrator.model_router import (
    route_completion,
    TaskCriticality,
    ModelUnavailableError,
)

FINANCIAL_KEYWORDS = {"bikri", "বিক্রি", "kharach", "খরচ", "hisab", "হিসাব", "taka", "টাকা", "labh", "লাভ"}
REPORT_KEYWORDS = {"report", "রিপোর্ট", "maaser hisab", "মাসের হিসাব"}
MARKET_KEYWORDS = {"ki banabo", "কি বানাবো", "bazar", "বাজার", "chahida", "চাহিদা", "demand"}
PRICING_KEYWORDS = {"দাম", "কত দামে", "price", "koto dam", "দাম কত"}
NEGOTIATION_KEYWORDS = {"দরদাম", "দর কষাকষি", "bargain", "negotiate", "কমান", "কম দামে বলেছে"}
# Distinct from PRICING_KEYWORDS: PRICING gives a one-shot deterministic
# recommendation; PRICE_CHAT starts the multi-turn "decide together, like a
# friend" conversation in price_chat_node.py. Checked before the broader
# PRICING keywords so an explicit "একসাথে দাম ঠিক করি" routes to the chat,
# not the one-shot recommendation.
PRICE_CHAT_KEYWORDS = {"একসাথে দাম", "দাম ঠিক করি", "discuss price", "দাম আলোচনা"}

INTENT_CLASSIFY_SYSTEM = (
    "তুমি কোথা-খাতার ইনটেন্ট ক্লাসিফায়ার।\n"
    "ব্যবহারকারীর বার্তা পড়ে নিচের একটি ক্যাটাগরি বেছে নাও এবং শুধু JSON ফেরত দাও:\n"
    '{"feature": "LEDGER" | "LEDGER_REPORT" | "MARKET" | "PRICING" | "NEGOTIATION" | "PRICE_CHAT" | "UNKNOWN", "confidence": <0.0-1.0>}'
)


async def classify_intent(state: ConversationState) -> dict:
    text = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").lower()

    if any(k in text for k in REPORT_KEYWORDS):
        return {"active_feature": "LEDGER_REPORT", "trace": ["intent_router:keyword:LEDGER_REPORT"]}
    if any(k in text for k in FINANCIAL_KEYWORDS):
        return {"active_feature": "LEDGER", "trace": ["intent_router:keyword:LEDGER"]}
    if any(k in text for k in NEGOTIATION_KEYWORDS):
        return {"active_feature": "NEGOTIATION", "trace": ["intent_router:keyword:NEGOTIATION"]}
    if any(k in text for k in PRICE_CHAT_KEYWORDS):
        return {"active_feature": "PRICE_CHAT", "trace": ["intent_router:keyword:PRICE_CHAT"]}
    if any(k in text for k in PRICING_KEYWORDS):
        return {"active_feature": "PRICING", "trace": ["intent_router:keyword:PRICING"]}
    if any(k in text for k in MARKET_KEYWORDS):
        return {"active_feature": "MARKET", "trace": ["intent_router:keyword:MARKET"]}

    if not text.strip():
        return {"active_feature": "IDLE", "trace": ["intent_router:empty_input"]}

    try:
        result = await route_completion(
            system=INTENT_CLASSIFY_SYSTEM, prompt=text, criticality=TaskCriticality.ROUTINE
        )
    except ModelUnavailableError:
        # Keyword matching already failed above; without the model we can't
        # classify — fall back to the unhandled-feature menu rather than crash.
        return {"active_feature": "IDLE", "trace": ["intent_router:model_unavailable"]}

    try:
        parsed = json.loads(result["text"])
        feature = parsed.get("feature", "UNKNOWN")
    except (json.JSONDecodeError, TypeError):
        feature = "UNKNOWN"

    return {
        "active_feature": feature if feature != "UNKNOWN" else "IDLE",
        "trace": [f"intent_router:llm:{result['model_used']}:{feature}"],
    }
