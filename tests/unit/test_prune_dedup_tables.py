import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from contextlib import asynccontextmanager

import pytest
import scripts.prune_dedup_tables as script_module


class _FakeResult:
    def fetchone(self):
        return (12, 3)


class _FakeDB:
    async def execute(self, *a, **kw):
        return _FakeResult()

    async def commit(self):
        pass


def _fake_get_db_session():
    @asynccontextmanager
    async def _ctx():
        yield _FakeDB()

    return _ctx


@pytest.mark.asyncio
async def test_prune_returns_row_counts_from_the_sql_function(monkeypatch):
    monkeypatch.setattr(script_module, "get_db_session", _fake_get_db_session())
    dedup_deleted, rate_limit_deleted = await script_module.prune()
    assert dedup_deleted == 12
    assert rate_limit_deleted == 3
