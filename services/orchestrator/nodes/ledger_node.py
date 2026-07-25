from __future__ import annotations

import json
import logging
import re

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
    "তুমি বাংলা আর্থিক তথ্য নিষ্কাশনকারী। নিচের বাংলা টেক্সট থেকে\n"
    "লেনদেন বের করো এবং শুধুমাত্র এই JSON ফরম্যাটে ফেরত দাও, অন্য কিছু লিখো না:\n\n"
    '{"transactions": [{"type": "INCOME"|"EXPENSE", "amount_inr": <number>,\n'
    ' "item_bengali": "...", "quantity": <number|null>, "unit": "...|null"}],\n'
    ' "confidence": <0.0-1.0>}\n\n'
    "Bengali number words: এক=1, দুই=2, তিন=3, চার=4, পাঁচ=5, দশ=10, পনেরো=15,\n"
    "বিশ=20, পঁচিশ=25, ত্রিশ=30, পঞ্চাশ=50, একশো=100, দুইশো=200, তিনশো=300,\n"
    "পাঁচশো=500, হাজার=1000. Extract ALL transactions present, even if multiple."
)

BASE_CONFIDENCE_FLOOR = 0.80
MAX_FLOOR_ADJUSTMENT = 0.12
MODEL_DOWN_MESSAGE = (
    "এই মুহূর্তে হিসাব প্রসেস করতে সমস্যা হচ্ছে। একটু পরে আবার চেষ্টা করুন।"
)


def _personalized_confidence_floor(user_profile: dict | None) -> float:
    if not user_profile:
        return BASE_CONFIDENCE_FLOOR
    correction_rate = float(user_profile.get("ledger_correction_rate", 0.0) or 0.0)
    adjustment = min(MAX_FLOOR_ADJUSTMENT, correction_rate * MAX_FLOOR_ADJUSTMENT * 2)
    return min(0.95, BASE_CONFIDENCE_FLOOR + adjustment)


def _strip_json_fences(text: str) -> str:
    return re.sub(r"```json|```", "", text).strip()


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
    except ModelUnavailableError:
        return {
            "pending_ledger_entry": None,
            "awaiting_confirmation": False,
            "outbound_messages": [{"type": "text", "body": MODEL_DOWN_MESSAGE}],
            "trace": ["ledger_extract_node:model_unavailable"],
        }

    try:
        parsed = json.loads(_strip_json_fences(result["text"]))
    except json.JSONDecodeError:
        parsed = {"transactions": [], "confidence": 0.0}

    pending = {
        "transactions": parsed.get("transactions", []),
        "overall_confidence": parsed.get("confidence", 0.0),
        "raw_transcript": transcript,
        "extracted_by": result["model_used"],
    }

    if pending["overall_confidence"] < 0.5 or not pending["transactions"]:
        clarify_msg = (
            "একটু পরিষ্কার হলো না। আবার বলুন? "
            "যেমন: '৩০০ টাকা পাপড় বিক্রি করেছি, ১০০ টাকা মশলা কিনেছি'"
        )
        return {
            "pending_ledger_entry": None,
            "awaiting_confirmation": False,
            "outbound_messages": [{"type": "text", "body": clarify_msg}],
            "trace": [f"ledger_extract_node:clarify:{result['model_used']}"],
        }

    outbound = _build_confirmation_message(pending, transcript)
    return {
        "pending_ledger_entry": pending,
        "awaiting_confirmation": True,
        "ledger_confirmation_turns": 0,
        "outbound_messages": [outbound],
        "trace": [f"ledger_extract_node:confirm:{result['model_used']}:floor={confidence_floor:.2f}:via={outbound['type']}"],
    }


def _build_confirmation_message(pending: dict, transcript: str) -> dict:
    """Two delivery paths, same underlying numbers:
      - If WA_LEDGER_CONFIRM_FLOW_ID is configured, send the tap-to-confirm
        Flow (ledger_confirm_flow.json) — no free text to mistype/mishear
        on the way to a permanent DB write.
      - Otherwise, unchanged plain-text হ্যাঁ/না confirmation, exactly as
        before this pass — nothing breaks for a deployment that hasn't set
        up the Flow yet.
    Both paths are consumed downstream by the SAME `_save()` in
    ledger_confirm_node.py — see graph.py's routing in _route_after_profile_load.
    """
    s = get_settings()
    body_text = _build_confirmation_text(pending)

    if not s.wa_ledger_confirm_flow_id:
        return {"type": "text", "body": body_text}

    income_lines, expense_lines, net_profit_line = _confirmation_lines(pending)
    return {
        "type": "flow",
        "flow_id": s.wa_ledger_confirm_flow_id,
        "header_text": "হিসাব যাচাই করুন",
        "body_text": "আপনার হিসাবটা একবার দেখে নিন, তারপর বেছে নিন।",
        "cta_text": "যাচাই করুন",
        "screen_id": "REVIEW_ENTRY",
        "screen_data": {
            "income_lines": income_lines or "কোনো আয় নেই এই এন্ট্রিতে",
            "expense_lines": expense_lines or "কোনো খরচ নেই এই এন্ট্রিতে",
            "net_profit_line": net_profit_line,
            "raw_transcript_preview": transcript[:300],
        },
    }


def _confirmation_lines(pending: dict) -> tuple[str, str, str]:
    income_lines, expense_lines = [], []
    total_income, total_expense = 0, 0
    for tx in pending["transactions"]:
        amt = tx.get("amount_inr", 0)
        amt_bn = to_bengali_digits(amt)
        if tx.get("type") == "INCOME":
            total_income += amt
            income_lines.append(f"✅ আয়: {tx.get('item_bengali', '')} → ₹{amt_bn}")
        else:
            total_expense += amt
            expense_lines.append(f"📤 খরচ: {tx.get('item_bengali', '')} → ₹{amt_bn}")
    net_line = f"লাভ: ₹{to_bengali_digits(total_income - total_expense)}"
    return "\n".join(income_lines), "\n".join(expense_lines), net_line


def _build_confirmation_text(pending: dict) -> str:
    income_lines, expense_lines, net_line = _confirmation_lines(pending)
    lines = ["আমি এইটুকু বুঝলাম:"]
    if income_lines:
        lines.append(income_lines)
    if expense_lines:
        lines.append(expense_lines)
    lines.append(f"\n💰 {net_line}")
    lines.append("\nঠিক আছে? (হ্যাঁ/না)")
    return "\n".join(lines)


def _build_confirmation(pending: dict) -> str:
    """Kept for backward compatibility — ledger_confirm_node.py's correction
    loop still calls this directly by name after re-extracting a correction,
    where the tap-to-confirm Flow doesn't apply (a correction reply is
    already free text, so the response stays text too)."""
    return _build_confirmation_text(pending)
