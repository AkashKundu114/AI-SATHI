import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from services.orchestrator.nodes import market_predictor_node as node_module
from services.orchestrator.model_router import ModelUnavailableError


@pytest.mark.asyncio
async def test_no_block_in_profile_asks_to_update_profile():
    result = await node_module.market_predictor_node({"user_profile": {}})
    assert result["trace"] == ["market_predictor_node:no_block"]


@pytest.mark.asyncio
async def test_no_user_profile_at_all_asks_to_update_profile():
    result = await node_module.market_predictor_node({})
    assert result["trace"] == ["market_predictor_node:no_block"]


@pytest.mark.asyncio
async def test_build_report_failure_degrades_to_friendly_message(monkeypatch):
    async def _raise(block):
        raise RuntimeError("db down")

    monkeypatch.setattr(node_module, "block_sales_trend", _raise)

    result = await node_module.market_predictor_node({"user_profile": {"block": "Balidewanganj"}})
    assert result["trace"] == ["market_predictor_node:build_report_failed"]


@pytest.mark.asyncio
async def test_no_rising_or_saturated_products_reports_insufficient_data(monkeypatch):
    async def _fake_trend(block):
        return []

    async def _fake_mandi(district):
        return []

    monkeypatch.setattr(node_module, "block_sales_trend", _fake_trend)
    monkeypatch.setattr(node_module, "fetch_mandi_prices", _fake_mandi)
    monkeypatch.setattr(
        node_module,
        "get_context_for_agents",
        lambda **kwargs: {"season": None, "upcoming_festivals": [], "upcoming_district_melas": []},
    )
    monkeypatch.setattr(node_module, "crops_at_harvest", lambda month: [])

    result = await node_module.market_predictor_node({"user_profile": {"block": "Balidewanganj"}})
    assert result["trace"] == ["market_predictor_node:insufficient_data"]


@pytest.mark.asyncio
async def test_happy_path_phrases_rising_and_saturated_products(monkeypatch):
    async def _fake_trend(block):
        return [
            {"category": "papad", "week": "2026-07-01", "total_amount": 5000},
            {"category": "papad", "week": "2026-06-24", "total_amount": 3000},
            {"category": "pickle", "week": "2026-07-01", "total_amount": 2000},
            {"category": "pickle", "week": "2026-06-24", "total_amount": 4000},
        ]

    async def _fake_mandi(district):
        return []

    async def _fake_completion(**kwargs):
        assert "papad" in kwargs["prompt"]
        return {"text": "পাপড়ের চাহিদা বাড়ছে, আচারের সরবরাহ বেশি।", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "block_sales_trend", _fake_trend)
    monkeypatch.setattr(node_module, "fetch_mandi_prices", _fake_mandi)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.market_predictor_node({"user_profile": {"block": "Balidewanganj"}})
    assert result["market_report"]["rising"] == ["papad"]
    assert result["market_report"]["saturated"] == ["pickle"]
    assert result["outbound_messages"][0]["body"] == "পাপড়ের চাহিদা বাড়ছে, আচারের সরবরাহ বেশি।"


@pytest.mark.asyncio
async def test_model_unavailable_during_phrasing_uses_plain_fallback(monkeypatch):
    async def _fake_trend(block):
        return [
            {"category": "papad", "week": "2026-07-01", "total_amount": 5000},
            {"category": "papad", "week": "2026-06-24", "total_amount": 3000},
        ]

    async def _fake_mandi(district):
        return []

    async def _raise(**kwargs):
        raise ModelUnavailableError("down")

    monkeypatch.setattr(node_module, "block_sales_trend", _fake_trend)
    monkeypatch.setattr(node_module, "fetch_mandi_prices", _fake_mandi)
    monkeypatch.setattr(node_module, "route_completion", _raise)

    result = await node_module.market_predictor_node({"user_profile": {"block": "Balidewanganj"}})
    assert "papad" in result["outbound_messages"][0]["body"]  


@pytest.mark.asyncio
async def test_mandi_price_lookup_failure_does_not_block_the_report(monkeypatch):
    async def _fake_trend(block):
        return [
            {"category": "papad", "week": "2026-07-01", "total_amount": 5000},
            {"category": "papad", "week": "2026-06-24", "total_amount": 3000},
        ]

    async def _raise_mandi(district):
        raise RuntimeError("agmarknet down")

    async def _fake_completion(**kwargs):
        return {"text": "ঠিক আছে", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "block_sales_trend", _fake_trend)
    monkeypatch.setattr(node_module, "fetch_mandi_prices", _raise_mandi)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.market_predictor_node({"user_profile": {"block": "Balidewanganj"}})
    assert result["market_report"]["mandi_prices"] == []
