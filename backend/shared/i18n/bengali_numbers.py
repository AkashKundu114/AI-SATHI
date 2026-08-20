from __future__ import annotations

BENGALI_DIGIT_MAP = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
LATIN_DIGIT_MAP = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

NUMBER_WORDS: dict[str, int] = {
    "শূন্য": 0,
    "এক": 1,
    "দুই": 2,
    "তিন": 3,
    "চার": 4,
    "পাঁচ": 5,
    "ছয়": 6,
    "সাত": 7,
    "আট": 8,
    "নয়": 9,
    "দশ": 10,
    "এগারো": 11,
    "বারো": 12,
    "তেরো": 13,
    "চৌদ্দ": 14,
    "পনেরো": 15,
    "ষোল": 16,
    "সতেরো": 17,
    "আঠারো": 18,
    "উনিশ": 19,
    "বিশ": 20,
    "পঁচিশ": 25,
    "ত্রিশ": 30,
    "পঁয়ত্রিশ": 35,
    "চল্লিশ": 40,
    "পঁয়তাল্লিশ": 45,
    "পঞ্চাশ": 50,
    "ষাট": 60,
    "সত্তর": 70,
    "আশি": 80,
    "নব্বই": 90,
    "একশো": 100,
    "দুইশো": 200,
    "তিনশো": 300,
    "চারশো": 400,
    "পাঁচশো": 500,
    "হাজার": 1000,
    "লাখ": 100000,
}


def to_bengali_digits(value: int | float) -> str:
    if isinstance(value, float):
        value = round(value)
    return str(value).translate(BENGALI_DIGIT_MAP)


def to_latin_digits(text: str) -> str:
    return text.translate(LATIN_DIGIT_MAP)


def parse_bengali_or_latin_number(text: str) -> float | None:
    import re

    m = re.search(r"[০-৯0-9,]+", text)
    if not m:
        return None
    try:
        return float(to_latin_digits(m.group(0)).replace(",", ""))
    except ValueError:
        return None


def contains_number_word(text: str) -> bool:
    return any(word in text for word in NUMBER_WORDS)
