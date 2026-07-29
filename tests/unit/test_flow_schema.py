import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.whatsapp.flow_schema import (
    validate_ledger_confirm_payload,
    validate_scheme_eligibility_payload,
)


def test_valid_confirmation_choice_passes():
    assert validate_ledger_confirm_payload({"confirmation_choice": "confirm_save"}) == "confirm_save"


def test_unknown_choice_value_rejected():
    assert validate_ledger_confirm_payload({"confirmation_choice": "delete_everything"}) is None


def test_extra_unexpected_key_rejected_even_with_valid_choice():
    assert validate_ledger_confirm_payload(
        {"confirmation_choice": "confirm_save", "amount_inr": 999999}
    ) is None


def test_non_dict_payload_rejected():
    assert validate_ledger_confirm_payload("confirm_save") is None
    assert validate_ledger_confirm_payload(None) is None


def test_non_string_choice_rejected():
    assert validate_ledger_confirm_payload({"confirmation_choice": 123}) is None


def test_missing_key_rejected():
    assert validate_ledger_confirm_payload({}) is None


def test_scheme_eligibility_valid_payload_passes():
    payload = {
        "scheme_name": "lakshmir_bhandar", "age": "35",
        "has_swasthya_sathi": "yes", "is_govt_employee": "no",
    }
    result = validate_scheme_eligibility_payload(payload)
    assert result is not None
    assert result["age"] == 35


def test_scheme_eligibility_rejects_out_of_range_age():
    payload = {
        "scheme_name": "lakshmir_bhandar", "age": "999",
        "has_swasthya_sathi": "yes", "is_govt_employee": "no",
    }
    assert validate_scheme_eligibility_payload(payload) is None


def test_scheme_eligibility_rejects_non_yes_no_bool_field():
    payload = {
        "scheme_name": "lakshmir_bhandar", "age": "35",
        "has_swasthya_sathi": "maybe", "is_govt_employee": "no",
    }
    assert validate_scheme_eligibility_payload(payload) is None
