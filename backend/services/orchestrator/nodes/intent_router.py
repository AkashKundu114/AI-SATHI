from __future__ import annotations

import json

from services.orchestrator.state import ConversationState
from services.orchestrator.model_router import (
    route_completion,
    TaskCriticality,
    ModelUnavailableError,
)

FINANCIAL_KEYWORDS = {"bikri", "বিক্রি", "kharach", "খরচ", "hisab", "হিসাব", "taka", "টাকা", "labh", "লাভ", "dhar", "ধার", "baki", "বাকি", "dewa", "দেওয়া", "newa", "নেওয়া", "nilam", "নিলাম", "dilam", "দিলাম", "niyeche", "নিয়েছে", "diyeche", "দিয়েছে", "kinechi", "কিনেছি"}
REPORT_KEYWORDS = {"report", "রিপোর্ট", "maaser hisab", "মাসের হিসাব"}
UPGRADE_KEYWORDS = {"upgrade", "আপগ্রেড", "premium", "প্রিমিয়াম", "plan", "প্ল্যান"}
NEGOTIATION_KEYWORDS = {"দরদাম", "dordam"}
MARKET_KEYWORDS = {"কি বানাবো", "ki banabo", "market", "বাজার", "bajar"}
PRICING_KEYWORDS = {"দাম", "dam", "pricing"}

INTENT_CLASSIFY_SYSTEM = (
    "তুমি AI-সাথীর ইনটেন্ট ক্লাসিফায়ার।\n"
    "ব্যবহারকারীর বার্তা পড়ে নিচের একটি ক্যাটাগরি বেছে নাও এবং শুধু JSON ফেরত দাও:\n"
    '{"feature": "LEDGER" | "LEDGER_REPORT" | "MARKET" | "PRICING" | "NEGOTIATION" | "UPGRADE" | "UNKNOWN", "confidence": <0.0-1.0>}'
)


async def classify_intent(state: ConversationState) -> dict:
    text = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").lower()

    if any(k in text for k in REPORT_KEYWORDS):
        return {"active_feature": "LEDGER_REPORT", "trace": ["intent_router:keyword:LEDGER_REPORT"]}
    if any(k in text for k in FINANCIAL_KEYWORDS):
        return {"active_feature": "LEDGER", "trace": ["intent_router:keyword:LEDGER"]}
    if any(k in text for k in UPGRADE_KEYWORDS):
        return {"active_feature": "UPGRADE", "trace": ["intent_router:keyword:UPGRADE"]}
    if any(k in text for k in NEGOTIATION_KEYWORDS):
        return {"active_feature": "NEGOTIATION", "trace": ["intent_router:keyword:NEGOTIATION"]}
    if any(k in text for k in MARKET_KEYWORDS):
        return {"active_feature": "MARKET", "trace": ["intent_router:keyword:MARKET"]}
    if any(k in text for k in PRICING_KEYWORDS):
        return {"active_feature": "PRICING", "trace": ["intent_router:keyword:PRICING"]}

    if not text.strip():
        return {"active_feature": "IDLE", "trace": ["intent_router:empty_input"]}

    try:
        result = await route_completion(
            system=INTENT_CLASSIFY_SYSTEM, prompt=text, criticality=TaskCriticality.ROUTINE
        )
    except ModelUnavailableError:
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

