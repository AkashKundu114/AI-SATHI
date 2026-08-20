import json
import logging

from shared.security.audit_log import log_security_event
from shared.security.input_sanitizer import sanitize_text_input, validate_phone_number


def test_log_security_event(caplog):
    with caplog.at_level(logging.WARNING, logger="security_audit"):
        log_security_event(
            "test_event",
            source_ip="127.0.0.1",
            whatsapp_number="+919876543210",
            details={"reason": "unit_test"},
        )

    assert len(caplog.records) == 1
    record_text = caplog.records[0].message
    assert "SECURITY_EVENT:" in record_text

    json_part = record_text.split("SECURITY_EVENT: ")[1]
    parsed = json.loads(json_part)
    assert parsed["event_type"] == "test_event"
    assert parsed["source_ip"] == "127.0.0.1"
    assert parsed["whatsapp_number"] == "+919876543210"
    assert parsed["details"]["reason"] == "unit_test"


def test_sanitize_text_input_edge_cases():
    assert sanitize_text_input("") == ""
    assert sanitize_text_input(None) == ""

    text_with_control = "Line 1\x00\x01\x02\nLine 2"
    clean = sanitize_text_input(text_with_control)
    assert "\x00" not in clean
    assert "\x01" not in clean
    assert "Line 1" in clean
    assert "Line 2" in clean


def test_validate_phone_number_strict():
    assert validate_phone_number("+919876543210") is True
    assert validate_phone_number("+15551757739") is True
    assert validate_phone_number("1264362833422500") is True

    assert validate_phone_number("") is False
    assert validate_phone_number(None) is False
    assert validate_phone_number("abc") is False
    assert validate_phone_number("SELECT * FROM users") is False
    assert validate_phone_number("+000000000000000000000") is False
