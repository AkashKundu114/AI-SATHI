import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager

import pytest
from shared.guardrails import budget as budget_module


class _FakeChargeResult:
    def __init__(self, used, total, degraded, hard_stopped):
        self._row = (used, total, degraded, hard_stopped)

    def fetchone(self):
        return self._row


class _FakeDB:
    def __init__(self, used, total, degraded, hard_stopped):
        self._used = used
        self._total = total
        self._degraded = degraded
        self._hard_stopped = hard_stopped

    async def execute(self, query, params=None):
        return _FakeChargeResult(
            self._used, self._total, self._degraded, self._hard_stopped
        )

    async def commit(self):
        pass


def _fake_get_db_session(used, total, degraded, hard_stopped):
    @asynccontextmanager
    async def _ctx():
        yield _FakeDB(used, total, degraded, hard_stopped)

    return _ctx


@pytest.fixture(autouse=True)
def _reset():
    budget_module.reset_for_tests()
    yield
    budget_module.reset_for_tests()


@pytest.mark.asyncio
async def test_charge_credits_returns_updated_status(monkeypatch):
    monkeypatch.setattr(
        budget_module,
        "get_db_session",
        _fake_get_db_session(used=10, total=1000, degraded=False, hard_stopped=False),
    )
    status = await budget_module.charge_credits("sarvam", 1.0, "text")
    assert status["used"] == 10
    assert status["degraded_mode"] is False


@pytest.mark.asyncio
async def test_get_budget_status_uses_cache_within_ttl(monkeypatch):
    call_count = {"n": 0}

    @asynccontextmanager
    async def _ctx():
        call_count["n"] += 1

        class _Row:
            def fetchone(self):
                return (10, 1000, False, False)

        class _DB:
            async def execute(self, *a, **kw):
                return _Row()

        yield _DB()

    monkeypatch.setattr(budget_module, "get_db_session", lambda: _ctx())

    await budget_module.get_budget_status("sarvam")
    await budget_module.get_budget_status("sarvam")
    assert call_count["n"] == 1


@pytest.mark.asyncio
async def test_is_degraded_true_when_flag_set(monkeypatch):
    monkeypatch.setattr(
        budget_module,
        "get_db_session",
        _fake_get_db_session(used=850, total=1000, degraded=True, hard_stopped=False),
    )
    assert await budget_module.is_degraded("sarvam") is True


@pytest.mark.asyncio
async def test_is_hard_stopped_true_when_flag_set(monkeypatch):
    monkeypatch.setattr(
        budget_module,
        "get_db_session",
        _fake_get_db_session(used=960, total=1000, degraded=True, hard_stopped=True),
    )
    assert await budget_module.is_hard_stopped("sarvam") is True


@pytest.mark.asyncio
async def test_budget_status_falls_open_on_db_error(monkeypatch):
    @asynccontextmanager
    async def _raising_ctx():
        raise RuntimeError("db down")
        yield

    monkeypatch.setattr(budget_module, "get_db_session", lambda: _raising_ctx())

    status = await budget_module.get_budget_status("sarvam")
    assert status["degraded_mode"] is False
    assert status["hard_stopped"] is False


def test_check_min_request_gap_first_call_always_passes():
    assert budget_module.check_min_request_gap("user-unique-1") is True


def test_check_min_request_gap_immediate_second_call_fails():
    budget_module.check_min_request_gap("user-unique-2")
    assert budget_module.check_min_request_gap("user-unique-2") is False
