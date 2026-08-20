import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from services.orchestrator.nodes import market_predictor_node as node_module


@pytest.mark.asyncio
async def test_cache_hit_skips_llm_call_entirely(monkeypatch):
    async def _fake_trend(block):
        return [
            {"category": "papad", "week": "2026-07-01", "total_amount": 5000},
            {"category": "papad", "week": "2026-06-24", "total_amount": 3000},
        ]

    async def _fake_mandi(district):
        return []

    async def _should_not_be_called(**kwargs):
        raise AssertionError("route_completion should not be called on a cache hit")

    async def _fake_cache_get(key, ttl_seconds=1200):
        return "পাপড়ের চাহিদা বাড়ছে (cached)"

    monkeypatch.setattr(node_module, "block_sales_trend", _fake_trend)
    monkeypatch.setattr(node_module, "fetch_mandi_prices", _fake_mandi)
    monkeypatch.setattr(node_module, "route_completion", _should_not_be_called)
    monkeypatch.setattr(node_module, "get_cached_response", _fake_cache_get)

    result = await node_module.market_predictor_node(
        {"user_profile": {"block": "Balidewanganj"}}
    )
    assert result["outbound_messages"][0]["body"] == "পাপড়ের চাহিদা বাড়ছে (cached)"
    assert "cache_hit" in result["trace"][0]


@pytest.mark.asyncio
async def test_cache_miss_calls_llm_and_writes_cache(monkeypatch):
    async def _fake_trend(block):
        return [
            {"category": "papad", "week": "2026-07-01", "total_amount": 5000},
            {"category": "papad", "week": "2026-06-24", "total_amount": 3000},
        ]

    async def _fake_mandi(district):
        return []

    async def _fake_completion(**kwargs):
        return {
            "text": "পাপড়ের চাহিদা বাড়ছে",
            "model_used": "sarvam-standard",
            "escalated": False,
        }

    written = {}

    async def _fake_cache_get(key, ttl_seconds=1200):
        return None

    async def _fake_cache_set(key, text):
        written["key"] = key
        written["text"] = text

    monkeypatch.setattr(node_module, "block_sales_trend", _fake_trend)
    monkeypatch.setattr(node_module, "fetch_mandi_prices", _fake_mandi)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)
    monkeypatch.setattr(node_module, "get_cached_response", _fake_cache_get)
    monkeypatch.setattr(node_module, "set_cached_response", _fake_cache_set)

    result = await node_module.market_predictor_node(
        {"user_profile": {"block": "Balidewanganj"}}
    )
    assert result["outbound_messages"][0]["body"] == "পাপড়ের চাহিদা বাড়ছে"
    assert written["text"] == "পাপড়ের চাহিদা বাড়ছে"
    assert "market_predictor_node:done" in result["trace"][0]
