import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from services.orchestrator.nodes import pricing_node as node_module
from services.orchestrator.model_router import ModelUnavailableError


class _FakeResult:
    def __init__(self, profile):
        self._profile = profile

    def scalar_one_or_none(self):
        return self._profile


def _fake_get_db_session(profile=None):
    @asynccontextmanager
    async def _ctx():
        class _DB:
            async def execute(self, *a, **kw):
                return _FakeResult(profile)
        yield _DB()
    return _ctx


def _profile(**overrides):
    base = dict(production_cost=100.0, preferred_margin=0.30, minimum_price=None, product_type="papad")
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_no_user_id_returns_no_profile_message():
    result = await node_module.pricing_node({})
    assert result["outbound_messages"][0]["body"] == node_module.NO_PROFILE_MSG
    assert result["trace"] == ["pricing_node:no_user"]


@pytest.mark.asyncio
async def test_no_seller_profile_row_returns_no_profile_message(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=None))
    result = await node_module.pricing_node({"user_id": "u1"})
    assert result["trace"] == ["pricing_node:no_profile"]


@pytest.mark.asyncio
async def test_profile_with_no_production_cost_returns_no_profile_message(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile(production_cost=None)))
    result = await node_module.pricing_node({"user_id": "u1"})
    assert result["trace"] == ["pricing_node:no_profile"]


@pytest.mark.asyncio
async def test_negative_cost_with_no_minimum_price_refuses_rather_than_use_zero_floor(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile(production_cost=-500, minimum_price=None)))
    result = await node_module.pricing_node({"user_id": "u1"})
    assert result["trace"] == ["pricing_node:non_positive_floor"]


@pytest.mark.asyncio
async def test_happy_path_no_block_no_market_data(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile()))

    async def _fake_completion(**kwargs):
        return {"text": "ভালো দাম!", "model_used": "sarvam-advanced", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.pricing_node({"user_id": "u1"})
    assert "₹130" in result["outbound_messages"][0]["body"]  # 100 * 1.30
    assert result["market_report"] is None


@pytest.mark.asyncio
async def test_happy_path_with_block_pulls_market_average(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile()))

    async def _fake_trend(block):
        return [{"category": "papad", "total_amount": 1000.0}, {"category": "papad", "total_amount": 2000.0}]

    async def _fake_completion(**kwargs):
        return {"text": "বাজারের গড় দাম অনুযায়ী ভালো।", "model_used": "sarvam-advanced", "escalated": False}

    monkeypatch.setattr(node_module, "block_sales_trend", _fake_trend)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.pricing_node({"user_id": "u1", "user_profile": {"block": "Balidewanganj"}})
    assert result["market_report"]["market_avg"] == 1500.0


@pytest.mark.asyncio
async def test_market_trend_lookup_failure_does_not_crash_pricing(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile()))

    async def _raise(block):
        raise RuntimeError("db down")

    async def _fake_completion(**kwargs):
        return {"text": "ঠিক আছে", "model_used": "sarvam-advanced", "escalated": False}

    monkeypatch.setattr(node_module, "block_sales_trend", _raise)
    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.pricing_node({"user_id": "u1", "user_profile": {"block": "Balidewanganj"}})
    assert result["market_report"] is None 


@pytest.mark.asyncio
async def test_model_unavailable_during_phrasing_still_returns_price(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile()))

    async def _raise(**kwargs):
        raise ModelUnavailableError("down")

    monkeypatch.setattr(node_module, "route_completion", _raise)

    result = await node_module.pricing_node({"user_id": "u1"})
    assert "₹130" in result["outbound_messages"][0]["body"]


@pytest.mark.asyncio
async def test_minimum_price_overrides_lower_margin_floor(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile(production_cost=100, preferred_margin=0.10, minimum_price=180)))

    async def _fake_completion(**kwargs):
        return {"text": "ঠিক আছে", "model_used": "sarvam-advanced", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake_completion)

    result = await node_module.pricing_node({"user_id": "u1"})
    assert "₹180" in result["outbound_messages"][0]["body"]
