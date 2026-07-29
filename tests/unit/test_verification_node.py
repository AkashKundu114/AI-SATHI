import pytest
from unittest.mock import patch, MagicMock

from services.orchestrator.nodes.verification_node import verification_node


@pytest.mark.asyncio
async def test_verification_node_pending():
    state = {
        "user_id": "test_user_1",
        "user_profile": {"verification_status": "pending"},
        "verification_step": "type_selection"
    }
    result = await verification_node(state)
    assert result["verification_step"] == "DONE"
    assert "রিভিউ-এ আছে" in result["outbound_messages"][0]["body"]
    assert "verification:pending_notice" in result["trace"]


@pytest.mark.asyncio
async def test_verification_node_type_selection_prompt():
    state = {
        "user_id": "test_user_1",
        "user_profile": {"verification_status": "unverified"},
        "verification_step": "type_selection"
    }
    result = await verification_node(state)
    assert result.get("verification_step") is None # State unchanged
    assert "1️⃣ স্বনির্ভর গোষ্ঠী" in result["outbound_messages"][0]["body"]
    assert "verification:prompt_type_selection" in result["trace"]


@pytest.mark.asyncio
@patch("services.orchestrator.nodes.verification_node.get_db_session")
async def test_verification_node_type_selected(mock_get_db):
    from unittest.mock import AsyncMock
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_get_db.return_value.__aenter__.return_value = mock_db
    
    state = {
        "user_id": "test_user_1",
        "user_profile": {"verification_status": "unverified"},
        "verification_step": "type_selection",
        "raw_input_text": "2" # Shopkeeper
    }
    result = await verification_node(state)
    
    assert result["verification_step"] == "doc_upload"
    assert result["user_profile"]["user_type"] == "shopkeeper"
    assert "ট্রেড লাইসেন্স" in result["outbound_messages"][0]["body"]
    assert "verification:type_selected" in result["trace"]


@pytest.mark.asyncio
async def test_verification_node_doc_upload_waiting():
    state = {
        "user_id": "test_user_1",
        "user_profile": {"verification_status": "unverified"},
        "verification_step": "doc_upload",
        "last_message_type": "text"
    }
    result = await verification_node(state)
    assert result.get("verification_step") is None
    assert "পরিষ্কার ছবি" in result["outbound_messages"][0]["body"]
    assert "verification:waiting_for_image" in result["trace"]


@pytest.mark.asyncio
async def test_verification_node_doc_upload_success():
    state = {
        "user_id": "test_user_1",
        "user_profile": {"verification_status": "unverified"},
        "verification_step": "doc_upload",
        "last_message_type": "image",
        "raw_image_s3_key": "s3://bucket/test.jpg"
    }
    result = await verification_node(state)
    assert result["verification_step"] == "id_entry"
    assert result["verification_doc_number"] == "s3://bucket/test.jpg"
    assert "সফলভাবে আপলোড হয়েছে" in result["outbound_messages"][0]["body"]
    assert "verification:image_received" in result["trace"]


@pytest.mark.asyncio
@patch("services.orchestrator.nodes.verification_node.get_db_session")
async def test_verification_node_id_entry(mock_get_db):
    from unittest.mock import AsyncMock
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_get_db.return_value.__aenter__.return_value = mock_db
    
    state = {
        "user_id": "test_user_1",
        "user_profile": {"verification_status": "unverified", "user_type": "shopkeeper"},
        "verification_step": "id_entry",
        "verification_doc_number": "s3://bucket/test.jpg",
        "raw_input_text": "TRD-12345"
    }
    result = await verification_node(state)
    
    assert result["verification_step"] == "DONE"
    assert result["user_profile"]["verification_status"] == "pending"
    assert "সফলভাবে জমা হয়েছে" in result["outbound_messages"][0]["body"]
    assert "verification:submitted" in result["trace"]
    assert mock_db.add.called
    assert mock_db.execute.called
    assert mock_db.commit.called
