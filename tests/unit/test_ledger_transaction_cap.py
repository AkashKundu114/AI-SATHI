import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import json
import pytest

from services.orchestrator.nodes import ledger_node as node_module


def _many_transactions(n: int) -> list[dict]:
    return [{"type": "INCOME", "amount_inr": 10, "item_bengali": f"item{i}"} for i in range(n)]


@pytest.mark.asyncio
async def test_transaction_list_is_truncated_at_the_cap(monkeypatch):
    async def _fake(**kwargs):
        return {
            "text": json.dumps({"transactions": _many_transactions(50), "confidence": 0.9}),
            "model_used": "sarvam-standard", "escalated": False,
        }

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "অনেকগুলো লেনদেন"})
    assert len(result["pending_ledger_entry"]["transactions"]) == node_module.MAX_TRANSACTIONS_PER_ENTRY
    assert "truncated" in result["trace"][0]


@pytest.mark.asyncio
async def test_transaction_list_under_cap_is_untouched(monkeypatch):
    async def _fake(**kwargs):
        return {
            "text": json.dumps({"transactions": _many_transactions(3), "confidence": 0.9}),
            "model_used": "sarvam-standard", "escalated": False,
        }

    monkeypatch.setattr(node_module, "route_completion", _fake)

    result = await node_module.ledger_extract_node({"raw_input_transcript": "তিনটি লেনদেন"})
    assert len(result["pending_ledger_entry"]["transactions"]) == 3
    assert "truncated" not in result["trace"][0]
