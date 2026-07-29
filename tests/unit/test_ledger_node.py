import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import pytest

from services.orchestrator.nodes import ledger_node as node_module
from services.orchestrator.model_router import ModelUnavailableError


def _fake_completion_result(payload: dict, model_used: str = "sarvam-standard") -> dict:
    return {"text": json.dumps(payload, ensure_ascii=False), "model_used": model_used, "escalated": False}


@pytest.mark.asyncio
async def test_model_unavailable_returns_friendly_message(monkeypatch):
    async def _raise(**kwargs):
        raise ModelUnavailableError("down")

    monkeypatch.setattr(node_module, "route_completion", _raise)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "৩০০ টাকা পাপড় বিক্রি করেছি"})
    assert result["outbound_messages"][0]["body"] == node_module.MODEL_DOWN_MESSAGE
    assert result["awaiting_confirmation"] is False


@pytest.mark.asyncio
async def test_malformed_json_treated_as_zero_confidence_and_clarifies(monkeypatch):
    async def _fake(**kwargs):
        return {"text": "not valid json", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "কিছু একটা"})
    assert "পরিষ্কার হলো না" in result["outbound_messages"][0]["body"]
    assert result["pending_ledger_entry"] is None


@pytest.mark.asyncio
async def test_low_confidence_extraction_asks_to_clarify(monkeypatch):
    async def _fake(**kwargs):
        return _fake_completion_result({"transactions": [{"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"}], "confidence": 0.3})

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "৩০০ টাকা পাপড় বিক্রি"})
    assert result["pending_ledger_entry"] is None
    assert result["awaiting_confirmation"] is False


@pytest.mark.asyncio
async def test_empty_transactions_list_asks_to_clarify_even_with_high_confidence(monkeypatch):
    async def _fake(**kwargs):
        return _fake_completion_result({"transactions": [], "confidence": 0.95})

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "আজ কিছু হয়নি"})
    assert result["pending_ledger_entry"] is None


@pytest.mark.asyncio
async def test_happy_path_builds_confirmation_and_sets_pending_entry(monkeypatch):
    async def _fake(**kwargs):
        return _fake_completion_result({
            "transactions": [
                {"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"},
                {"type": "EXPENSE", "amount_inr": 100, "item_bengali": "মশলা"},
            ],
            "confidence": 0.9,
        })

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "৩০০ টাকা পাপড় বিক্রি করেছি, ১০০ টাকা মশলা কিনেছি"})
    assert result["awaiting_confirmation"] is True
    assert result["ledger_confirmation_turns"] == 0
    assert len(result["pending_ledger_entry"]["transactions"]) == 2
    body = result["outbound_messages"][0]["body"]
    assert "৩০০" in body and "১০০" in body
    assert "লাভ: ₹২০০" in body


@pytest.mark.asyncio
async def test_strips_markdown_json_fences_before_parsing(monkeypatch):
    async def _fake(**kwargs):
        return {"text": '```json\n{"transactions": [{"type": "INCOME", "amount_inr": 50, "item_bengali": "মুড়ি"}], "confidence": 0.9}\n```',
                "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "৫০ টাকা মুড়ি বিক্রি"})
    assert result["pending_ledger_entry"] is not None
    assert result["pending_ledger_entry"]["transactions"][0]["amount_inr"] == 50


@pytest.mark.asyncio
async def test_high_correction_rate_user_gets_a_stricter_confidence_floor(monkeypatch):
    captured = {}

    async def _fake(**kwargs):
        captured["confidence_floor"] = kwargs["confidence_floor"]
        return _fake_completion_result({"transactions": [{"type": "INCOME", "amount_inr": 100, "item_bengali": "x"}], "confidence": 0.99})

    monkeypatch.setattr(node_module, "route_completion", _fake)

    profile = {"ledger_correction_rate": 1.0} 
    await node_module.ledger_extract_node({"raw_input_transcript": "১০০ টাকা বিক্রি", "user_profile": profile})
    assert captured["confidence_floor"] > node_module.BASE_CONFIDENCE_FLOOR


@pytest.mark.asyncio
async def test_no_user_profile_uses_base_confidence_floor(monkeypatch):
    captured = {}

    async def _fake(**kwargs):
        captured["confidence_floor"] = kwargs["confidence_floor"]
        return _fake_completion_result({"transactions": [{"type": "INCOME", "amount_inr": 100, "item_bengali": "x"}], "confidence": 0.99})

    monkeypatch.setattr(node_module, "route_completion", _fake)

    await node_module.ledger_extract_node({"raw_input_transcript": "১০০ টাকা বিক্রি"})
    assert captured["confidence_floor"] == node_module.BASE_CONFIDENCE_FLOOR


@pytest.mark.asyncio
async def test_code_mixed_transcript_triggers_translation_before_extraction(monkeypatch):
    calls = {"translate": 0}

    async def _fake_translate(text, target_lang):
        calls["translate"] += 1
        return {"text": "আজ পাপড় তিনশো টাকায় বিক্রি করেছি", "model_used": "sarvam-translate"}

    async def _fake_completion(**kwargs):
        assert kwargs["prompt"] == "আজ পাপড় তিনশো টাকায় বিক্রি করেছি"  # translated text was used
        return _fake_completion_result({"transactions": [{"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"}], "confidence": 0.9})

    monkeypatch.setattr(node_module, "route_translation", _fake_translate)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "aj papad tinsho taka bikri korechi"})
    assert calls["translate"] == 1
    assert result["pending_ledger_entry"]["raw_transcript"] == "আজ পাপড় তিনশো টাকায় বিক্রি করেছি"


@pytest.mark.asyncio
async def test_pure_bengali_transcript_never_calls_translation(monkeypatch):
    async def _should_not_be_called(text, target_lang):
        raise AssertionError("translation should not be called for pure Bengali input")

    async def _fake_completion(**kwargs):
        return _fake_completion_result({"transactions": [{"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"}], "confidence": 0.9})

    monkeypatch.setattr(node_module, "route_translation", _should_not_be_called)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "আজ পাপড় তিনশো টাকায় বিক্রি করেছি"})
    assert result["pending_ledger_entry"] is not None


@pytest.mark.asyncio
async def test_translation_failure_falls_back_to_raw_transcript(monkeypatch):
    async def _fake_translate(text, target_lang):
        raise ModelUnavailableError("translation down")

    async def _fake_completion(**kwargs):
        assert kwargs["prompt"] == "aj papad tinsho taka bikri korechi"  # raw text used, untranslated
        return _fake_completion_result({"transactions": [{"type": "INCOME", "amount_inr": 300, "item_bengali": "পাপড়"}], "confidence": 0.9})

    monkeypatch.setattr(node_module, "route_translation", _fake_translate)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "aj papad tinsho taka bikri korechi"})
    assert result["pending_ledger_entry"] is not None
