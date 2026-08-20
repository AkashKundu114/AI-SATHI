import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager

import pytest
from shared.db import dedup as dedup_module


class _FakeResult:
    def __init__(self, count):
        self._count = count

    def fetchone(self):
        return (self._count,)


class _FakeDB:
    def __init__(self, count):
        self._count = count

    async def execute(self, *a, **kw):
        return _FakeResult(self._count)

    async def commit(self):
        pass


def _fake_get_db_session(count):
    @asynccontextmanager
    async def _ctx():
        yield _FakeDB(count)

    return _ctx


@pytest.mark.asyncio
async def test_under_cap_returns_true(monkeypatch):
    monkeypatch.setattr(dedup_module, "get_db_session", _fake_get_db_session(count=3))
    result = await dedup_module.check_and_increment_daily_feature_cap(
        "user-1", "catalog", max_per_day=15
    )
    assert result is True


@pytest.mark.asyncio
async def test_at_cap_returns_true_boundary_inclusive(monkeypatch):
    monkeypatch.setattr(dedup_module, "get_db_session", _fake_get_db_session(count=15))
    result = await dedup_module.check_and_increment_daily_feature_cap(
        "user-1", "catalog", max_per_day=15
    )
    assert result is True


@pytest.mark.asyncio
async def test_over_cap_returns_false(monkeypatch):
    monkeypatch.setattr(dedup_module, "get_db_session", _fake_get_db_session(count=16))
    result = await dedup_module.check_and_increment_daily_feature_cap(
        "user-1", "catalog", max_per_day=15
    )
    assert result is False
