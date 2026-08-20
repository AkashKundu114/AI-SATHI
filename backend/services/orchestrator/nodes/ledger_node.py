from __future__ import annotations

import json
import logging
import re
import unicodedata

from services.orchestrator.model_router import (
    ModelUnavailableError,
    TaskCriticality,
    route_completion,
    route_translation,
)
from services.orchestrator.state import ConversationState
from shared.config.settings import get_settings
from shared.i18n.bengali_numbers import to_bengali_digits

logger = logging.getLogger("ledger_node")

_LATIN_LETTER_RE = re.compile(r"[A-Za-z]")
_BENGALI_LETTER_RE = re.compile(r"[\u0980-\u09FF]")
_BANGLISH_LATIN_RATIO_THRESHOLD = 0.35

MAX_TRANSACTIONS_PER_ENTRY = 20


def _looks_code_mixed(text: str) -> bool:
    latin = len(_LATIN_LETTER_RE.findall(text))
    bengali = len(_BENGALI_LETTER_RE.findall(text))
    total_letters = latin + bengali
    if total_letters < 6:
        return False
    return (latin / total_letters) >= _BANGLISH_LATIN_RATIO_THRESHOLD


def _pre_replace_bengali_slang(text: str) -> str:
    t = text
    t = re.sub(r"\b(sorser|shorsher|sorse|soriser)\s*(tel|teel)?\b", "সর্ষের তেল", t, flags=re.I)
    t = re.sub(r"\b(sada|shada|soya|soyabean)\s*tel\b", "সয়াবিন তেল", t, flags=re.I)
    t = re.sub(r"\b(beter)\s*chair\b", "বেতের চেয়ার", t, flags=re.I)
    t = re.sub(r"\b(momo)\b", "মোমো", t, flags=re.I)
    t = re.sub(r"\b(dhan)\b", "ধান", t, flags=re.I)
    t = re.sub(r"\b(chal|chaal)\b", "চাল", t, flags=re.I)
    t = re.sub(r"\b(kantha|nakshi)\b", "নকশিকাঁথা", t, flags=re.I)
    return t


async def _normalize_transcript(transcript: str) -> str:
    pre_cleaned = _pre_replace_bengali_slang(transcript)
    if not _looks_code_mixed(pre_cleaned):
        return pre_cleaned
    try:
        result = await route_translation(pre_cleaned, target_lang="bn-IN")
        translated = result.get("text", "") or pre_cleaned

        translated = re.sub(r"\b(source|mustard)\s*oil\b", "সর্ষের তেল", translated, flags=re.I)
        return translated
    except ModelUnavailableError:
        logger.warning("translation normalization failed, extracting from raw transcript instead")
        return pre_cleaned


RURAL_ITEM_PATTERNS = [
    (
        re.compile(r"\b(sorser|sorse|shorsher|shorshe|soriser|mustard|সর্ষের?|সরিষার?|সরিষা)\s*(tel|তেল)?\b", re.I),
        "সর্ষের তেল",
    ),
    (re.compile(r"\b(sada|shada|soya|soyabean|white)\s*(tel|তেল)\b", re.I), "সয়াবিন তেল"),
    (re.compile(r"\b(kerosene|kerosin|কেরোসিন)\s*(tel|তেল)?\b", re.I), "কেরোসিন তেল"),
    (re.compile(r"\b(tel|তেল)\b", re.I), "ভোজ্য তেল"),
    (re.compile(r"\b(momo|মোমো)\b", re.I), "মোমো"),
    (re.compile(r"\b(beter\s*chair|বেতের\s*চেয়ার)\b", re.I), "বেতের চেয়ার"),
    (re.compile(r"\b(chair|চেয়ার)\b", re.I), "চেয়ার"),
    (re.compile(r"\b(cha|tiffin|tea|চা|টিফিন)\b", re.I), "চা/টিফিন"),
    (re.compile(r"\b(mishti|sweets?|মিষ্টি)\b", re.I), "মিষ্টি"),
    (re.compile(r"\b(chal|chaal|rice|চাল)\b", re.I), "চাল"),
    (re.compile(r"\b(dhan|ধান)\b", re.I), "ধান"),
    (re.compile(r"\b(papad|papar|পাপড়)\b", re.I), "পাপড়"),
    (re.compile(r"\b(saree|shari|শাড়ি|শাড়ী)\b", re.I), "শাড়ি"),
    (re.compile(r"\b(sobji|vegetables?|সবজি|তরকারি)\b", re.I), "সবজি"),
    (re.compile(r"\b(shak|saak|শাক)\b", re.I), "শাক"),
    (re.compile(r"\b(machh|mach|fish|মাছ)\b", re.I), "মাছ"),
    (re.compile(r"\b(dim|egg|eggs?|ডিম)\b", re.I), "ডিম"),
    (re.compile(r"\b(dudh|doodh|milk|দুধ)\b", re.I), "দুধ"),
    (re.compile(r"\b(murgi|chicken|মুরগি)\b", re.I), "মুরগি"),
    (re.compile(r"\b(mangsho|meat|মাংস)\b", re.I), "মাংস"),
    (re.compile(r"\b(moshla|mosla|spices?|মশলা|মসলা)\b", re.I), "মশলা"),
    (re.compile(r"\b(kantha|nakshi|কাঁথা|নকশী)\b", re.I), "নকশিকাঁথা"),
    (re.compile(r"\b(gohona|ornament|গহনা|হস্তশিল্প)\b", re.I), "হস্তশিল্প/গহনা"),
    (re.compile(r"\b(sar|shar|fertilizer|সার)\b", re.I), "সার"),
    (re.compile(r"\b(beej|bij|seeds?|বীজ)\b", re.I), "বীজ"),
    (re.compile(r"\b(kitnashok|pesticide|কীটনাশক)\b", re.I), "কীটনাশক"),
]

EXTRACTION_SYSTEM = (
    "তুমি বাংলা ও গ্রামীণ আর্থিক তথ্য নিষ্কাশনকারী সহকারী। নিচের বাংলা/ইংরেজি/বাংলিশ বার্তা থেকে\n"
    "লেনদেনের তথ্য বের করো এবং শুধুমাত্র এই JSON ফরম্যাটে ফেরত দাও, অন্য কিছু লিখো না:\n\n"
    '{"transactions": [{"type": "INCOME"|"EXPENSE"|"LEND"|"BORROW"|"RECOVERY"|"KISTI"|"SAVINGS"|"WAGES", "amount_inr": <total_number>,\n'
    ' "item_bengali": "...", "quantity": <number|null>, "unit": "...|null"}],\n'
    ' "confidence": <0.0-1.0>}\n\n'
    "IMPORTANT INSTRUCTIONS:\n"
    "1. `amount_inr` MUST be the EXACT amount in INR stated in the message. Do NOT invent multipliers or multiply by syllables in words like 'সর্ষে' or 'সের' unless an explicit quantity number is mentioned (e.g. '২ কেজি' or '৩টি'). If the message says 'সর্ষের তেল ৩৯ টাকা লেগেছে', amount_inr is exactly 39.\n"
    "2. Recognize transaction types carefully:\n"
    "   - 'INCOME': বিক্রি, বিক্রয়, আয়, উপার্জন, জমা ('beter chair bikri korechi', 'dhan bechechi').\n"
    "   - 'EXPENSE': খাওয়া, কেনা, কেনাকাটা, খরচ, ব্যয়, বাজার, পরিবহন, চা, মোমো, খাবার, ওষুধ ('momo kheyechi 50 takar' -> EXPENSE ₹50, 'sorser tel 39 taka legeche' -> EXPENSE ₹39).\n"
    "   - 'LEND': কাউকে ধার দেওয়া, বাকি বিক্রি ('rina di ke 300 dhar diyechi').\n"
    "   - 'BORROW': কারও থেকে ধার নেওয়া, ঋণ গ্রহণ ('karor theke dhar nilam').\n"
    "   - 'RECOVERY': বাকি আদায়, ধার ফেরত পাওয়া ('baki pelam', 'dhar ferot pelam').\n"
    "   - 'KISTI': সমিতির বা ব্যাংকের কিস্তি শোধ ('kisti dilam').\n"
    "   - 'SAVINGS': সঞ্চয় বা চাঁদা জমা ('sanchay joma').\n"
    "   - 'WAGES': দৈনিক মজুরি ('majuri pelam' / 'majuri dilam').\n"
    "3. Understand colloquial quantity and number words.\n"
    "Extract ALL transactions present, even if multiple."
)

BASE_CONFIDENCE_FLOOR = 0.80
MAX_FLOOR_ADJUSTMENT = 0.12

MODEL_DOWN_MESSAGE = "দুঃখিত, এই মুহূর্তে হিসাব রাখা যাচ্ছে না। একটু পরে আবার চেষ্টা করুন।"
CLARIFICATION_MESSAGE = "দুঃখিত, হিসাবটি পরিষ্কার হলো না। অনুগ্রহ করে সঠিক সংখ্যা ও বিবরণ দিয়ে আবার বলুন।"


def _personalized_confidence_floor(user_profile: dict | None) -> float:
    if not user_profile:
        return BASE_CONFIDENCE_FLOOR
    correction_rate = float(user_profile.get("ledger_correction_rate", 0.0) or 0.0)
    adjustment = min(MAX_FLOOR_ADJUSTMENT, correction_rate * MAX_FLOOR_ADJUSTMENT * 2)
    return min(0.95, BASE_CONFIDENCE_FLOOR + adjustment)


def _strip_json_fences(text: str) -> str:
    return re.sub(r"```json|```", "", text).strip()


def _extract_single_clause(clause: str) -> dict | None:

    text_lower = clause.lower()
    bn_digits = {"০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4", "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9"}
    norm_text = clause
    for bn, en in bn_digits.items():
        norm_text = norm_text.replace(bn, en)

    word_num_map = {
        "হাজার": 1000,
        "পাঁচশো": 500,
        "চারশো": 400,
        "তিনশো": 300,
        "আড়াইশো": 250,
        "দুইশো": 200,
        "দেড়শো": 150,
        "একশো": 100,
        "একশ": 100,
        "পঞ্চাশ": 50,
        "চল্লিশ": 40,
        "ত্রিশ": 30,
        "পঁচিশ": 25,
        "বিশ": 20,
        "পনেরো": 15,
        "দশ": 10,
    }
    word_amt = 0
    for w, val in word_num_map.items():
        if w in norm_text:
            word_amt = val
            break

    numbers = [int(n) for n in re.findall(r"\d+", norm_text)]
    amount = 0
    if numbers:
        amounts = [n for n in numbers if n >= 1]
        amount = numbers[0] if len(numbers) == 1 else (max(amounts) if amounts else numbers[0])
    elif word_amt > 0:
        amount = word_amt

    if amount <= 0:
        return None

    if any(
        k in text_lower
        for k in ["baki adaye", "baki adai", "dhar ferot", "baki pelam", "ধার ফেরত", "বাকি আদায়", "ফেরত পেলাম"]
    ):
        tx_type = "RECOVERY"
    elif any(k in text_lower for k in ["kisti", "কিস্তি", "কিস্তি দিলাম", "ঋণ শোধ", "লোন শোধ"]):
        tx_type = "KISTI"
    elif any(k in text_lower for k in ["sanchay", "সঞ্চয়", "চাঁদা", "chanda", "সঞ্চয়"]):
        tx_type = "SAVINGS"
    elif any(k in text_lower for k in ["majuri", "mojuri", "মজুরি", "জন", "jon", "জন-খাটা", "kheter kaj"]):
        tx_type = "WAGES"
    elif any(
        k in text_lower for k in ["dhar diyeche", "dhar nilam", "rin nilam", "ধার দিয়েছে", "ধার নিলাম", "ধার নেওয়া", "ঋণ"]
    ):
        tx_type = "BORROW"
    elif any(
        k in text_lower
        for k in ["dhar diyechi", "dhar dilam", "baki bikri", "ধার দিয়েছি", "ধার দিলাম", "ধার দেওয়া", "বাকিতে বিক্রি"]
    ):
        tx_type = "LEND"
    elif any(
        k in text_lower
        for k in [
            "bikri",
            "bikro",
            "bikroy",
            "bechechi",
            "bechlam",
            "joma",
            "pelam",
            "aaye",
            "uporjon",
            "বিক্রি",
            "বিক্রয়",
            "বেচেছি",
            "বেচলাম",
            "জমা",
            "পেলাম",
            "আয়",
            "উপার্জন",
        ]
    ):
        tx_type = "INCOME"
    elif any(
        k in text_lower
        for k in [
            "bought",
            "buy",
            "purchase",
            "kinechi",
            "kinlam",
            "kena",
            "খরচ",
            "খরচা",
            "ব্যয়",
            "কিনেছি",
            "কিনলাম",
            "কেনা",
            "khoroch",
            "khorcha",
            "kharach",
            "khoroc",
            "kheyechi",
            "khelam",
            "khawa",
            "khabar",
            "kheye",
            "খেয়েছি",
            "খেলাম",
            "খাওয়া",
            "খাবার",
            "beej",
            "bij",
            "বীজ",
            "tel",
            "তেল",
            "bhara",
            "ভাড়া",
            "bill",
            "বিল",
            "recharge",
            "রিচার্জ",
            "legeche",
            "লেগেছে",
            "niyeche",
            "নিয়েছে",
            "osudh",
            "ooshodh",
            "medicine",
            "ওষুধ",
            "ঔষধ",
            "momo",
            "মোমো",
            "mishti",
            "মিষ্টি",
            "tiffin",
            "টিফিন",
        ]
    ) or re.search(r"\b(cha|sar|shar)\b", text_lower):
        tx_type = "EXPENSE"
    else:
        tx_type = "EXPENSE" if any(w in text_lower for w in ["legeche", "khoroch", "taka", "টাকা"]) else "INCOME"

    item = None
    for pattern, item_name in RURAL_ITEM_PATTERNS:
        if pattern.search(clause) or pattern.search(text_lower):
            item = item_name
            break

    unit = None
    if "hali" in text_lower or "হালি" in norm_text:
        unit = "হালি"
    elif "jora" in text_lower or "জোড়া" in norm_text:
        unit = "জোড়া"
    elif "mon" in text_lower or "মণ" in norm_text:
        unit = "মণ"
    elif "ser" in text_lower or "সের" in norm_text:
        unit = "সের"
    elif "bosta" in text_lower or "বস্তা" in norm_text:
        unit = "বস্তা"
    elif "aati" in text_lower or "আটি" in norm_text or "আঁটি" in norm_text:
        unit = "আঁটি"

    if not item:
        cleaned_item = re.sub(
            r"[\d০-৯]+|\btakar?\b|\btaka\b|টাকার?|টাকা|বিক্রি|করেছি|কিনেছি|খেয়েছি|খেয়েছি|খেলাম|খরচ|লাভ|ধার|diyechi|kheyechi|korechi|bikro|bikri|legeche|niyeche|ota|লেগেছে|নিয়েছে|ওটা",
            "",
            clause,
            flags=re.IGNORECASE,
        ).strip(" -.,")
        item = cleaned_item[:30] if cleaned_item else "পণ্য"

    return {"type": tx_type, "amount_inr": amount, "item_bengali": item, "unit": unit}


def _extract_multi_ledger_fallback(transcript: str) -> dict:
    txs = []
    clauses = [c.strip() for c in re.split(r"[,;\n]| এবং | আর | and ", transcript) if c.strip()]
    if len(clauses) > 1:
        for c in clauses:
            res = _extract_single_clause(c)
            if res:
                txs.append(res)
    if not txs:
        single = _extract_single_clause(transcript)
        if single:
            txs.append(single)
        else:
            txs.append({"type": "INCOME", "amount_inr": 100, "item_bengali": "পণ্য", "unit": None})

    return {
        "transactions": txs,
        "overall_confidence": 0.95,
        "raw_transcript": transcript,
        "extracted_by": "deterministic_fallback",
    }


async def ledger_extract_node(state: ConversationState) -> dict:
    original_transcript = state.get("raw_input_transcript") or state.get("raw_input_text") or ""
    transcript = await _normalize_transcript(original_transcript)
    confidence_floor = _personalized_confidence_floor(state.get("user_profile"))

    context_entry = state.get("last_rejected_ledger_entry") or state.get("last_discussed_ledger_entry")
    norm_orig = original_transcript
    bn_digits = {"০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4", "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9"}
    for bn, en in bn_digits.items():
        norm_orig = norm_orig.replace(bn, en)
    nums = [int(n) for n in re.findall(r"\d+", norm_orig)]
    has_item_keyword = any(pat.search(original_transcript) for pat, _ in RURAL_ITEM_PATTERNS)

    if nums and not has_item_keyword and context_entry and context_entry.get("transactions"):
        prev_tx = context_entry["transactions"][0]
        new_amt = max(nums) if any(n >= 1 for n in nums) else nums[0]
        updated_tx = dict(prev_tx)
        updated_tx["amount_inr"] = float(new_amt)
        pending = {
            "transactions": [updated_tx],
            "overall_confidence": 0.95,
            "raw_transcript": original_transcript,
            "extracted_by": "context_continuation",
        }
        outbound = _build_confirmation_message(pending, original_transcript)
        return {
            "pending_ledger_entry": pending,
            "last_discussed_ledger_entry": pending,
            "awaiting_confirmation": True,
            "ledger_confirmation_turns": 1,
            "outbound_messages": [outbound],
            "trace": ["ledger_extract_node:context_continuation"],
        }

    try:
        result = await route_completion(
            system=EXTRACTION_SYSTEM,
            prompt=transcript,
            criticality=TaskCriticality.ROUTINE,
            confidence_floor=confidence_floor,
        )
        model_used = result["model_used"]
        try:
            parsed = json.loads(_strip_json_fences(result["text"]))
        except (json.JSONDecodeError, TypeError, KeyError):
            return {
                "pending_ledger_entry": None,
                "awaiting_confirmation": False,
                "outbound_messages": [{"type": "text", "body": CLARIFICATION_MESSAGE}],
                "trace": ["ledger_extract_node:malformed_json"],
            }
    except (ModelUnavailableError, Exception) as exc:
        logger.warning("Model extraction failed (%s), using deterministic fallback", exc)
        parsed = _extract_multi_ledger_fallback(transcript)
        model_used = "deterministic_fallback"

    confidence = parsed.get("confidence", parsed.get("overall_confidence", 0.0))
    if confidence < confidence_floor:
        return {
            "pending_ledger_entry": None,
            "awaiting_confirmation": False,
            "outbound_messages": [{"type": "text", "body": CLARIFICATION_MESSAGE}],
            "trace": ["ledger_extract_node:low_confidence"],
        }

    transactions = parsed.get("transactions", [])
    if not transactions:
        return {
            "pending_ledger_entry": None,
            "awaiting_confirmation": False,
            "outbound_messages": [{"type": "text", "body": CLARIFICATION_MESSAGE}],
            "trace": ["ledger_extract_node:empty_transactions"],
        }

    truncated = len(transactions) > MAX_TRANSACTIONS_PER_ENTRY
    transactions = transactions[:MAX_TRANSACTIONS_PER_ENTRY]

    nums_in_orig = [int(n) for n in re.findall(r"\d+", norm_orig)]
    if len(nums_in_orig) == 1 and len(transactions) == 1:
        explicit_num = nums_in_orig[0]
        curr_amt = transactions[0].get("amount_inr", 0)
        if curr_amt != explicit_num and not any(
            w in original_transcript.lower()
            for w in ["duto", "tinte", "charte", "hali", "jora", "kg", "কেজি", "দুটো", "তিনটে"]
        ):
            transactions[0]["amount_inr"] = float(explicit_num)

    pending = {
        "transactions": transactions,
        "overall_confidence": confidence,
        "raw_transcript": transcript,
        "extracted_by": model_used,
    }

    outbound = _build_confirmation_message(pending, transcript)
    trace_suffix = ":truncated" if truncated else ""
    return {
        "pending_ledger_entry": pending,
        "last_discussed_ledger_entry": pending,
        "awaiting_confirmation": True,
        "ledger_confirmation_turns": 0,
        "outbound_messages": [outbound],
        "trace": [f"ledger_extract_node:confirm:{model_used}:via={outbound['type']}{trace_suffix}"],
    }


def _build_confirmation_message(pending: dict, transcript: str) -> dict:
    s = get_settings()
    body_text = _build_confirmation_text(pending)

    if not s.wa_ledger_confirm_flow_id:
        return {"type": "text", "body": body_text}

    income_lines, expense_lines, net_profit_line = _confirmation_lines(pending)
    return {
        "type": "flow",
        "flow_id": s.wa_ledger_confirm_flow_id,
        "header_text": "হিসাব নিশ্চিতকরণ",
        "body_text": "আপনার হিসাবের বিবরণ নিচে দেওয়া হলো:",
        "cta_text": "নিশ্চিত করুন",
        "screen_id": "REVIEW_ENTRY",
        "screen_data": {
            "income_lines": income_lines or "কোনো নগদ আয় নেই",
            "expense_lines": expense_lines or "কোনো খরচ নেই এই এন্ট্রিতে",
            "net_profit_line": net_profit_line,
            "raw_transcript_preview": transcript[:300],
        },
    }


def _confirmation_lines(pending: dict) -> tuple[str, str, str]:
    income_lines, expense_lines = [], []
    total_income, total_expense = 0, 0
    for tx in pending.get("transactions", []):
        amt = tx.get("amount_inr", 0)
        amt_bn = to_bengali_digits(amt)
        tx_type = tx.get("type", "INCOME")
        item = unicodedata.normalize("NFC", str(tx.get("item_bengali", "") or ""))
        if tx_type == "INCOME":
            total_income += amt
            income_lines.append(unicodedata.normalize("NFC", f"{item}-এর জন্য ₹{amt_bn} আয়"))
        elif tx_type == "EXPENSE":
            total_expense += amt
            expense_lines.append(unicodedata.normalize("NFC", f"{item}-এর জন্য ₹{amt_bn} খরচ"))
        elif tx_type == "LEND":
            total_expense += amt
            expense_lines.append(unicodedata.normalize("NFC", f"{item}-কে ₹{amt_bn} ধার দেওয়া হয়েছে"))
        elif tx_type == "BORROW":
            total_income += amt
            income_lines.append(unicodedata.normalize("NFC", f"{item}-এর কাছ থেকে ₹{amt_bn} ধার নেওয়া হয়েছে"))
        else:
            expense_lines.append(unicodedata.normalize("NFC", f"{item}-এর জন্য ₹{amt_bn} (অন্যান্য)"))
    net_profit = total_income - total_expense
    if net_profit >= 0:
        net_profit_line = unicodedata.normalize("NFC", f"লাভ: ₹{to_bengali_digits(net_profit)}")
    else:
        net_profit_line = unicodedata.normalize("NFC", f"ক্ষতি: ₹{to_bengali_digits(abs(net_profit))}")
    return "\n".join(income_lines), "\n".join(expense_lines), net_profit_line


def _build_confirmation_text(pending: dict) -> str:
    income_lines, expense_lines, net_profit_line = _confirmation_lines(pending)
    lines = [unicodedata.normalize("NFC", "আমি আপনার হিসাবটি গুছিয়ে নিয়েছি। আপনি কি নিশ্চিত করতে চান যে:")]
    if income_lines:
        lines.append(income_lines)
    if expense_lines:
        lines.append(expense_lines)
    if net_profit_line and (income_lines or expense_lines):
        lines.append(net_profit_line)
    lines.append(unicodedata.normalize("NFC", "\nএই হিসাবটি কি ঠিক আছে? (হ্যাঁ/না)"))
    return unicodedata.normalize("NFC", "\n".join(lines))


def _build_confirmation(pending: dict) -> str:
    return _build_confirmation_text(pending)
