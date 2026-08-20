import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.orchestrator.graph import (
    _interactive_payload,
    _route_after_intent,
    _route_after_price_chat,
    _route_after_profile_load,
)


def test_interactive_payload_parses_json_for_interactive_messages():
    state = {
        "last_message_type": "interactive",
        "raw_input_text": '{"confirmation_choice": "confirm_save"}',
    }
    assert _interactive_payload(state) == {"confirmation_choice": "confirm_save"}


def test_interactive_payload_empty_for_non_interactive_messages():
    state = {
        "last_message_type": "text",
        "raw_input_text": '{"confirmation_choice": "confirm_save"}',
    }
    assert _interactive_payload(state) == {}


def test_interactive_payload_empty_for_malformed_json():
    state = {"last_message_type": "interactive", "raw_input_text": "not json"}
    assert _interactive_payload(state) == {}


def test_new_user_routes_to_onboarding():
    assert _route_after_profile_load({"is_new_user": True}) == "onboarding"


def test_incomplete_onboarding_routes_to_onboarding():
    state = {"is_new_user": False, "onboarding_step": "AWAIT_BLOCK"}
    assert _route_after_profile_load(state) == "onboarding"


def test_completed_onboarding_does_not_route_back_to_onboarding():
    state = {
        "is_new_user": False,
        "onboarding_step": "DONE",
        "last_message_type": "text",
    }
    assert _route_after_profile_load(state) == "classify_intent"


def test_awaiting_confirmation_with_flow_tap_routes_to_flow_node():
    state = {
        "awaiting_confirmation": True,
        "last_message_type": "interactive",
        "raw_input_text": '{"confirmation_choice": "confirm_save"}',
    }
    assert _route_after_profile_load(state) == "ledger_confirm_flow"


def test_awaiting_confirmation_with_plain_text_routes_to_text_node():
    state = {
        "awaiting_confirmation": True,
        "last_message_type": "text",
        "raw_input_text": "হ্যাঁ",
    }
    assert _route_after_profile_load(state) == "ledger_confirm"


def test_awaiting_confirmation_with_unrelated_interactive_payload_falls_back_to_text_node():
    state = {
        "awaiting_confirmation": True,
        "last_message_type": "interactive",
        "raw_input_text": '{"scheme_name": "lakshmir_bhandar"}',
    }
    assert _route_after_profile_load(state) == "ledger_confirm"


def test_awaiting_negotiation_routes_to_negotiation():
    state = {"awaiting_negotiation": True, "last_message_type": "text"}
    assert _route_after_profile_load(state) == "negotiation"


def test_awaiting_price_chat_routes_to_price_chat():
    state = {"awaiting_price_chat": True, "last_message_type": "text"}
    assert _route_after_profile_load(state) == "price_chat"


def test_confirmation_takes_priority_over_negotiation_and_price_chat():
    state = {
        "awaiting_confirmation": True,
        "awaiting_negotiation": True,
        "awaiting_price_chat": True,
        "last_message_type": "text",
    }
    assert _route_after_profile_load(state) == "ledger_confirm"


def test_image_with_no_pending_flags_routes_to_catalog():
    state = {"last_message_type": "image"}
    assert _route_after_profile_load(state) == "catalog"


def test_plain_text_with_no_pending_flags_routes_to_classify_intent():
    state = {"last_message_type": "text"}
    assert _route_after_profile_load(state) == "classify_intent"


def test_route_after_intent_covers_every_feature():
    expected = {
        "LEDGER": "ledger",
        "LEDGER_REPORT": "ledger_report",
        "MARKET": "market",
        "PRICING": "pricing",
        "NEGOTIATION": "negotiation",
        "PRICE_CHAT": "price_chat",
        "IDLE": "unhandled",
        "UNKNOWN_FEATURE": "unhandled",
    }
    for feature, expected_node in expected.items():
        assert _route_after_intent({"active_feature": feature}) == expected_node


def test_price_chat_still_open_ends_the_turn():
    state = {"awaiting_price_chat": True, "agreed_price": None}
    assert _route_after_price_chat(state) == "end"


def test_price_chat_agreed_but_still_marked_awaiting_ends_the_turn():
    state = {"awaiting_price_chat": True, "agreed_price": 250.0}
    assert _route_after_price_chat(state) == "end"


def test_price_chat_finalized_hands_off_to_catalog():
    state = {"awaiting_price_chat": False, "agreed_price": 250.0}
    assert _route_after_price_chat(state) == "catalog"


def test_price_chat_never_started_ends_the_turn():
    state = {}
    assert _route_after_price_chat(state) == "end"
