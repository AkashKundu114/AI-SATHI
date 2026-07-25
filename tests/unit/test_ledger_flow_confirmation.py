import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.orchestrator.nodes import ledger_node


_SAMPLE_PENDING = {
    "transactions": [
        {"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"},
        {"type": "EXPENSE", "amount_inr": 100, "item_bengali": "মশলা"},
    ],
    "overall_confidence": 0.9,
    "raw_transcript": "আজ ৩০০ টাকা পাপড় বিক্রি করেছি, ১০০ টাকা মশলা কিনেছি",
    "extracted_by": "sarvam-standard",
}


class _FakeSettingsNoFlow:
    wa_ledger_confirm_flow_id = ""


class _FakeSettingsWithFlow:
    wa_ledger_confirm_flow_id = "123456789"


def test_confirmation_lines_use_bengali_digits():
    income, expense, net = ledger_node._confirmation_lines(_SAMPLE_PENDING)
    assert "৩০০" in income
    assert "১০০" in expense
    assert "২০০" in net  # 300 - 100
    # No stray Latin digits should appear in a Bengali-digit line
    assert not any(ch.isdigit() for ch in income if ch not in "০১২৩৪৫৬৭৮৯")


def test_falls_back_to_text_when_flow_not_configured(monkeypatch):
    monkeypatch.setattr(ledger_node, "get_settings", lambda: _FakeSettingsNoFlow())
    msg = ledger_node._build_confirmation_message(_SAMPLE_PENDING, _SAMPLE_PENDING["raw_transcript"])
    assert msg["type"] == "text"
    assert "৩০০" in msg["body"]
    assert "ঠিক আছে?" in msg["body"]


def test_sends_flow_when_configured(monkeypatch):
    monkeypatch.setattr(ledger_node, "get_settings", lambda: _FakeSettingsWithFlow())
    msg = ledger_node._build_confirmation_message(_SAMPLE_PENDING, _SAMPLE_PENDING["raw_transcript"])
    assert msg["type"] == "flow"
    assert msg["flow_id"] == "123456789"
    assert msg["screen_id"] == "REVIEW_ENTRY"
    assert "৩০০" in msg["screen_data"]["income_lines"]
    assert "১০০" in msg["screen_data"]["expense_lines"]


def test_flow_screen_data_handles_income_only_entry(monkeypatch):
    monkeypatch.setattr(ledger_node, "get_settings", lambda: _FakeSettingsWithFlow())
    income_only = {**_SAMPLE_PENDING, "transactions": [_SAMPLE_PENDING["transactions"][0]]}
    msg = ledger_node._build_confirmation_message(income_only, income_only["raw_transcript"])
    assert msg["screen_data"]["expense_lines"] == "কোনো খরচ নেই এই এন্ট্রিতে"


def test_legacy_build_confirmation_alias_still_works():
    # ledger_confirm_node.py's correction loop calls _build_confirmation by
    # name directly — must keep working unchanged after this refactor.
    text = ledger_node._build_confirmation(_SAMPLE_PENDING)
    assert "৩০০" in text
    assert "ঠিক আছে?" in text
