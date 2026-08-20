import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
from contextlib import asynccontextmanager

import pytest
from services.orchestrator.model_router import ModelUnavailableError
from services.orchestrator.nodes import ledger_confirm_node as node_module


class _FakeDB:
    def __init__(self, raise_on_commit: Exception | None = None):
        self.added = []
        self.raise_on_commit = raise_on_commit

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        if self.raise_on_commit:
            raise self.raise_on_commit


def _fake_get_db_session(raise_on_commit=None):
    fake_db = _FakeDB(raise_on_commit=raise_on_commit)

    @asynccontextmanager
    async def _ctx():
        yield fake_db

    _ctx.fake_db = fake_db
    return _ctx


_PENDING = {
    "transactions": [{"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"}],
    "overall_confidence": 0.9,
    "raw_transcript": "৩০০ টাকা পাপড় বিক্রি",
    "extracted_by": "sarvam-standard",
}


@pytest.mark.asyncio
async def test_no_pending_entry_resets_with_message():
    result = await node_module.ledger_confirm_node({"raw_input_text": "হ্যাঁ"})
    assert result["pending_ledger_entry"] is None
    assert result["trace"] == ["ledger_confirm_node:no_pending"]


@pytest.mark.asyncio
async def test_exceeding_max_confirmation_turns_discards_entry():
    state = {
        "raw_input_text": "কি বললে",
        "pending_ledger_entry": _PENDING,
        "ledger_confirmation_turns": node_module.MAX_CONFIRMATION_TURNS,
    }
    result = await node_module.ledger_confirm_node(state)
    assert result["pending_ledger_entry"] is None
    assert "বাদ দেওয়া হলো" in result["outbound_messages"][0]["body"]


@pytest.mark.asyncio
async def test_unrecognized_reply_asks_yes_or_no():
    state = {"raw_input_text": "আচ্ছা ঠিক আছে হবে", "pending_ledger_entry": _PENDING}
    result = await node_module.ledger_confirm_node(state)
    assert result["awaiting_confirmation"] is True
    assert "হ্যাঁ" in result["outbound_messages"][0]["body"]


@pytest.mark.asyncio
async def test_affirmative_reply_with_no_user_id_resets_with_message(monkeypatch):
    state = {"raw_input_text": "হ্যাঁ", "pending_ledger_entry": _PENDING}

    result = await node_module.ledger_confirm_node(state)
    assert result["pending_ledger_entry"] is None
    assert result["trace"] == ["ledger_confirm_node:save_failed_no_user_id"]


@pytest.mark.asyncio
async def test_affirmative_reply_saves_and_reports_income_expense_totals(monkeypatch):
    fake_ctx = _fake_get_db_session()
    monkeypatch.setattr("shared.db.session.get_db_session", fake_ctx)

    pending = {
        "transactions": [
            {"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"},
            {"type": "EXPENSE", "amount_inr": 100, "item_bengali": "মশলা"},
        ],
        "overall_confidence": 0.9,
        "raw_transcript": "...",
        "extracted_by": "sarvam-standard",
    }

    state = {
        "raw_input_text": "হ্যাঁ",
        "pending_ledger_entry": pending,
        "user_id": "user-1",
    }
    result = await node_module.ledger_confirm_node(state)

    import unicodedata

    body = unicodedata.normalize("NFC", result["outbound_messages"][0]["body"])
    assert "আয় হয়েছে ₹300" in body
    assert "খরচ হয়েছে ₹100" in body
    assert len(fake_ctx.fake_db.added) == 2


@pytest.mark.asyncio
async def test_affirmative_reply_with_absurd_amount_rejects_before_saving(monkeypatch):
    fake_ctx = _fake_get_db_session()
    monkeypatch.setattr("shared.db.session.get_db_session", fake_ctx)

    pending = {
        "transactions": [
            {
                "type": "INCOME",
                "amount_inr": node_module.MAX_REASONABLE_AMOUNT + 1,
                "item_bengali": "x",
            }
        ],
        "overall_confidence": 0.9,
        "raw_transcript": "...",
        "extracted_by": "sarvam-standard",
    }

    state = {
        "raw_input_text": "হ্যাঁ",
        "pending_ledger_entry": pending,
        "user_id": "user-1",
    }
    result = await node_module.ledger_confirm_node(state)

    assert result["pending_ledger_entry"] is None
    assert result["trace"] == ["ledger_confirm_node:amount_out_of_range"]
    assert len(fake_ctx.fake_db.added) == 0


@pytest.mark.asyncio
async def test_db_commit_failure_resets_with_friendly_message(monkeypatch):
    fake_ctx = _fake_get_db_session(raise_on_commit=RuntimeError("db down"))
    monkeypatch.setattr("shared.db.session.get_db_session", fake_ctx)

    state = {
        "raw_input_text": "হ্যাঁ",
        "pending_ledger_entry": _PENDING,
        "user_id": "user-1",
    }
    result = await node_module.ledger_confirm_node(state)

    assert result["trace"] == ["ledger_confirm_node:db_commit_failed"]


@pytest.mark.asyncio
async def test_negative_reply_discards_entry():
    state = {"raw_input_text": "না", "pending_ledger_entry": _PENDING}
    result = await node_module.ledger_confirm_node(state)
    assert result["pending_ledger_entry"] is None
    assert "বাদ দেওয়া হলো" in result["outbound_messages"][0]["body"]
    assert "declined_by_user" in result["trace"][0]


@pytest.mark.asyncio
async def test_negative_with_digits_triggers_correction_flow(monkeypatch):
    async def _fake(**kwargs):
        return {
            "text": json.dumps(
                {
                    "transactions": [
                        {"type": "INCOME", "amount_inr": 400, "item_bengali": "পাপড়"}
                    ],
                    "confidence": 0.9,
                }
            ),
            "model_used": "sarvam-standard",
            "escalated": False,
        }

    monkeypatch.setattr(node_module, "route_completion", _fake)

    state = {"raw_input_text": "না, ৪০০ টাকা ছিল", "pending_ledger_entry": _PENDING}
    result = await node_module.ledger_confirm_node(state)
    assert result["pending_ledger_entry"]["transactions"][0]["amount_inr"] == 400
    assert result["awaiting_confirmation"] is True


@pytest.mark.asyncio
async def test_reply_containing_digits_is_treated_as_correction_even_without_na(
    monkeypatch,
):
    async def _fake(**kwargs):
        return {
            "text": json.dumps(
                {
                    "transactions": [
                        {"type": "INCOME", "amount_inr": 400, "item_bengali": "পাপড়"}
                    ],
                    "confidence": 0.9,
                }
            ),
            "model_used": "sarvam-standard",
            "escalated": False,
        }

    monkeypatch.setattr(node_module, "route_completion", _fake)

    state = {"raw_input_text": "৪০০ টাকা ছিল", "pending_ledger_entry": _PENDING}
    result = await node_module.ledger_confirm_node(state)
    assert "correction_applied" in result["trace"][0]


@pytest.mark.asyncio
async def test_correction_model_unavailable_asks_to_retry_later(monkeypatch):
    async def _raise(**kwargs):
        raise ModelUnavailableError("down")

    monkeypatch.setattr(node_module, "route_completion", _raise)

    state = {"raw_input_text": "ভুল হয়েছে", "pending_ledger_entry": _PENDING}
    result = await node_module.ledger_confirm_node(state)
    assert "সমস্যা হচ্ছে" in result["outbound_messages"][0]["body"]
    assert (
        "pending_ledger_entry" not in result
        or result.get("pending_ledger_entry") is None
    )


@pytest.mark.asyncio
async def test_correction_malformed_json_asks_to_repeat(monkeypatch):
    async def _fake(**kwargs):
        return {"text": "not json", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    state = {"raw_input_text": "ভুল হয়েছে", "pending_ledger_entry": _PENDING}
    result = await node_module.ledger_confirm_node(state)
    assert "সংশোধন বুঝতে পারলাম না" in result["outbound_messages"][0]["body"]


def test_validate_amount_rejects_negative():
    assert node_module._validate_amount(-1) is None


def test_validate_amount_accepts_normal_value():
    assert node_module._validate_amount(299.999) == 300.0
