import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from services.orchestrator import model_router as router_module
from shared.config.token_budgets import DEFAULT_TOKEN_BUDGET


class _FakeSettings:
    sarvam_api_key = "test-key"
    sarvam_advanced_model = "sarvam-105b"
    sarvam_chat_model = "sarvam-30b"
    use_local_models = False


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    router_module._reset_breaker_for_tests()
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    async def _not_hard_stopped(vendor):
        return False

    async def _not_degraded(vendor):
        return False

    async def _fake_charge(*a, **kw):
        return {
            "used": 0,
            "total_budget": 1,
            "degraded_mode": False,
            "hard_stopped": False,
        }

    monkeypatch.setattr(router_module, "is_hard_stopped", _not_hard_stopped)
    monkeypatch.setattr(router_module, "is_degraded", _not_degraded)
    monkeypatch.setattr(router_module, "charge_credits", _fake_charge)
    yield
    router_module._reset_breaker_for_tests()


@pytest.mark.asyncio
async def test_known_task_name_passes_its_specific_max_tokens(monkeypatch):
    captured = {}

    async def _fake_chat_completion(system, prompt, model=None, max_tokens=700):
        captured["max_tokens"] = max_tokens
        return '{"confidence": 0.9}'

    monkeypatch.setattr(
        router_module.sarvam_client, "chat_completion", _fake_chat_completion
    )

    await router_module.route_completion(
        system="s",
        prompt="p",
        criticality=router_module.TaskCriticality.ROUTINE,
        confidence_floor=0.0,
        task_name="greeting",
    )
    assert captured["max_tokens"] == 50


@pytest.mark.asyncio
async def test_no_task_name_uses_default_budget(monkeypatch):
    captured = {}

    async def _fake_chat_completion(system, prompt, model=None, max_tokens=700):
        captured["max_tokens"] = max_tokens
        return '{"confidence": 0.9}'

    monkeypatch.setattr(
        router_module.sarvam_client, "chat_completion", _fake_chat_completion
    )

    await router_module.route_completion(
        system="s",
        prompt="p",
        criticality=router_module.TaskCriticality.ROUTINE,
        confidence_floor=0.0,
    )
    assert captured["max_tokens"] == DEFAULT_TOKEN_BUDGET
