import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from services.orchestrator import model_router as router_module
from services.translation_service.sarvam_client import SarvamUnavailableError


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
async def test_breaker_stays_closed_below_failure_threshold(monkeypatch):
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    async def _raise(*a, **kw):
        raise SarvamUnavailableError("down")

    monkeypatch.setattr(router_module.sarvam_client, "chat_completion", _raise)

    for _ in range(router_module._BREAKER_FAILURE_THRESHOLD - 1):
        with pytest.raises(router_module.ModelUnavailableError):
            await router_module.route_completion(
                system="s", prompt="p", criticality=router_module.TaskCriticality.ROUTINE
            )

    assert router_module._breaker_is_open() is False


@pytest.mark.asyncio
async def test_breaker_opens_after_threshold_consecutive_failures(monkeypatch):
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    async def _raise(*a, **kw):
        raise SarvamUnavailableError("down")

    monkeypatch.setattr(router_module.sarvam_client, "chat_completion", _raise)

    for _ in range(router_module._BREAKER_FAILURE_THRESHOLD):
        with pytest.raises(router_module.ModelUnavailableError):
            await router_module.route_completion(
                system="s", prompt="p", criticality=router_module.TaskCriticality.ROUTINE
            )

    assert router_module._breaker_is_open() is True


@pytest.mark.asyncio
async def test_open_breaker_skips_sarvam_call_entirely(monkeypatch):
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    call_count = {"n": 0}

    async def _raise(*a, **kw):
        call_count["n"] += 1
        raise SarvamUnavailableError("down")

    monkeypatch.setattr(router_module.sarvam_client, "chat_completion", _raise)

    for _ in range(router_module._BREAKER_FAILURE_THRESHOLD):
        with pytest.raises(router_module.ModelUnavailableError):
            await router_module.route_completion(
                system="s", prompt="p", criticality=router_module.TaskCriticality.ROUTINE
            )

    calls_before = call_count["n"]

    with pytest.raises(router_module.ModelUnavailableError):
        await router_module.route_completion(
            system="s", prompt="p", criticality=router_module.TaskCriticality.ROUTINE
        )

    assert call_count["n"] == calls_before  # breaker open — Sarvam not called again


@pytest.mark.asyncio
async def test_a_success_resets_the_failure_counter(monkeypatch):
    monkeypatch.setattr(router_module, "get_settings", lambda: _FakeSettings())

    responses = [SarvamUnavailableError("down"), SarvamUnavailableError("down"), '{"confidence": 0.9}']

    async def _sequenced(*a, **kw):
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(router_module.sarvam_client, "chat_completion", _sequenced)

    for _ in range(2):
        with pytest.raises(router_module.ModelUnavailableError):
            await router_module.route_completion(
                system="s", prompt="p", criticality=router_module.TaskCriticality.ROUTINE, confidence_floor=0.0
            )

    result = await router_module.route_completion(
        system="s", prompt="p", criticality=router_module.TaskCriticality.ROUTINE, confidence_floor=0.0
    )
    assert result["model_used"] == "sarvam-standard"
    assert router_module._breaker_state["consecutive_failures"] == 0
