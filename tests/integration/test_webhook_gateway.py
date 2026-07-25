import hmac
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from services.gateway import main as gateway
from shared.config.settings import get_settings


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class _FakeRedis:
    def __init__(self):
        self.keys = set()
        self.counts = {}

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.keys:
            return False
        self.keys.add(key)
        return True

    async def incr(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key, seconds):
        return True


def _body(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _signature(body: bytes) -> str:
    secret = get_settings().wa_app_secret.encode()
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_valid_text_webhook_is_deduped_and_dispatched_once(monkeypatch):
    fake_redis = _FakeRedis()
    dispatched = []

    async def _fake_get_redis():
        return fake_redis

    async def _fake_dispatch(msg):
        dispatched.append(msg)

    monkeypatch.setattr(gateway, "get_redis", _fake_get_redis)
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
