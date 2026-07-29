import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from services.orchestrator.nodes import negotiation_node as node_module
from services.orchestrator.model_router import ModelUnavailableError


def _fake_get_db_session(profile=None):
    @asynccontextmanager
    async def _ctx():
        class _Result:
            def scalar_one_or_none(self):
                return profile

        class _DB:
            async def execute(self, *a, **kw):
                return _Result()
        yield _DB()
    return _ctx


def _profile(**overrides):
    base = dict(production_cost=100.0, preferred_margin=0.30, minimum_price=None, product_type="papad")
    base.update(overrides)
    return SimpleNamespace(**base)


async def _no_reason(**kwargs):
    return {"text": "", "model_used": "sarvam-advanced", "escalated": False}


@pytest.mark.asyncio
async def test_no_profile_returns_no_profile_message():
    result = await node_module.negotiation_node({})  # no user_id at all
    assert result["outbound_messages"][0]["body"] == node_module.NO_PROFILE_MSG


@pytest.mark.asyncio
async def test_negative_cost_profile_treated_as_no_profile(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile(production_cost=-500, minimum_price=None)))
    result = await node_module.negotiation_node({"user_id": "u1"})
    assert result["outbound_messages"][0]["body"] == node_module.NO_PROFILE_MSG


@pytest.mark.asyncio
async def test_starting_with_no_offer_in_text_asks_for_one(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile()))
    result = await node_module.negotiation_node({"user_id": "u1", "raw_input_text": "কাস্টমার আসতে চায়"})
    assert result["outbound_messages"][0]["body"] == node_module.NO_OFFER_MSG
    assert result["pending_negotiation"]["turns"] == 0


@pytest.mark.asyncio
async def test_starting_offer_at_or_above_floor_is_accepted(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile()))
    monkeypatch.setattr(node_module, "route_completion", _no_reason)

    result = await node_module.negotiation_node({"user_id": "u1", "raw_input_text": "কাস্টমার ১৫০ টাকা বলেছে"})
    assert "150" in result["outbound_messages"][0]["body"]
    assert result["pending_negotiation"] is None
    assert result["awaiting_negotiation"] is False


@pytest.mark.asyncio
async def test_starting_offer_below_floor_gets_a_counter(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(profile=_profile()))  # floor = 130
    monkeypatch.setattr(node_module, "route_completion", _no_reason)

    result = await node_module.negotiation_node({"user_id": "u1", "raw_input_text": "কাস্টমার ৮০ টাকা বলেছে"})
    assert result["awaiting_negotiation"] is True
    assert result["pending_negotiation"]["last_counter"] == 130.0  # turn 1 holds at floor
    assert "130" in result["outbound_messages"][0]["body"]


@pytest.mark.asyncio
async def test_accepting_previous_counter_finalizes_deal(monkeypatch):
    monkeypatch.setattr(node_module, "route_completion", _no_reason)

    pending = {"floor_price": 130.0, "product_type": "papad", "turns": 1, "last_counter": 130.0}
    result = await node_module.negotiation_node({"pending_negotiation": pending, "raw_input_text": "হ্যাঁ"})
    assert result["pending_negotiation"] is None
    assert "130" in result["outbound_messages"][0]["body"]
    assert "negotiation_node:finalized" in result["trace"][0]


@pytest.mark.asyncio
async def test_continuing_with_no_offer_repeats_the_ask():
    pending = {"floor_price": 130.0, "product_type": "papad", "turns": 1}
    result = await node_module.negotiation_node({"pending_negotiation": pending, "raw_input_text": "চিন্তা করছি"})
    assert result["outbound_messages"][0]["body"] == node_module.NO_OFFER_MSG
    assert result["pending_negotiation"] == pending  # unchanged


@pytest.mark.asyncio
async def test_exceeding_max_turns_holds_firm_and_ends_negotiation():
    pending = {"floor_price": 130.0, "product_type": "papad", "turns": node_module.MAX_NEGOTIATION_TURNS}
    result = await node_module.negotiation_node({"pending_negotiation": pending, "raw_input_text": "৯০ টাকা দেব"})
    assert result["pending_negotiation"] is None
    assert "130" in result["outbound_messages"][0]["body"]
    assert "max_turns_hold_firm" in result["trace"][0]


@pytest.mark.asyncio
async def test_second_counter_splits_gap_between_floor_and_offer(monkeypatch):
    monkeypatch.setattr(node_module, "route_completion", _no_reason)

    pending = {"floor_price": 200.0, "product_type": "papad", "turns": 1, "last_counter": 200.0}
    result = await node_module.negotiation_node({"pending_negotiation": pending, "raw_input_text": "১০০ টাকা দেব"})
    # turn becomes 2: max(floor, (floor+offer)/2) = max(200, 150) = 200
    assert result["pending_negotiation"]["last_counter"] == 200.0


@pytest.mark.asyncio
async def test_model_unavailable_during_reason_generation_still_completes_deal(monkeypatch):
    async def _raise(**kwargs):
        raise ModelUnavailableError("down")

    monkeypatch.setattr(node_module, "route_completion", _raise)

    pending = {"floor_price": 130.0, "product_type": "papad", "turns": 1, "last_counter": 130.0}
    result = await node_module.negotiation_node({"pending_negotiation": pending, "raw_input_text": "হ্যাঁ"})
    assert "130" in result["outbound_messages"][0]["body"] 


@pytest.mark.asyncio
async def test_reason_containing_a_number_is_discarded_not_shown(monkeypatch):
    async def _fake(**kwargs):
        return {"text": "৫০ টাকা কম দিলেও চলবে", "model_used": "sarvam-advanced", "escalated": False}  # model breaks the rule

    monkeypatch.setattr(node_module, "route_completion", _fake)

    pending = {"floor_price": 130.0, "product_type": "papad", "turns": 1, "last_counter": 130.0}
    result = await node_module.negotiation_node({"pending_negotiation": pending, "raw_input_text": "হ্যাঁ"})
    assert "৫০" not in result["outbound_messages"][0]["body"]  


@pytest.mark.asyncio
async def test_reason_containing_spelled_out_number_word_is_discarded(monkeypatch):
    async def _fake(**kwargs):
        return {"text": "পঞ্চাশ টাকা হলে রাজি", "model_used": "sarvam-advanced", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    pending = {"floor_price": 130.0, "product_type": "papad", "turns": 1, "last_counter": 130.0}
    result = await node_module.negotiation_node({"pending_negotiation": pending, "raw_input_text": "হ্যাঁ"})
    assert "পঞ্চাশ" not in result["outbound_messages"][0]["body"]
