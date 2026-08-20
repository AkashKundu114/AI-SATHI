from __future__ import annotations

import json

from services.orchestrator.model_router import (
    ModelUnavailableError,
    TaskCriticality,
    route_completion,
)
from services.orchestrator.state import ConversationState

FINANCIAL_KEYWORDS = {
    "bikri",
    "bikrii",
    "bikrir",
    "bikrih",
    "বিক্রি",
    "বিক্রির",
    "বিক্রি করলাম",
    "bechechi",
    "বেচেছি",
    "bechlam",
    "বেচলাম",
    "sold",
    "sell",
    "selling",
    "sale",
    "labh",
    "লাভ",
    "aay",
    "আয়",
    "jama",
    "জমা",
    "pela",
    "পেলাম",
    "pelam",
    "pabona",
    "পাবো",
    "pawa",
    "পাওয়া",
    "nogod",
    "নগদ",
    "bought",
    "buy",
    "buying",
    "purchase",
    "kharach",
    "khoroch",
    "খরচ",
    "ব্যয়",
    "byay",
    "kheyechi",
    "খেয়েছি",
    "khelam",
    "খেলাম",
    "khawa",
    "খাওয়া",
    "momo",
    "মোমো",
    "mishti",
    "মিষ্টি",
    "kinechi",
    "কিনেছি",
    "kinlam",
    "কিনলাম",
    "dilam",
    "দিলাম",
    "diyechi",
    "দিয়েছি",
    "dilum",
    "suud",
    "সুদ",
    "kisti",
    "কিস্তি",
    "bhortuki",
    "ভর্তুকি",
    "anudaan",
    "অনুদানে",
    "dhar",
    "ধার",
    "baki",
    "বাকী",
    "বাকি",
    "dena",
    "দেনা",
    "powna",
    "পাওনা",
    "udhar",
    "উধার",
    "rin",
    "ঋণ",
    "loan",
    "sanchay",
    "সঞ্চয়",
    "samity",
    "সমিতি",
    "khatian",
    "খতিয়ান",
    "mohajon",
    "মহাজন",
    "chalan",
    "চালান",
    "bokeya",
    "বকেয়া",
    "poisa",
    "পয়সা",
    "poisha",
    "hisaab",
    "hisab",
    "হিসাব",
    "হিসাবে",
    "khata",
    "খাতা",
    "tule",
    "তুলে",
    "rakhun",
    "রাখুন",
    "entry",
    "এন্ট্রি",
    "ledger",
    "লেজার",
    "boi",
    "বই",
    "lenden",
    "লেনদেন",
    "taka",
    "takai",
    "takar",
    "টাকা",
    "টাকায়",
    "টাকার",
    "rs",
    "rs.",
    "rupee",
    "rupees",
    "inr",
    "₹",
    "mon",
    "মণ",
    "ser",
    "সের",
    "poya",
    "পোয়া",
    "hali",
    "হালি",
    "jora",
    "জোড়া",
    "kuri",
    "কুড়ি",
    "bosta",
    "বস্তা",
    "aati",
    "আটি",
    "আঁটি",
    "bigha",
    "বিঘা",
    "katha",
    "কাঠা",
}
REPORT_KEYWORDS = {"report", "রিপোর্ট", "maaser hisab", "মাসের হিসাব", "সারসংক্ষেপ", "hisab nikesh", "হিসাব নিকাশ"}
UPGRADE_KEYWORDS = {"upgrade", "আপগ্রেড", "premium", "প্রিমিয়াম", "plan", "প্ল্যান"}
NEGOTIATION_KEYWORDS = {"দরদাম", "dordam", "bargain", "দামাদামি"}
MARKET_KEYWORDS = {"কি বানাবো", "ki banabo", "market", "বাজার", "bajar", "haat", "হাট", "কৈ মাছ", "সবজি মান্ডি"}
PRICING_KEYWORDS = {"দাম", "dam", "pricing", "দর", "রেট", "rate"}

INTENT_CLASSIFY_SYSTEM = (
    "You are the AI-SATHI intelligent intent classifier for rural Bengali and Banglish (Romanized Bengali) micro-entrepreneurs in West Bengal.\n"
    "Categorize the user's message into exactly one feature category based on deep semantic understanding:\n\n"
    "- 'LEDGER': Any financial transaction, sale (বিক্রি / bechechi / bikri / bikroi korlam / bechlam / বেচেছি), "
    "purchase/buy (কিনলাম / kinechi / kinlam / kena holo), food or personal expense (খেয়েছি / kheyechi / khelam / kharach / khoroch), "
    "daily business costs, transport, raw materials, labor, lending/debt/borrowing (ধার / দেনা / dhar dilam / baki / kisti / ঋণ / loan), "
    "paddy/crop/handicraft sales (ধান বিক্রি / dhan bikroi / চাল / মাছ / সবজি), cash received/given (টাকা পেলাম / টাকা দিলাম / rs), "
    "or any recordable income/expense transaction in pure Bengali or Banglish.\n"
    "- 'LEDGER_REPORT': Asking for financial reports, summary of accounts, total monthly calculation, or balances (হিসাবের রিপোর্ট / মাসের হিসাব / কত লাভ হলো / খাতা দেখাও).\n"
    "- 'MARKET': Inquiring about market trends, mandi prices, crop calendar, what products to make/sell (বাজার দর / কি বানাবো / কিসের চাহিদা / মান্ডি রেট).\n"
    "- 'PRICING': Asking for asking-price advice or recommended price for an item (কত দামে বিক্রি করব / দাম ঠিক করে দাও / pricing suggestion).\n"
    "- 'NEGOTIATION': Seeking bargaining advice or counter-offer tactics with buyers (গ্রাহক কম দিচ্ছে / দরদাম / bargaining advice).\n"
    "- 'UPGRADE': Inquiring about premium tiers or account upgrades.\n"
    "- 'UNKNOWN': Greetings (নমস্কার, হ্যালো, Hi), village chit-chat, onboarding details, or non-financial conversation.\n\n"
    "Respond strictly in JSON format:\n"
    '{"feature": "LEDGER" | "LEDGER_REPORT" | "MARKET" | "PRICING" | "NEGOTIATION" | "UPGRADE" | "UNKNOWN", "confidence": <0.0-1.0>}'
)


async def classify_intent(state: ConversationState) -> dict:
    text = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").lower()

    if any(k in text for k in REPORT_KEYWORDS):
        return {"active_feature": "LEDGER_REPORT", "trace": ["intent_router:keyword:LEDGER_REPORT"]}
    if any(k in text for k in UPGRADE_KEYWORDS):
        return {"active_feature": "UPGRADE", "trace": ["intent_router:keyword:UPGRADE"]}
    if any(k in text for k in NEGOTIATION_KEYWORDS):
        return {"active_feature": "NEGOTIATION", "trace": ["intent_router:keyword:NEGOTIATION"]}
    if any(k in text for k in MARKET_KEYWORDS):
        return {"active_feature": "MARKET", "trace": ["intent_router:keyword:MARKET"]}
    if any(k in text for k in PRICING_KEYWORDS):
        return {"active_feature": "PRICING", "trace": ["intent_router:keyword:PRICING"]}
    if any(k in text for k in FINANCIAL_KEYWORDS):
        return {"active_feature": "LEDGER", "trace": ["intent_router:keyword:LEDGER"]}

    has_numbers = any(ch.isdigit() for ch in text) or any("০" <= ch <= "৯" for ch in text)
    if has_numbers and (state.get("last_rejected_ledger_entry") or state.get("last_discussed_ledger_entry")):
        context_words = [
            "ota",
            "eta",
            "oi",
            "ei",
            "ta",
            "takar",
            "taka",
            "niyeche",
            "legeche",
            "chilo",
            "হলো",
            "ওটা",
            "এটা",
            "টাকা",
            "লেগেছে",
            "নিয়েছে",
            "হবে",
        ]
        if any(cw in text for cw in context_words) or len(text.split()) <= 4:
            return {"active_feature": "LEDGER", "trace": ["intent_router:context_followup:LEDGER"]}

    if not text.strip():
        return {"active_feature": "IDLE", "trace": ["intent_router:empty_input"]}

    try:
        result = await route_completion(system=INTENT_CLASSIFY_SYSTEM, prompt=text, criticality=TaskCriticality.ROUTINE)
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
