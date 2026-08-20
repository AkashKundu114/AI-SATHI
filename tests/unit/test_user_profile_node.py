import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from services.orchestrator.nodes import user_profile_node as node_module


class _FakeResult:
    def __init__(self, user):
        self._user = user

    def scalar_one_or_none(self):
        return self._user


class _FakeDB:
    def __init__(self, user):
        self._user = user

    async def execute(self, *args, **kwargs):
        return _FakeResult(self._user)


def _fake_get_db_session(user=None, raise_exc: Exception | None = None):
    @asynccontextmanager
    async def _ctx():
        if raise_exc:
            raise raise_exc
        yield _FakeDB(user)

    return _ctx


def _user(**overrides):
    base = dict(
        id="uuid-1234",
        business_categories=["papad", "pickle"],
        self_reported_literacy="functional",
        preferred_modality="voice",
        dialect_hint="rarhi",
        ledger_correction_rate=0.125,
        trust_stage="established",
        block="Balidewanganj",
        district="Hooghly",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_new_user_not_found_returns_is_new_user_true(monkeypatch):
    monkeypatch.setattr(node_module, "get_db_session", _fake_get_db_session(user=None))

    result = await node_module.load_user_profile_node(
        {"phone_number": "919876543210"}
    )
    assert result["is_new_user"] is True
    assert result["user_id"] is None
    assert result["user_profile"] is None
    assert result["trace"] == ["load_user_profile:new_user"]


@pytest.mark.asyncio
async def test_db_error_is_treated_as_new_user_not_a_crash(monkeypatch):
    monkeypatch.setattr(
        node_module,
        "get_db_session",
        _fake_get_db_session(raise_exc=RuntimeError("db down")),
    )

    result = await node_module.load_user_profile_node(
        {"phone_number": "919876543210"}
    )
    assert result["is_new_user"] is True
    assert result["trace"] == ["load_user_profile:db_error_treated_as_new_user"]


@pytest.mark.asyncio
async def test_existing_user_returns_full_profile(monkeypatch):
    monkeypatch.setattr(
        node_module, "get_db_session", _fake_get_db_session(user=_user())
    )

    result = await node_module.load_user_profile_node(
        {"phone_number": "919876543210"}
    )
    assert result["is_new_user"] is False
    assert result["user_id"] == "uuid-1234"
    assert result["user_profile"]["block"] == "Balidewanganj"
    assert result["user_profile"]["ledger_correction_rate"] == 0.125
    assert result["user_profile"]["business_categories"] == ["papad", "pickle"]


@pytest.mark.asyncio
async def test_null_business_categories_defaults_to_empty_list(monkeypatch):
    monkeypatch.setattr(
        node_module,
        "get_db_session",
        _fake_get_db_session(user=_user(business_categories=None)),
    )

    result = await node_module.load_user_profile_node(
        {"phone_number": "919876543210"}
    )
    assert result["user_profile"]["business_categories"] == []


@pytest.mark.asyncio
async def test_null_correction_rate_defaults_to_zero(monkeypatch):
    monkeypatch.setattr(
        node_module,
        "get_db_session",
        _fake_get_db_session(user=_user(ledger_correction_rate=None)),
    )

    result = await node_module.load_user_profile_node(
        {"phone_number": "919876543210"}
    )
    assert result["user_profile"]["ledger_correction_rate"] == 0.0
