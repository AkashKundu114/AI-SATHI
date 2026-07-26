import hmac
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from services.gateway import main as gateway
from shared.config.settings import get_settings


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _body(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _signature(body: bytes) -> str:
    secret = get_settings().wa_app_secret.encode()
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_valid_text_webhook_is_deduped_and_dispatched_once(monkeypatch):
    seen_message_ids: set[str] = set()
    dispatched = []

    async def _fake_mark_seen_or_skip(message_id: str) -> bool:
        if message_id in seen_message_ids:
            return False
        seen_message_ids.add(message_id)
        return True

    async def _fake_rate_limit(phone_number: str, max_per_hour: int) -> bool:
        return True

    async def _fake_dispatch(msg):
        dispatched.append(msg)

    monkeypatch.setattr(gateway, "mark_seen_or_skip", _fake_mark_seen_or_skip)
    monkeypatch.setattr(gateway, "check_and_increment_rate_limit", _fake_rate_limit)
    monkeypatch.setattr(gateway, "_dispatch_to_orchestrator", _fake_dispatch)

    body = _body("sample_text_webhook.json")
    client = TestClient(gateway.app)

    for _ in range(2):
        response = client.post(
            "/webhook/whatsapp",
            content=body,
            headers={"X-Hub-Signature-256": _signature(body), "content-type": "application/json"},
        )
        assert response.status_code == 200

    assert len(dispatched) == 1
    assert dispatched[0].message_id == "wamid.TEXT123"
    assert dispatched[0].text == "আজ ৩০০ টাকা পাপড় বিক্রি করেছি"


def test_bad_signature_is_rejected_before_dispatch(monkeypatch):
    dispatched = []

    async def _fake_dispatch(msg):
        dispatched.append(msg)

    monkeypatch.setattr(gateway, "_dispatch_to_orchestrator", _fake_dispatch)

    body = _body("sample_text_webhook.json")
    client = TestClient(gateway.app)
    response = client.post(
        "/webhook/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": "sha256=bad", "content-type": "application/json"},
    )

    assert response.status_code == 403
    assert dispatched == []


def test_webhook_fixtures_parse_to_expected_message_shapes():
    from shared.whatsapp.parser import parse_webhook_payload

    expected = {
        "sample_text_webhook.json": ("text", "wamid.TEXT123"),
        "sample_audio_webhook.json": ("audio", "wamid.AUDIO123"),
        "sample_image_webhook.json": ("image", "wamid.IMAGE123"),
        "sample_interactive_webhook.json": ("interactive", "wamid.INTERACTIVE123"),
    }

    for filename, (message_type, message_id) in expected.items():
        payload = json.loads(_body(filename))
        msg = parse_webhook_payload(payload)
        assert msg is not None
        assert msg.message_type == message_type
        assert msg.message_id == message_id
