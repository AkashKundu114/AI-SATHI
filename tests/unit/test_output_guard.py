import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.guardrails.output_guard import (
    MAX_OUTPUT_CHARS,
    enforce_output_guard,
    validate_output,
)


def test_normal_bengali_reply_is_safe():
    is_safe, reason = validate_output("আমি হিসাব রাখতে সাহায্য করতে পারি।")
    assert is_safe is True
    assert reason is None


def test_openai_style_secret_key_flagged():
    is_safe, reason = validate_output(
        "here is the key sk-abcdefghijklmnopqrstuvwxyz123456"
    )
    assert is_safe is False
    assert reason == "contains_secret_shaped_string"


def test_bearer_token_flagged():
    is_safe, reason = validate_output(
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890"
    )
    assert is_safe is False


def test_aadhaar_shaped_number_flagged():
    is_safe, reason = validate_output("আপনার আধার নম্বর 1234 5678 9012")
    assert is_safe is False
    assert reason == "contains_sensitive_pii"


def test_pan_shaped_string_flagged():
    is_safe, reason = validate_output("PAN: ABCDE1234F")
    assert is_safe is False


def test_otp_mention_flagged():
    is_safe, reason = validate_output("Your OTP: 123456")
    assert is_safe is False


def test_url_flagged():
    is_safe, reason = validate_output("বিস্তারিত জানতে দেখুন https://example.com/scheme")
    assert is_safe is False
    assert reason == "contains_unexpected_url"


def test_sql_statement_flagged():
    is_safe, reason = validate_output("SELECT * FROM users WHERE id = 1")
    assert is_safe is False
    assert reason == "contains_sql_or_stack_trace"


def test_stack_trace_flagged():
    is_safe, reason = validate_output(
        'Traceback (most recent call last):\n  File "app.py", line 10'
    )
    assert is_safe is False


def test_over_length_output_flagged():
    is_safe, reason = validate_output("ক" * (MAX_OUTPUT_CHARS + 1))
    assert is_safe is False
    assert reason == "exceeds_max_output_chars"


def test_empty_output_is_safe():
    is_safe, reason = validate_output("")
    assert is_safe is True


def test_enforce_output_guard_returns_original_when_safe():
    result = enforce_output_guard("ভালো উত্তর", fallback="fallback")
    assert result == "ভালো উত্তর"


def test_enforce_output_guard_returns_fallback_when_unsafe():
    result = enforce_output_guard(
        "sk-leakedsecretkeyabcdefghijklmnop", fallback="নিরাপদ উত্তর"
    )
    assert result == "নিরাপদ উত্তর"
