import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from services.orchestrator import model_router as router_module


class _FakeSettings:
    sarvam_api_key = "test-key"
    sarvam_advanced_model = "sarvam-105b"
    sarvam_chat_model = "sarvam-30b"
    use_local_models = False


@pytest.fixture(autouse=True)
def _reset_breaker():
    router_module._reset_breaker_for_tests()
    yield
    router_module._reset_breaker_for_tests()


@pytest.mark.asyncio
async def test_advanced_tier_raises_budget_exhausted_when_hard_stopped(monkeypatch):
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    async def _hard_stopped(vendor):
        return True

    monkeypatch.setattr(router_module, "is_hard_stopped", _hard_stopped)

    with pytest.raises(router_module.BudgetExhaustedError):
        await router_module.route_completion(
            system="s",
            prompt="p",
            criticality=router_module.TaskCriticality.ROUTINE,
            tier=router_module.AgentTier.ADVANCED,
        )


@pytest.mark.asyncio
async def test_budget_exhausted_error_is_a_model_unavailable_error_subclass():
    assert issubclass(
        router_module.BudgetExhaustedError, router_module.ModelUnavailableError
    )


@pytest.mark.asyncio
async def test_advanced_tier_downgrades_to_standard_when_degraded(monkeypatch):
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    async def _not_hard_stopped(vendor):
        return False

    async def _degraded(vendor):
        return True

    monkeypatch.setattr(router_module, "is_hard_stopped", _not_hard_stopped)
    monkeypatch.setattr(router_module, "is_degraded", _degraded)

    captured = {}

    async def _fake_chat_completion(system, prompt, model=None, *args, **kwargs):
        captured["model"] = model
        return '{"confidence": 0.9}'

    async def _fake_charge(*a, **kw):
        return {
            "used": 0,
            "total_budget": 1,
            "degraded_mode": True,
            "hard_stopped": False,
        }

    monkeypatch.setattr(
        router_module.sarvam_client, "chat_completion", _fake_chat_completion
    )
    monkeypatch.setattr(router_module, "charge_credits", _fake_charge)

    result = await router_module.route_completion(
        system="s",
        prompt="p",
        criticality=router_module.TaskCriticality.ROUTINE,
        tier=router_module.AgentTier.ADVANCED,
        confidence_floor=0.0,
    )
    assert captured["model"] == _FakeSettings.sarvam_chat_model

    assert result["model_used"] == "sarvam-standard"


@pytest.mark.asyncio
async def test_routine_tier_unaffected_by_degraded_mode(monkeypatch):
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    async def _not_hard_stopped(vendor):
        return False

    async def _degraded(vendor):
        return True

    monkeypatch.setattr(router_module, "is_hard_stopped", _not_hard_stopped)
    monkeypatch.setattr(router_module, "is_degraded", _degraded)

    async def _fake_chat_completion(system, prompt, model=None, *args, **kwargs):
        return '{"confidence": 0.9}'

    async def _fake_charge(*a, **kw):
        return {
            "used": 0,
            "total_budget": 1,
            "degraded_mode": True,
            "hard_stopped": False,
        }

    monkeypatch.setattr(
        router_module.sarvam_client, "chat_completion", _fake_chat_completion
    )
    monkeypatch.setattr(router_module, "charge_credits", _fake_charge)

    result = await router_module.route_completion(
        system="s",
        prompt="p",
        criticality=router_module.TaskCriticality.ROUTINE,
        confidence_floor=0.0,
    )
    assert result["model_used"] == "sarvam-standard"
