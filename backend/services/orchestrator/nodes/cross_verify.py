from __future__ import annotations

import re

from services.orchestrator.model_router import route_completion, TaskCriticality, ModelUnavailableError
from shared.knowledge.dignity_guidelines import DIGNITY_RULES_BENGALI

VERIFY_SYSTEM = (
    "তুমি একজন স্বাধীন পর্যালোচক। নিচের বার্তাটি ব্যবহারকারীকে পাঠানোর আগে যাচাই করো।\n\n"
    f"{DIGNITY_RULES_BENGALI}\n\n"
    "শুধুমাত্র এই JSON ফরম্যাটে ফেরত দাও:\n"
    '{"dignity_ok": true|false, "reason": "<এক লাইনে, শুধু dignity_ok false হলে>"}'
)

_AMOUNT_RE = re.compile(r"₹\s?[০-৯0-9,]+")
_DIGIT_RE = re.compile(r"[০-৯0-9,]+")
_BENGALI_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def _extract_rupee_amounts(text: str) -> list[float]:
    out = []
    for m in _AMOUNT_RE.finditer(text):
        digits = _DIGIT_RE.search(m.group(0))
        if not digits:
            continue
        try:
            out.append(float(digits.group(0).translate(_BENGALI_DIGITS).replace(",", "")))
        except ValueError:
            continue
    return out


def check_numeric_integrity(draft_text: str, allowed_amounts: list[float], tolerance: float = 0.5) -> dict:
    found = _extract_rupee_amounts(draft_text)
    unmatched = [
        amt for amt in found
        if not any(abs(amt - allowed) <= tolerance for allowed in allowed_amounts)
    ]
    return {"numeric_ok": len(unmatched) == 0, "found_amounts": found, "unmatched_amounts": unmatched}


async def verify_dignity(draft_text: str) -> dict:
    try:
        result = await route_completion(
            system=VERIFY_SYSTEM, prompt=draft_text, criticality=TaskCriticality.ROUTINE, confidence_floor=0.0,
        )
    except ModelUnavailableError:
        return {"dignity_ok": True, "reason": "verifier_unavailable_failed_open"}

    import json

    try:
        parsed = json.loads(re.sub(r"```json|```", "", result["text"]).strip())
        return {"dignity_ok": bool(parsed.get("dignity_ok", True)), "reason": parsed.get("reason", "")}
    except (json.JSONDecodeError, TypeError):
        return {"dignity_ok": True, "reason": "verifier_parse_failed_failed_open"}


async def cross_verify_outbound(draft_text: str, allowed_amounts: list[float]) -> dict:
    numeric = check_numeric_integrity(draft_text, allowed_amounts)
    dignity = await verify_dignity(draft_text)
    return {**numeric, **dignity, "safe_to_send": numeric["numeric_ok"] and dignity["dignity_ok"]}
