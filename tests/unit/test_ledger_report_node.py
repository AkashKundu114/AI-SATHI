import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from datetime import date
from types import SimpleNamespace

import pytest
from services.orchestrator.nodes import ledger_report_node as node_module


def _stub_pdf_generator(monkeypatch, fake):
    monkeypatch.setitem(
        sys.modules,
        "services.pdf_service.generator",
        SimpleNamespace(generate_monthly_report=fake),
    )


@pytest.fixture(autouse=True)
def _mock_cap(monkeypatch):
    async def _fake_cap(*a, **kw):
        return True

    monkeypatch.setattr(node_module, "check_and_increment_daily_feature_cap", _fake_cap)


@pytest.mark.asyncio
async def test_no_user_id_asks_to_start_ledger_first():
    result = await node_module.ledger_report_node({})
    assert result["trace"] == ["ledger_report_node:no_user"]


@pytest.mark.asyncio
async def test_generation_failure_degrades_to_friendly_message(monkeypatch):
    async def _raise(user_id, year, month):
        raise RuntimeError("weasyprint blew up")

    _stub_pdf_generator(monkeypatch, _raise)

    import uuid

    uid = f"test-user-{uuid.uuid4().hex[:8]}"
    result = await node_module.ledger_report_node({"user_id": uid})
    assert "generation_failed" in result["trace"][0]
    assert "সমস্যা হয়েছে" in result["outbound_messages"][0]["body"]


@pytest.mark.asyncio
async def test_zero_entries_reports_no_data_for_the_month(monkeypatch):
    async def _fake(user_id, year, month):
        return {
            "total_income": 0,
            "total_expense": 0,
            "s3_url": "https://example.com/x.pdf",
        }

    _stub_pdf_generator(monkeypatch, _fake)

    import uuid

    uid = f"test-user-{uuid.uuid4().hex[:8]}"
    result = await node_module.ledger_report_node({"user_id": uid})
    assert result["trace"] == ["ledger_report_node:no_entries"]


@pytest.mark.asyncio
async def test_happy_path_sends_document_message_with_correct_caption(monkeypatch):
    async def _fake(user_id, year, month):
        return {
            "total_income": 500.0,
            "total_expense": 200.0,
            "s3_url": "https://example.com/report.pdf",
        }

    _stub_pdf_generator(monkeypatch, _fake)

    result = await node_module.ledger_report_node({"user_id": "u1"})
    msg = result["outbound_messages"][0]
    assert msg["type"] == "document"
    assert msg["url"] == "https://example.com/report.pdf"
    assert "আয়: ₹500" in msg["caption"]
    assert "খরচ: ₹200" in msg["caption"]
    assert "লাভ: ₹300" in msg["caption"]
    today = date.today()
    assert msg["filename"] == f"kotha-khata-{today.year}-{today.month:02d}.pdf"
    assert result["trace"] == ["ledger_report_node:sent"]
