import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from services.orchestrator.nodes import conversation_node as node_module
from services.orchestrator.model_router import ModelUnavailableError


@pytest.mark.asyncio
async def test_empty_input_returns_canned_fallback_without_calling_model(monkeypatch):
    async def _should_not_be_called(**kwargs):
        raise AssertionError("route_completion should not be called for empty input")

    monkeypatch.setattr(node_module, "route_completion", _should_not_be_called)

    result = await node_module.general_conversation_node({"raw_input_text": "   "})
    assert result["outbound_messages"][0]["body"] == node_module.CANNED_FALLBACK
    assert result["trace"] == ["general_conversation_node:empty_input"]


@pytest.mark.asyncio
async def test_model_unavailable_falls_back_to_canned_message(monkeypatch):
    async def _raise(**kwargs):
        raise ModelUnavailableError("down")

    monkeypatch.setattr(node_module, "route_completion", _raise)

    result = await node_module.general_conversation_node({"raw_input_text": "cricket score bolo"})
    assert result["outbound_messages"][0]["body"] == node_module.CANNED_FALLBACK
    assert result["trace"] == ["general_conversation_node:model_unavailable"]


@pytest.mark.asyncio
async def test_happy_path_returns_model_reply_and_trace(monkeypatch):
    async def _fake(**kwargs):
        return {"text": "আমি রান্নার রেসিপি জানি না, কিন্তু হিসাব রাখতে সাহায্য করতে পারি।", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.general_conversation_node({"raw_input_text": "রান্নার রেসিপি বলো"})
    assert result["outbound_messages"][0]["body"] == "আমি রান্নার রেসিপি জানি না, কিন্তু হিসাব রাখতে সাহায্য করতে পারি।"
    assert result["trace"] == ["general_conversation_node:sarvam-standard"]


@pytest.mark.asyncio
async def test_blank_model_reply_falls_back_to_canned_message(monkeypatch):
    async def _fake(**kwargs):
        return {"text": "   ", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.general_conversation_node({"raw_input_text": "hi"})
    assert result["outbound_messages"][0]["body"] == node_module.CANNED_FALLBACK


@pytest.mark.asyncio
async def test_reads_transcript_field_when_text_field_absent(monkeypatch):
    async def _fake(**kwargs):
        assert kwargs["prompt"] == "ভয়েস থেকে আসা টেক্সট"
        return {"text": "ঠিক আছে", "model_used": "sarvam-standard", "escalated": False}

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.general_conversation_node({"raw_input_transcript": "ভয়েস থেকে আসা টেক্সট"})
    assert result["outbound_messages"][0]["body"] == "ঠিক আছে"
