import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import pytest

from services.orchestrator.nodes import intent_router as node_module
from services.orchestrator.model_router import ModelUnavailableError


@pytest.mark.asyncio
async def test_report_keyword_routes_without_calling_model(monkeypatch):
    async def _should_not_be_called(**kwargs):
        raise AssertionError("model should not be called when a keyword matches")

    monkeypatch.setattr(node_module, "route_completion", _should_not_be_called)

    result = await node_module.classify_intent({"raw_input_text": "এই মাসের রিপোর্ট দাও"})
    assert result["active_feature"] == "LEDGER_REPORT"


@pytest.mark.asyncio
async def test_financial_keyword_routes_to_ledger(monkeypatch):
    async def _should_not_be_called(**kwargs):
        raise AssertionError("model should not be called when a keyword matches")

    monkeypatch.setattr(node_module, "route_completion", _should_not_be_called)

    result = await node_module.classify_intent({"raw_input_text": "৩০০ টাকা পাপড় বিক্রি করেছি"})
    assert result["active_feature"] == "LEDGER"


@pytest.mark.asyncio
async def test_negotiation_keyword_checked_before_pricing_keyword():
    result = await node_module.classify_intent({"raw_input_text": "দরদাম করতে চাই"})
    assert result["active_feature"] == "NEGOTIATION"


@pytest.mark.asyncio
async def test_market_keyword_routes_to_market():
    result = await node_module.classify_intent({"raw_input_text": "এই মাসে কি বানাবো"})
    assert result["active_feature"] == "MARKET"


@pytest.mark.asyncio
async def test_pricing_keyword_routes_to_pricing():
    result = await node_module.classify_intent({"raw_input_text": "দাম কত হবে"})
    assert result["active_feature"] == "PRICING"


@pytest.mark.asyncio
async def test_empty_input_returns_idle_without_calling_model(monkeypatch):
    async def _should_not_be_called(**kwargs):
        raise AssertionError("model should not be called for empty input")

    monkeypatch.setattr(node_module, "route_completion", _should_not_be_called)

    result = await node_module.classify_intent({"raw_input_text": ""})
    assert result["active_feature"] == "IDLE"
    assert result["trace"] == ["intent_router:empty_input"]


@pytest.mark.asyncio
async def test_no_keyword_match_falls_through_to_model(monkeypatch):
    async def _fake(**kwargs):
        return {"text": json.dumps({"feature": "PRICING", "confidence": 0.9}), "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.classify_intent({"raw_input_text": "কিছু একটা অস্পষ্ট কথা"})
    assert result["active_feature"] == "PRICING"


@pytest.mark.asyncio
async def test_model_returns_unknown_feature_maps_to_idle(monkeypatch):
    async def _fake(**kwargs):
        return {"text": json.dumps({"feature": "UNKNOWN", "confidence": 0.3}), "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.classify_intent({"raw_input_text": "কিছু একটা অস্পষ্ট কথা"})
    assert result["active_feature"] == "IDLE"


@pytest.mark.asyncio
async def test_model_returns_malformed_json_maps_to_idle(monkeypatch):
    async def _fake(**kwargs):
        return {"text": "not json at all", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.classify_intent({"raw_input_text": "কিছু একটা অস্পষ্ট কথা"})
    assert result["active_feature"] == "IDLE"


@pytest.mark.asyncio
async def test_model_unavailable_falls_back_to_idle_not_a_crash(monkeypatch):
    async def _raise(**kwargs):
        raise ModelUnavailableError("down")

    monkeypatch.setattr(node_module, "route_completion", _raise)

    result = await node_module.classify_intent({"raw_input_text": "কিছু একটা অস্পষ্ট কথা"})
    assert result["active_feature"] == "IDLE"
    assert result["trace"] == ["intent_router:model_unavailable"]


@pytest.mark.asyncio
async def test_reads_transcript_field_when_text_field_absent():
    result = await node_module.classify_intent({"raw_input_transcript": "রিপোর্ট চাই"})
    assert result["active_feature"] == "LEDGER_REPORT"
