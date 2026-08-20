import pytest
from services.orchestrator.nodes.intent_router import classify_intent
from services.orchestrator.nodes.upgrade_node import upgrade_node


@pytest.mark.asyncio
async def test_upgrade_node_returns_plan_details():
    state = {"phone_number": "+919876543210"}
    result = await upgrade_node(state)

    assert result["trace"] == ["upgrade_node:info_sent"]
    assert len(result["outbound_messages"]) == 1
    assert result["outbound_messages"][0]["type"] == "text"
    assert "AI-SATHI প্রিমিয়াম প্ল্যান" in result["outbound_messages"][0]["body"]
    assert "₹99" in result["outbound_messages"][0]["body"]
    assert "₹299" in result["outbound_messages"][0]["body"]
    assert "₹499" in result["outbound_messages"][0]["body"]


@pytest.mark.asyncio
async def test_classify_intent_routes_upgrade_keywords():
    keywords = ["upgrade", "আপগ্রেড", "premium", "প্রিমিয়াম", "plan", "প্ল্যান"]
    for kw in keywords:
        state = {"raw_input_text": f"আমি {kw} করতে চাই"}
        res = await classify_intent(state)
        assert res["active_feature"] == "UPGRADE"
        assert res["trace"] == ["intent_router:keyword:UPGRADE"]
