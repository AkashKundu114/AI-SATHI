import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager

import pytest
from shared.guardrails import poster_dedup as dedup_module


def test_build_key_stable_for_same_inputs():
    k1 = dedup_module.build_poster_dedup_key("user-1", "পাপড়", "caption text")
    k2 = dedup_module.build_poster_dedup_key("user-1", "পাপড়", "caption text")
    assert k1 == k2


def test_build_key_differs_by_user():
    k1 = dedup_module.build_poster_dedup_key("user-1", "পাপড়", "caption text")
    k2 = dedup_module.build_poster_dedup_key("user-2", "পাপড়", "caption text")
    assert k1 != k2


def test_build_key_case_and_whitespace_insensitive():
    k1 = dedup_module.build_poster_dedup_key("user-1", "  Papad  ", "Caption  Text")
    k2 = dedup_module.build_poster_dedup_key("user-1", "papad", "caption text")
    assert k1 == k2


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeDB:
    def __init__(self, row=None):
        self._row = row

    async def execute(self, *a, **kw):
        return _FakeResult(self._row)

    async def commit(self):
        pass


def _fake_get_db_session(row=None):
    @asynccontextmanager
    async def _ctx():
        yield _FakeDB(row)

    return _ctx


@pytest.mark.asyncio
async def test_get_cached_poster_returns_none_on_miss(monkeypatch):
    monkeypatch.setattr(dedup_module, "get_db_session", _fake_get_db_session(row=None))
    result = await dedup_module.get_cached_poster("some-key")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_poster_returns_dict_on_hit(monkeypatch):
    monkeypatch.setattr(
        dedup_module,
        "get_db_session",
        _fake_get_db_session(row=("catalog/x/poster.jpg", "flux-pro")),
    )
    result = await dedup_module.get_cached_poster("some-key")
    assert result == {
        "poster_s3_key": "catalog/x/poster.jpg",
        "poster_tier": "flux-pro",
    }


@pytest.mark.asyncio
async def test_record_poster_does_not_raise_on_db_error(monkeypatch):
    @asynccontextmanager
    async def _raising_ctx():
        raise RuntimeError("db down")
        yield

    monkeypatch.setattr(dedup_module, "get_db_session", lambda: _raising_ctx())
    await dedup_module.record_poster("key", "s3key", "flux-pro")
