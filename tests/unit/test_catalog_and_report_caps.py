import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest

from services.orchestrator.nodes import catalog_node as catalog_module
from services.orchestrator.nodes import ledger_report_node as report_module


@pytest.mark.asyncio
async def test_catalog_node_blocks_when_daily_cap_reached(monkeypatch):
    async def _cap_reached(user_id, feature, max_per_day):
        return False

    monkeypatch.setattr(catalog_module, "check_and_increment_daily_feature_cap", _cap_reached)

    result = await catalog_module.catalog_node({"user_id": "u1", "raw_image_s3_key": "x.jpg"})
    assert result["trace"] == ["catalog_node:daily_cap_reached"]
    assert result["outbound_messages"][0]["body"] == catalog_module.CAP_REACHED_MSG


@pytest.mark.asyncio
async def test_catalog_node_skips_cap_check_without_user_id(monkeypatch):
    called = {"count": 0}

    async def _should_not_be_called(*a, **kw):
        called["count"] += 1
        return True

    monkeypatch.setattr(catalog_module, "check_and_increment_daily_feature_cap", _should_not_be_called)

    result = await catalog_module.catalog_node({})  
    assert called["count"] == 0
    assert result["trace"] == ["catalog_node:no_image_key"]


@pytest.mark.asyncio
async def test_ledger_report_node_blocks_when_daily_cap_reached(monkeypatch):
    async def _cap_reached(user_id, feature, max_per_day):
        return False

    monkeypatch.setattr(report_module, "check_and_increment_daily_feature_cap", _cap_reached)

    result = await report_module.ledger_report_node({"user_id": "u1"})
    assert result["trace"] == ["ledger_report_node:daily_cap_reached"]
    assert result["outbound_messages"][0]["body"] == report_module.REPORT_CAP_REACHED_MSG
