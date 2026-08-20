from __future__ import annotations

import json
import re

from services.orchestrator.model_router import (
    ModelUnavailableError,
    TaskCriticality,
    route_completion,
)
from services.orchestrator.state import ConversationState

AFFIRMATIVE = {
    "হ্যাঁ",
    "হ্যা",
    "ha",
    "haa",
    "haan",
    "thik",
    "ঠিক",
    "thik ache",
    "ঠিক আছে",
    "ok",
    "okay",
    "yes",
    "y",
    "yup",
    "hobe",
    "হবে",
    "hbe",
    "shothik",
    "সঠিক",
    "👍",
    "ji",
    "জি",
}
NEGATIVE = {
    "না",
    "no",
    "na",
    "bhul",
    "ভুল",
    "ঠিক নয়",
    "thik noy",
    "hobe na",
    "হবে না",
    "cancel",
    "bad din",
    "বাদ দিন",
    "দরকার নেই",
    "dorkar nei",
    "rakhbo na",
    "রাখব না",
}

MAX_CONFIRMATION_TURNS = 3
MAX_REASONABLE_AMOUNT = 500_000

CORRECTION_SYSTEM = (
    "তুমি বাংলা আর্থিক তথ্য নিষ্কাশনকারী। ব্যবহারকারী একটি পূর্বের\n"
    "নিষ্কাশনে সংশোধন দিয়েছেন। মূল বাক্য, পূর্বের ফলাফল এবং সংশোধনের ভিত্তিতে\n"
    "আপডেট করা JSON ফেরত দাও, একই ফরম্যাটে:\n\n"
    '{"transactions": [{"type": "INCOME"|"EXPENSE", "amount_inr": <number>,\n'
    ' "item_bengali": "...", "quantity": <number|null>, "unit": "...|null"}],\n'
    ' "confidence": <0.0-1.0>}'
)


def _validate_amount(amt: float) -> float | None:
    if amt != amt or amt in (float("inf"), float("-inf")):
        return None
    if amt < 0 or amt > MAX_REASONABLE_AMOUNT:
        return None
    return round(amt, 2)


async def ledger_confirm_node(state: ConversationState) -> dict:
    reply_raw = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").strip().lower()
    pending = state.get("pending_ledger_entry")
    turns = state.get("ledger_confirmation_turns", 0) + 1

    if not pending:
        return _reset_with_message("একটু সমস্যা হয়েছে। আবার হিসাব বলুন।", trace="ledger_confirm_node:no_pending")

    if turns > MAX_CONFIRMATION_TURNS:
        return _reset_with_message(
            "হিসাবটা বাদ দেওয়া হলো। নতুন করে বলুন কি বিক্রি বা খরচ হয়েছে।",
            trace="ledger_confirm_node:max_turns_exceeded",
        )

    if reply_raw in AFFIRMATIVE:
        return await _save(state, pending)

    if reply_raw in NEGATIVE and not _looks_like_correction(reply_raw):
        return _reset_with_message(
            "ঠিক আছে, এই হিসাবটি বাদ দেওয়া হলো। নতুন কোনো হিসাব থাকলে বলুন বা লিখুন।",
            trace=f"ledger_confirm_node:declined_by_user:turn={turns}",
            rejected_entry=pending,
        )

    if _looks_like_correction(reply_raw) or any(neg in reply_raw for neg in ["ভুল হয়েছে", "হিসাব ভুল", "সংশোধন"]):
        return await _apply_correction(state, pending, reply_raw, turns)

    return {
        "awaiting_confirmation": True,
        "ledger_confirmation_turns": turns,
        "outbound_messages": [{"type": "text", "body": "বুঝলাম না। 'হ্যাঁ' বা 'না' বলুন।"}],
        "trace": [f"ledger_confirm_node:unrecognized_reply:turn={turns}"],
    }


def _looks_like_correction(text: str) -> bool:
    return any(ch.isdigit() for ch in text) or any("০" <= ch <= "৯" for ch in text)


async def _apply_correction(state: ConversationState, pending: dict, correction_text: str, turns: int) -> dict:
    from services.orchestrator.nodes.ledger_node import (
        _build_confirmation,
        _extract_single_clause,
        _strip_json_fences,
    )

    prompt = (
        f"মূল বাক্য: {pending.get('raw_transcript', '')}\n"
        f"পূর্বের ফলাফল: {pending}\n"
        f"ব্যবহারকারীর সংশোধন: {correction_text}\n\n"
        "সংশোধন প্রয়োগ করে আপডেট করা JSON ফেরত দাও।"
    )
    try:
        result = await route_completion(
            system=CORRECTION_SYSTEM, prompt=prompt, criticality=TaskCriticality.ROUTINE, confidence_floor=0.80
        )
        try:
            parsed = json.loads(_strip_json_fences(result["text"]))
            txns = parsed.get("transactions", [])
            if txns:
                updated = {
                    "transactions": txns,
                    "overall_confidence": float(parsed.get("confidence", 0.9)),
                    "raw_transcript": pending.get("raw_transcript", ""),
                    "extracted_by": result.get("model_used", "sarvam-standard"),
                }
                return {
                    "pending_ledger_entry": updated,
                    "last_discussed_ledger_entry": updated,
                    "awaiting_confirmation": True,
                    "ledger_confirmation_turns": turns,
                    "outbound_messages": [
                        {
                            "type": "text",
                            "body": f"আমি আপনার হিসাবটি সংশোধন করেছি। আপনি কি নিশ্চিত করতে চান যে:\n{_build_confirmation(updated)}\n\nএই হিসাবটি কি ঠিক আছে? (হ্যাঁ/না)",
                        }
                    ],
                    "trace": [f"ledger_confirm_node:correction_applied:{result.get('model_used')}:turn={turns}"],
                }
            else:
                return _reset_with_message(
                    "সংশোধন বুঝতে পারলাম না। অনুগ্রহ করে আবার বলুন।", trace=f"ledger_confirm_node:malformed_json:turn={turns}"
                )
        except Exception:
            return _reset_with_message(
                "সংশোধন বুঝতে পারলাম না। অনুগ্রহ করে আবার বলুন।", trace=f"ledger_confirm_node:malformed_json:turn={turns}"
            )
    except ModelUnavailableError:
        nums = [int(n) for n in re.findall(r"\d+", correction_text)]
        txns = pending.get("transactions", [])
        if nums and txns:
            new_amt = max(nums) if any(n >= 10 for n in nums) else nums[0]
            corrected_txns = list(txns)
            corrected_txns[0] = dict(corrected_txns[0])
            corrected_txns[0]["amount_inr"] = float(new_amt)
            clause_extracted = _extract_single_clause(correction_text)
            if clause_extracted and clause_extracted.get("item_bengali") and clause_extracted["item_bengali"] != "পণ্য":
                corrected_txns[0]["item_bengali"] = clause_extracted["item_bengali"]

            updated = {
                "transactions": corrected_txns,
                "overall_confidence": 0.85,
                "raw_transcript": pending.get("raw_transcript", ""),
                "extracted_by": "deterministic_correction_fallback",
            }
            return {
                "pending_ledger_entry": updated,
                "last_discussed_ledger_entry": updated,
                "awaiting_confirmation": True,
                "ledger_confirmation_turns": turns,
                "outbound_messages": [
                    {"type": "text", "body": f"হিসাবটি সংশোধন করা হলো। আবার দেখুন:\n\n{_build_confirmation(updated)}"}
                ],
                "trace": [f"ledger_confirm_node:deterministic_correction:turn={turns}"],
            }
        return _reset_with_message(
            "এই মুহূর্তে সংশোধন প্রসেস করতে সমস্যা হচ্ছে। একটু পরে আবার চেষ্টা করুন।",
            trace=f"ledger_confirm_node:model_unavailable:turn={turns}",
        )


async def _save(state: ConversationState, pending: dict) -> dict:
    import re
    import uuid as _uuid

    from sqlalchemy import select

    from shared.db.models import LedgerEntry, User
    from shared.db.session import get_db_session

    user_id_raw = state.get("user_id") or state.get("phone_number")
    if not user_id_raw:
        return _reset_with_message(
            "হিসাব রাখতে সমস্যা হয়েছে। একটু পরে আবার চেষ্টা করুন।",
            trace="ledger_confirm_node:save_failed_no_user_id",
        )

    validated: list[tuple[dict, float]] = []
    for tx in pending.get("transactions", []):
        raw_amt = float(tx.get("amount_inr", 0) or 0)
        amt = _validate_amount(raw_amt)
        if amt is None:
            return _reset_with_message(
                "টাকার পরিমাণটা ঠিক বুঝতে পারলাম না। আবার বলুন, যেমন: '৩০০ টাকা পাপড় বিক্রি করেছি'",
                trace="ledger_confirm_node:amount_out_of_range",
            )
        validated.append((tx, amt))

    total_income, total_expense = 0.0, 0.0
    saved_count = 0

    try:
        async with get_db_session() as db:
            target_uuid = None
            if isinstance(user_id_raw, _uuid.UUID):
                target_uuid = user_id_raw
            elif isinstance(user_id_raw, str):
                try:
                    target_uuid = _uuid.UUID(user_id_raw)
                except (ValueError, TypeError):
                    target_uuid = None

            if hasattr(db, "execute"):
                user = None
                if target_uuid:
                    try:
                        user = (await db.execute(select(User).where(User.id == target_uuid))).scalar_one_or_none()
                    except Exception:
                        user = None

                if not user:
                    phone_query = str(user_id_raw).strip()
                    digits = re.sub(r"[^\d]", "", phone_query)
                    last10 = digits[-10:] if len(digits) >= 10 else digits
                    try:
                        user = (
                            (
                                await db.execute(
                                    select(User).where(
                                        (User.phone_number == phone_query)
                                        | (User.phone_number == f"+91{last10}")
                                        | (User.phone_number == last10)
                                        | (User.phone_number.endswith(last10))
                                    )
                                )
                            )
                            .scalars()
                            .first()
                        )
                    except Exception:
                        user = None

                if not user:
                    phone_query = str(user_id_raw).strip()
                    digits = re.sub(r"[^\d]", "", phone_query)
                    last10 = digits[-10:] if len(digits) >= 10 else digits
                    user = User(
                        id=_uuid.uuid4(),
                        phone_number=f"+91{last10}" if len(last10) == 10 else phone_query,
                        name="User",
                        verification_status="verified",
                    )
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)

                final_user_id = user.id if isinstance(user.id, _uuid.UUID) else _uuid.UUID(str(user.id))
            else:
                final_user_id = target_uuid or user_id_raw

            for tx, amt in validated:
                entry = LedgerEntry(
                    id=_uuid.uuid4(),
                    user_id=final_user_id,
                    entry_type=tx.get("type", "INCOME"),
                    amount_inr=amt,
                    category=tx.get("item_bengali"),
                    description_bengali=tx.get("item_bengali"),
                    quantity=tx.get("quantity"),
                    unit=tx.get("unit"),
                    raw_transcript=pending.get("raw_transcript"),
                    is_corrected=pending.get("extracted_by") is not None
                    and state.get("ledger_confirmation_turns", 0) > 0,
                    extracted_by=pending.get("extracted_by"),
                )
                db.add(entry)
                saved_count += 1
                if tx.get("type") == "INCOME":
                    total_income += amt
                else:
                    total_expense += amt
            await db.commit()

    except Exception as exc:
        import logging

        logger = logging.getLogger(__name__)
        try:
            from sqlalchemy.exc import SQLAlchemyError

            if isinstance(exc, SQLAlchemyError):
                logger.error("Database error saving ledger entry: %s", exc)
            else:
                logger.exception("Unexpected error saving ledger entry: %s", exc)
        except ImportError:
            logger.exception("Error saving ledger entry: %s", exc)

        return _reset_with_message(
            "হিসাব রাখতে সমস্যা হয়েছে। একটু পরে আবার চেষ্টা করুন।",
            trace="ledger_confirm_node:db_commit_failed",
        )

    import unicodedata

    success_msg = unicodedata.normalize(
        "NFC",
        (
            f"দারুণ! আপনার হিসাবটি সফলভাবে সংরক্ষণ করা হয়েছে।\n\n"
            f"আপনার এই এন্ট্রিতে মোট আয় হয়েছে ₹{total_income:.0f} এবং খরচ হয়েছে ₹{total_expense:.0f}। "
            f"মাসের শেষে রিপোর্ট দেখতে চাইলে শুধু 'রিপোর্ট' লিখুন বা বলুন।"
        ),
    )

    return {
        "pending_ledger_entry": None,
        "awaiting_confirmation": False,
        "ledger_confirmation_turns": 0,
        "outbound_messages": [{"type": "text", "body": success_msg}],
        "trace": [f"ledger_confirm_node:saved:{saved_count}_entries"],
    }


def _reset_with_message(msg: str, trace: str, rejected_entry: dict | None = None) -> dict:
    ret = {
        "pending_ledger_entry": None,
        "awaiting_confirmation": False,
        "ledger_confirmation_turns": 0,
        "outbound_messages": [{"type": "text", "body": msg}],
        "trace": [trace],
    }
    if rejected_entry:
        ret["last_rejected_ledger_entry"] = rejected_entry
        ret["last_discussed_ledger_entry"] = rejected_entry
    return ret
