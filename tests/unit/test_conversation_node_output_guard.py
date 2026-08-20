import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from services.orchestrator.nodes import conversation_node as node_module


@pytest.mark.asyncio
async def test_leaked_secret_in_model_reply_is_replaced_with_canned_fallback(
    monkeypatch,
):
    async def _fake(**kwargs):
        return {
            "text": "here's a key sk-abcdefghijklmnopqrstuvwxyz123456",
            "model_used": "sarvam-standard",
            "escalated": False,
        }

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.general_conversation_node({"raw_input_text": "কিছু বলো"})
    assert result["outbound_messages"][0]["body"] == node_module.CANNED_FALLBACK
    assert "output_guard_triggered" in result["trace"][0]


@pytest.mark.asyncio
async def test_url_in_model_reply_is_replaced_with_canned_fallback(monkeypatch):
    async def _fake(**kwargs):
        return {
            "text": "দেখুন https://example.com/details",
            "model_used": "sarvam-standard",
            "escalated": False,
        }

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.general_conversation_node({"raw_input_text": "কিছু বলো"})
    assert result["outbound_messages"][0]["body"] == node_module.CANNED_FALLBACK


@pytest.mark.asyncio
async def test_normal_reply_passes_through_unchanged(monkeypatch):
    async def _fake(**kwargs):
        return {
            "text": "আমি রান্নার রেসিপি জানি না, কিন্তু হিসাব রাখতে সাহায্য করতে পারি।",
            "model_used": "sarvam-standard",
            "escalated": False,
        }

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.general_conversation_node(
        {"raw_input_text": "রান্নার রেসিপি বলো"}
    )
    assert (
        result["outbound_messages"][0]["body"]
        == "আমি রান্নার রেসিপি জানি না, কিন্তু হিসাব রাখতে সাহায্য করতে পারি।"
    )
    assert "output_guard_triggered" not in result["trace"][0]
