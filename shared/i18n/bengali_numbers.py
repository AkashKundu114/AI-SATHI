from __future__ import annotations

"""Centralized Bengali <-> Latin digit and number-word helpers.

Previously this exact translation table (`০১২৩৪৫৬৭৮৯` -> `0123456789`) was
duplicated independently in `negotiation_node.py`, `grounding_verifier.py`,
and `bengali_calendar.py`. Centralizing it here means a correctness fix
(e.g. handling a Bengali digit variant, or extending the word-number list)
only needs to happen once — the same reasoning `bengali_calendar.py` and
`local_products.py` already document for their own single-source-of-truth
role.

NUMBER_WORDS is reused by both grounding_verifier.py (catching word-form
hallucinated amounts) and negotiation_node.py (catching word-form prices
in LLM-generated reason fragments) — kept here as the single canonical
list so the two don't silently drift apart.
"""

BENGALI_DIGIT_MAP = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
LATIN_DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

NUMBER_WORDS: dict[str, int] = {
    "শূন্য": 0, "এক": 1, "দুই": 2, "তিন": 3, "চার": 4, "পাঁচ": 5, "ছয়": 6, "সাত": 7,
    "আট": 8, "নয়": 9, "দশ": 10, "এগারো": 11, "বারো": 12, "তেরো": 13, "চৌদ্দ": 14,
    "পনেরো": 15, "ষোল": 16, "সতেরো": 17, "আঠারো": 18, "উনিশ": 19, "বিশ": 20,
    "পঁচিশ": 25, "ত্রিশ": 30, "পঁয়ত্রিশ": 35, "চল্লিশ": 40, "পঁয়তাল্লিশ": 45,
    "পঞ্চাশ": 50, "ষাট": 60, "সত্তর": 70, "আশি": 80, "নব্বই": 90,
    "একশো": 100, "দুইশো": 200, "তিনশো": 300, "চারশো": 400, "পাঁচশো": 500,
    "হাজার": 1000, "লাখ": 100000,
}


def to_bengali_digits(value: int | float) -> str:
    """1234 -> ১২৩৪. Rounds floats to the nearest integer for display —
    financial amounts in this codebase are already rounded to paisa
    before display (see ledger_confirm_node._validate_amount)."""
    if isinstance(value, float):
        value = round(value)
    return str(value).translate(BENGALI_DIGIT_MAP)


def to_latin_digits(text: str) -> str:
    """১২৩৪ -> 1234, leaving any non-digit characters untouched."""
    return text.translate(LATIN_DIGIT_MAP)


def parse_bengali_or_latin_number(text: str) -> float | None:
    """Best-effort: extracts and parses the first digit run in `text`
    (Bengali or Latin, comma-separated ok), returning None if nothing
    parses. Does NOT validate range — callers (e.g.
    negotiation_node._extract_amount) apply their own domain-specific
    bounds after calling this, since 'reasonable' differs per agent."""
    import re

    m = re.search(r"[০-৯0-9,]+", text)
    if not m:
        return None
    try:
        return float(to_latin_digits(m.group(0)).replace(",", ""))
    except ValueError:
        return None


def contains_number_word(text: str) -> bool:
    """True if `text` contains any spelled-out Bengali number word — the
    check that closed the original gap in both grounding_verifier.py
    (HIGH-3) and negotiation_node.py (CRIT-1), where a digit-only scan
    missed "পঞ্চাশ" (fifty) entirely since it has no digit glyphs."""
    return any(word in text for word in NUMBER_WORDS)
