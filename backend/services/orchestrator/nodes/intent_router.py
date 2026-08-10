from __future__ import annotations

import json

from services.orchestrator.state import ConversationState
from services.orchestrator.model_router import (
    route_completion,
    TaskCriticality,
    ModelUnavailableError,
)

FINANCIAL_KEYWORDS = {
    # Income & Sales
    "bikri", "bikrii", "bikrir", "bikrih", "বিক্রি", "বিক্রির", "বিক্রি করলাম",
    "sold", "sell", "selling", "sale", "labh", "লাভ", "aay", "আয়", "jama", "জমা",
    "pela", "পেলাম", "pelam", "pabona", "পাবো", "pawa", "পাওয়া", "nogod", "নগদ",
    # Expenses & Buying
    "bought", "buy", "buying", "purchase", "kharach", "khoroch", "খরচ", "ব্যয়", "byay",
    "kinechi", "কিনেছি", "kinlam", "কিনলাম", "dilam", "দিলাম", "diyechi", "দিয়েছি", "dilum",
    "suud", "সুদ", "kisti", "কিস্তি", "bhortuki", "ভর্তুকি", "anudaan", "অনুদানে",
    # Debt, Loan, SHG, Ledger & Accounts
    "dhar", "ধার", "baki", "বাকী", "বাকি", "dena", "দেনা", "powna", "পাওনা", "udhar", "উধার",
    "rin", "ঋণ", "loan", "sanchay", "সঞ্চয়", "samity", "সমিতি", "khatian", "খতিয়ান",
    "mohajon", "মহাজন", "chalan", "চালান", "bokeya", "বকেয়া", "poisa", "পয়সা", "poisha",
    "hisaab", "hisab", "হিসাব", "হিসাবে", "khata", "খাতা", "tule", "তুলে", "rakhun", "রাখুন",
    "entry", "এন্ট্রি", "ledger", "লেজার", "boi", "বই", "lenden", "লেনদেন",
    # Currency & Units
    "taka", "takai", "takar", "টাকা", "টাকায়", "টাকার", "rs", "rs.", "rupee", "rupees", "inr", "₹",
    "mon", "মণ", "ser", "সের", "poya", "পোয়া", "hali", "হালি", "jora", "জোড়া", "kuri", "কুড়ি",
    "bosta", "বস্তা", "aati", "আটি", "আঁটি", "bigha", "বিঘা", "katha", "কাঠা"
}
REPORT_KEYWORDS = {"report", "রিপোর্ট", "maaser hisab", "মাসের হিসাব", "সারসংক্ষেপ", "hisab nikesh", "হিসাব নিকাশ"}
UPGRADE_KEYWORDS = {"upgrade", "আপগ্রেড", "premium", "প্রিমিয়াম", "plan", "প্ল্যান"}
NEGOTIATION_KEYWORDS = {"দরদাম", "dordam", "bargain", "দামাদামি"}
MARKET_KEYWORDS = {"কি বানাবো", "ki banabo", "market", "বাজার", "bajar", "haat", "হাট", "কৈ মাছ", "সবজি মান্ডি"}
PRICING_KEYWORDS = {"দাম", "dam", "pricing", "দর", "রেট", "rate"}

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

