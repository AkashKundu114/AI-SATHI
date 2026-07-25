from __future__ import annotations

"""Cross-agent verification — the person asked that "one output from an
agent should be verified and researched by other agents" before the user
sees it. This is a bounded, honest version of that idea, consistent with
the rest of this codebase's philosophy (grounding_verifier.py already does
exactly this for RAG answers — assertion extraction + independent check,
never trust generation alone).

What this genuinely does: runs a SECOND, independently-prompted model call
(different system prompt, no shared context with the first call beyond the
draft text itself) that checks a draft outbound message against two things:
  1. Dignity — does it match shared/knowledge/dignity_guidelines.py's rules?
  2. Numeric integrity — does every ₹ amount in the draft exactly match one
     of the `allowed_amounts` the caller passed in? (allowed_amounts should
     always be code-computed values, e.g. from pricing_node._recommend —
     never taken from the first agent's own text, or this check is
     circular and worthless.)

What this deliberately does NOT do: run a full second RAG pipeline, spin up
a debate between agents, or replace the existing deterministic guards
(_validate_amount, _mentions_a_number, grounding_verifier). Those stay as
the primary defense; this is an additional, cheap sanity pass on top,
scoped to messages that are about to go out to the user. A "have every
agent's output re-derived and cross-checked by every other agent" system
is a much larger, multi-day architecture change (real inter-agent protocol,
latency budget rework, cost model rework) — flagged here as a real
follow-up, not attempted in this pass.
"""

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
    """Deterministic, no LLM — every ₹ figure in the draft must match one
    of the caller-supplied, code-computed allowed_amounts within a small
    rounding tolerance. Returns which amounts (if any) don't match anything
    the caller actually computed, i.e. amounts the LLM invented."""
    found = _extract_rupee_amounts(draft_text)
    unmatched = [
        amt for amt in found
        if not any(abs(amt - allowed) <= tolerance for allowed in allowed_amounts)
    ]
    return {"numeric_ok": len(unmatched) == 0, "found_amounts": found, "unmatched_amounts": unmatched}


async def verify_dignity(draft_text: str) -> dict:
    """Independent second model call for a tone check. Fails open (treats
    as ok) on model unavailability rather than blocking delivery — a tone
    check should degrade gracefully, the same way every other optional
    enrichment in this codebase does (market notes, mandi prices)."""
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
    """Convenience combined check. Callers (pricing_node, price_chat_node,
    catalog_node) can call this on a fully-composed outbound body before
    returning it. If numeric_ok is False, the caller MUST NOT send the
    draft as-is — fall back to a deterministic, code-only message instead
    (same fail-safe direction as grounding_verifier's fallback line)."""
    numeric = check_numeric_integrity(draft_text, allowed_amounts)
    dignity = await verify_dignity(draft_text)
    return {**numeric, **dignity, "safe_to_send": numeric["numeric_ok"] and dignity["dignity_ok"]}
