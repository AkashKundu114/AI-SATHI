import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.pdf_service.generator import _months_of_history
from shared.i18n.bengali_numbers import (
    contains_number_word,
    parse_bengali_or_latin_number,
    to_bengali_digits,
    to_latin_digits,
)


def test_to_bengali_digits_basic():
    assert to_bengali_digits(1234) == "১২৩৪"


def test_to_bengali_digits_rounds_floats():
    assert to_bengali_digits(199.6) == "২০০"


def test_to_latin_digits_basic():
    assert to_latin_digits("১২৩৪") == "1234"


def test_to_latin_digits_leaves_non_digits_untouched():
    assert to_latin_digits("₹১২৩ টাকা") == "₹123 টাকা"


def test_parse_bengali_or_latin_number_bengali():
    assert parse_bengali_or_latin_number("৳৫০০ দিচ্ছি") == 500.0


def test_parse_bengali_or_latin_number_latin_with_comma():
    assert parse_bengali_or_latin_number("₹1,200 দেবে") == 1200.0


def test_parse_bengali_or_latin_number_none_when_absent():
    assert parse_bengali_or_latin_number("সে রাজি না") is None


def test_contains_number_word_true_for_spelled_out():
    assert contains_number_word("পঞ্চাশ টাকা হলে রাজি") is True


def test_contains_number_word_false_for_clean_text():
    assert contains_number_word("ভালো মানের পণ্য") is False


def test_months_of_history_none_when_no_entries():
    assert _months_of_history(None, date(2026, 7, 1)) == 0


def test_months_of_history_same_month_counts_as_one():
    assert _months_of_history(datetime(2026, 7, 5), date(2026, 7, 31)) == 1


def test_months_of_history_counts_inclusive_span():
    assert _months_of_history(datetime(2026, 1, 20), date(2026, 3, 31)) == 3


def test_months_of_history_never_negative():
    assert _months_of_history(datetime(2026, 12, 1), date(2026, 1, 1)) == 0
