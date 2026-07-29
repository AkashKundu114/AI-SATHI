from shared.security.input_sanitizer import sanitize_text_input, validate_phone_number


def test_sanitize_text_input_strips_control_characters():
    dirty = "Hello\x00 World\x07!"
    clean = sanitize_text_input(dirty)
    assert clean == "Hello World!"


def test_sanitize_text_input_truncates_length():
    long_text = "a" * 3000
    clean = sanitize_text_input(long_text, max_chars=100)
    assert len(clean) == 100


def test_validate_phone_number_e164():
    assert validate_phone_number("+919876543210") is True
    assert validate_phone_number("15551757739") is True
    assert validate_phone_number("invalid_phone") is False
    assert validate_phone_number("<script>alert(1)</script>") is False
