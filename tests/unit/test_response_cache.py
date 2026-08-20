import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager

import pytest
from shared.guardrails import response_cache as cache_module


def test_normalize_query_text_lowercases_and_sorts_words():
    assert cache_module.normalize_query_text(
        "Today Onion Price"
    ) == cache_module.normalize_query_text("price onion today")


def test_normalize_query_text_converts_bengali_digits():
    assert "1000" in cache_module.normalize_query_text("১০০০ টাকা")


def test_build_cache_key_is_stable_for_equivalent_queries():
    key1 = cache_module.build_cache_key(
        "market_report", "আজ পেঁয়াজের দাম", scope="Balidewanganj"
    )
    key2 = cache_module.build_cache_key(
        "market_report", "পেঁয়াজের আজ দাম", scope="Balidewanganj"
    )
    assert key1 == key2


def test_build_cache_key_differs_by_scope():
    key1 = cache_module.build_cache_key("market_report", "same query", scope="BlockA")
    key2 = cache_module.build_cache_key("market_report", "same query", scope="BlockB")
    assert key1 != key2


def test_build_cache_key_differs_by_feature():
    key1 = cache_module.build_cache_key("market_report", "same query", scope="x")
    key2 = cache_module.build_cache_key("scheme_search", "same query", scope="x")
    assert key1 != key2


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeDB:
    def __init__(self, row=None):
        self._row = row
        self.executed = []

    async def execute(self, query, params=None):
        self.executed.append(params)
        return _FakeResult(self._row)

    async def commit(self):
        pass


def _fake_get_db_session(row=None):
    @asynccontextmanager
    async def _ctx():
        yield _FakeDB(row)

    return _ctx


@pytest.mark.asyncio
async def test_get_cached_response_returns_none_on_miss(monkeypatch):
    monkeypatch.setattr(cache_module, "get_db_session", _fake_get_db_session(row=None))
    result = await cache_module.get_cached_response("some-key")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_response_returns_text_on_hit(monkeypatch):
    monkeypatch.setattr(
        cache_module, "get_db_session", _fake_get_db_session(row=("cached answer",))
    )
    result = await cache_module.get_cached_response("some-key")
    assert result == "cached answer"


@pytest.mark.asyncio
async def test_get_cached_response_falls_back_to_none_on_db_error(monkeypatch):
    @asynccontextmanager
    async def _raising_ctx():
        raise RuntimeError("db down")
        yield

    monkeypatch.setattr(cache_module, "get_db_session", lambda: _raising_ctx())
    result = await cache_module.get_cached_response("some-key")
    assert result is None


@pytest.mark.asyncio
async def test_set_cached_response_does_not_raise_on_db_error(monkeypatch):
    @asynccontextmanager
    async def _raising_ctx():
        raise RuntimeError("db down")
        yield

    monkeypatch.setattr(cache_module, "get_db_session", lambda: _raising_ctx())
    await cache_module.set_cached_response("some-key", "text")
