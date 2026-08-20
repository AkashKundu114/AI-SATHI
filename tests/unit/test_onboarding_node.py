import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from services.orchestrator.nodes import onboarding_node as node_module


@pytest.mark.asyncio
async def test_welcome_step_sends_welcome_and_advances_to_await_name():
    result = await node_module.onboarding_node({"onboarding_step": "WELCOME"})
    assert result["onboarding_step"] == "AWAIT_NAME"
    assert result["outbound_messages"][0]["body"] == node_module.WELCOME


@pytest.mark.asyncio
async def test_default_step_treated_as_welcome_when_missing():
    result = await node_module.onboarding_node({})
    assert result["onboarding_step"] == "AWAIT_NAME"


@pytest.mark.asyncio
async def test_await_name_empty_reply_asks_again():
    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_NAME", "raw_input_text": "   "}
    )
    assert result["trace"] == ["onboarding_node:empty_name"]
    assert "onboarding_step" not in result


@pytest.mark.asyncio
async def test_await_name_valid_reply_advances_to_await_block():
    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_NAME", "raw_input_text": "সুনীতা দাস"}
    )
    assert result["onboarding_name"] == "সুনীতা দাস"
    assert result["onboarding_step"] == "AWAIT_BLOCK"
    assert "সুনীতা দাস দি" in result["outbound_messages"][0]["body"]


@pytest.mark.asyncio
async def test_await_name_truncates_absurdly_long_input():
    long_name = "স" * 500
    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_NAME", "raw_input_text": long_name}
    )
    assert len(result["onboarding_name"]) == node_module._MAX_FIELD_LEN


@pytest.mark.asyncio
async def test_await_block_empty_reply_asks_again():
    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_BLOCK", "raw_input_text": ""}
    )
    assert result["trace"] == ["onboarding_node:empty_block"]


@pytest.mark.asyncio
async def test_await_block_valid_reply_advances_to_await_consent():
    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_BLOCK", "raw_input_text": "Balidewanganj"}
    )
    assert result["onboarding_block"] == "Balidewanganj"
    assert result["onboarding_step"] == "AWAIT_CONSENT"


@pytest.mark.asyncio
async def test_await_consent_refusal_does_not_create_user(monkeypatch):
    async def _should_not_be_called(state):
        raise AssertionError("_create_user should not be called without consent")

    monkeypatch.setattr(node_module, "_create_user", _should_not_be_called)

    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_CONSENT", "raw_input_text": "না"}
    )
    assert result["trace"] == ["onboarding_node:consent_not_given"]


@pytest.mark.asyncio
async def test_await_consent_accepted_creates_user_and_completes(monkeypatch):
    async def _fake_create_user(state):
        return "new-user-uuid"

    monkeypatch.setattr(node_module, "_create_user", _fake_create_user)

    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_CONSENT", "raw_input_text": "হ্যাঁ"}
    )
    assert result["user_id"] == "new-user-uuid"
    assert result["is_new_user"] is False
    assert result["onboarding_step"] == "DONE"
    assert result["trace"] == ["onboarding_node:complete"]


@pytest.mark.asyncio
async def test_await_consent_accepts_english_yes_variants(monkeypatch):
    async def _fake_create_user(state):
        return "new-user-uuid"

    monkeypatch.setattr(node_module, "_create_user", _fake_create_user)

    for variant in ["ha", "haan", "yes", "হ্যা"]:
        result = await node_module.onboarding_node(
            {"onboarding_step": "AWAIT_CONSENT", "raw_input_text": variant}
        )
        assert result["onboarding_step"] == "DONE", f"failed for variant={variant!r}"


@pytest.mark.asyncio
async def test_await_consent_create_user_failure_degrades_gracefully(monkeypatch):
    async def _fake_create_user(state):
        raise RuntimeError("db down")

    monkeypatch.setattr(node_module, "_create_user", _fake_create_user)

    result = await node_module.onboarding_node(
        {"onboarding_step": "AWAIT_CONSENT", "raw_input_text": "হ্যাঁ"}
    )
    assert result["trace"] == ["onboarding_node:create_user_failed"]
    assert "user_id" not in result


@pytest.mark.asyncio
async def test_done_step_or_unknown_step_shows_start_prompt():
    result = await node_module.onboarding_node({"onboarding_step": "DONE"})
    assert result["trace"] == ["onboarding_node:already_done"]
