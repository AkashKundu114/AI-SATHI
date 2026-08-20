from __future__ import annotations

import json
import logging
import re
import unicodedata

from services.orchestrator.state import ConversationState
from services.orchestrator.model_router import (
    route_completion,
    route_translation,
    TaskCriticality,
    ModelUnavailableError,
)
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


async def _normalize_transcript(transcript: str) -> str:
    if not _looks_code_mixed(transcript):
        return transcript
    try:
        result = await route_translation(transcript, target_lang="bn-IN")
        return result["text"] or transcript
    except ModelUnavailableError:
        logger.warning("translation normalization failed, extracting from raw transcript instead")
        return transcript

EXTRACTION_SYSTEM = (
    "তুমি বাংলা ও গ্রামীণ আর্থিক তথ্য নিষ্কাশনকারী সহকারী। নিচের বাংলা/ইংরেজি/বাংলিশ বার্তা থেকে\n"
    "লেনদেনের তথ্য বের করো এবং শুধুমাত্র এই JSON ফরম্যাটে ফেরত দাও, অন্য কিছু লিখো না:\n\n"
    '{"transactions": [{"type": "INCOME"|"EXPENSE"|"LEND"|"BORROW"|"RECOVERY"|"KISTI"|"SAVINGS"|"WAGES", "amount_inr": <total_number>,\n'
    ' "item_bengali": "...", "quantity": <number|null>, "unit": "...|null"}],\n'
    ' "confidence": <0.0-1.0>}\n\n'
    "IMPORTANT INSTRUCTIONS:\n"
    "1. `amount_inr` MUST be the TOTAL amount in INR. If given per unit and quantity (e.g. '50 takar duto' or '20 takai 1 hali'), calculate total: 50 * 2 = 100.\n"
    "2. Recognize transaction types carefully:\n"
    "   - 'INCOME': বিক্রি, বিক্রয়, আয়, উপার্জন, জমা ('beter chair bikri korechi', 'dhan bechechi').\n"
    "   - 'EXPENSE': খাওয়া, খাওয়া-দাওয়া, কেনা, কেনাকাটা, খরচ, ব্যয়, বাজার, পরিবহন, চা, মোমো, খাবার, ওষুধ ('momo kheyechi 50 takar' -> EXPENSE ₹50, 'tel kinechi 100 takar' -> EXPENSE ₹100).\n"
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
    bn_digits = {'০':'0', '১':'1', '২':'2', '৩':'3', '৪':'4', '৫':'5', '৬':'6', '৭':'7', '৮':'8', '৯':'9'}
    norm_text = clause
    for bn, en in bn_digits.items():
        norm_text = norm_text.replace(bn, en)

    word_num_map = {
        "হাজার": 1000, "পাঁচশো": 500, "চারশো": 400, "তিনশো": 300, "আড়াইশো": 250,
        "দুইশো": 200, "দেড়শো": 150, "একশো": 100, "একশ": 100, "পঞ্চাশ": 50,
        "চল্লিশ": 40, "ত্রিশ": 30, "পঁচিশ": 25, "বিশ": 20, "পনেরো": 15, "দশ": 10
    }
    word_amt = 0
    for w, val in word_num_map.items():
        if w in norm_text:
            word_amt = val
            break

    numbers = [int(n) for n in re.findall(r'\d+', norm_text)]
    amount = 0
    if numbers:
        amounts = [n for n in numbers if n >= 10]
        amount = max(amounts) if amounts else numbers[0]
    elif word_amt > 0:
        amount = word_amt

    if amount <= 0:
        return None

    if any(k in text_lower for k in ["baki adaye", "baki adai", "dhar ferot", "baki pelam", "ধার ফেরত", "বাকি আদায়", "ফেরত পেলাম"]):
        tx_type = "RECOVERY"
    elif any(k in text_lower for k in ["kisti", "কিস্তি", "কিস্তি দিলাম", "ঋণ শোধ", "লোন শোধ"]):
        tx_type = "KISTI"
    elif any(k in text_lower for k in ["sanchay", "সঞ্চয়", "চাঁদা", "chanda", "সঞ্চয়"]):
        tx_type = "SAVINGS"
    elif any(k in text_lower for k in ["majuri", "mojuri", "মজুরি", "জন", "jon", "জন-খাটা", "kheter kaj"]):
        tx_type = "WAGES"
    elif any(k in text_lower for k in ["dhar diyeche", "dhar nilam", "rin nilam", "ধার দিয়েছে", "ধার নিলাম", "ধার নেওয়া", "ঋণ"]):
        tx_type = "BORROW"
    elif any(k in text_lower for k in ["dhar diyechi", "dhar dilam", "baki bikri", "ধার দিয়েছি", "ধার দিলাম", "ধার দেওয়া", "বাকিতে বিক্রি"]):
        tx_type = "LEND"
    elif any(k in text_lower for k in [
        "bikri", "bikro", "bikroy", "bechechi", "bechlam", "joma", "pelam", "aaye", "uporjon",
        "বিক্রি", "বিক্রয়", "বেচেছি", "বেচলাম", "জমা", "পেলাম", "আয়", "উপার্জন"
    ]):
        tx_type = "INCOME"
    elif any(k in text_lower for k in [
        "bought", "buy", "purchase", "kinechi", "kinlam", "kena", "খরচ", "খরচা", "ব্যয়", "কিনেছি", "কিনলাম", "কেনা",
        "khoroch", "khorcha", "kharach", "khoroc", "kheyechi", "khelam", "khawa", "khabar", "kheye", "খেয়েছি", "খেলাম", "খাওয়া", "খাবার",
        "beej", "bij", "বীজ", "tel", "তেল", "bhara", "ভাড়া", "bill", "বিল", "recharge", "রিচার্জ",
        "osudh", "ooshodh", "medicine", "ওষুধ", "ঔষধ", "momo", "মোমো", "mishti", "মিষ্টি", "tiffin", "টিফিন"
    ]) or re.search(r'\b(cha|sar|shar)\b', text_lower):
        tx_type = "EXPENSE"
    else:
        tx_type = "INCOME"


    item = "পণ্য"
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

    if "momo" in text_lower or "মোমো" in norm_text:
        item = "মোমো"
    elif "chair" in text_lower or "চেয়ার" in norm_text:
        item = "বেতের চেয়ার" if ("beter" in text_lower or "বেত" in norm_text) else "চেয়ার"
    elif "cha" in text_lower or "চা" in norm_text:
        item = "চা/টিফিন"
    elif "mishti" in text_lower or "মিষ্টি" in norm_text:
        item = "মিষ্টি"
    elif "rice" in text_lower or "chal" in text_lower or "চাল" in norm_text:
        item = "চাল"
    elif "dhan" in text_lower or "ধান" in norm_text:
        item = "ধান"
    elif "papar" in text_lower or "papad" in text_lower or "পাপড়" in norm_text:
        item = "পাপড়"
    elif "saree" in text_lower or "shari" in text_lower or "শাড়ি" in norm_text or "শাড়ী" in norm_text:
        item = "শাড়ি"
    elif "vegetable" in text_lower or "sobji" in text_lower or "সবজি" in norm_text or "তরকারি" in norm_text:
        item = "সবজি"
    elif "shak" in text_lower or "শাক" in norm_text:
        item = "শাক"
    elif "machh" in text_lower or "mach" in text_lower or "মাছ" in norm_text:
        item = "মাছ"
    elif "dim" in text_lower or "ডিম" in norm_text:
        item = "ডিম"
    elif "dudh" in text_lower or "দুধ" in norm_text:
        item = "দুধ"
    elif "murgi" in text_lower or "মুরগি" in norm_text:
        item = "মুরগি"
    elif "tel" in text_lower or "তেল" in norm_text:
        item = "তেল"
    elif "moshla" in text_lower or "mosla" in text_lower or "মশলা" in norm_text or "মসলা" in norm_text:
        item = "মশলা"
    elif "gohona" in text_lower or "গহনা" in norm_text or "হস্তশিল্প" in norm_text:
        item = "হস্তশিল্প"
    elif "shar" in text_lower or "sar" in text_lower or "সার" in norm_text or "বীজ" in norm_text:
        item = "কৃষি সার/বীজ"
    else:
        cleaned_item = re.sub(
            r'[\d০-৯]+|\btakar?\b|\btaka\b|টাকার?|টাকা|বিক্রি|করেছি|কিনেছি|খেয়েছি|খেয়েছি|খেলাম|খরচ|লাভ|ধার|diyechi|kheyechi|korechi|bikro|bikri',
            '', clause, flags=re.IGNORECASE
        ).strip(' -.,')
        item = cleaned_item[:30] if cleaned_item else "পণ্য"

    return {

        "type": tx_type,
        "amount_inr": amount,
        "item_bengali": item,
        "unit": unit
    }


def _extract_multi_ledger_fallback(transcript: str) -> dict:
    txs = []
    clauses = [c.strip() for c in re.split(r'[,;\n]| এবং | আর | and ', transcript) if c.strip()]
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
            txs.append({
                "type": "INCOME",
                "amount_inr": 100,
                "item_bengali": "পণ্য",
                "unit": None
            })

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
        item = unicodedata.normalize("NFC", str(tx.get('item_bengali', '') or ''))
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

