from fastapi.testclient import TestClient
from services.gateway import main as gateway


def test_oversized_webhook_body_is_dropped_before_signature_check(monkeypatch):
    dispatched = []

    async def _fake_dispatch(msg):
        dispatched.append(msg)

    monkeypatch.setattr(gateway, "_dispatch_to_orchestrator", _fake_dispatch)

    oversized_body = (
        b'{"entry": [' + b'{"padding": "x"},' * 200_000 + b'{"padding": "x"}]}'
    )
    assert len(oversized_body) > gateway.MAX_WEBHOOK_BODY_BYTES

    client = TestClient(gateway.app)
    response = client.post(
        "/webhook/whatsapp",
        content=oversized_body,
        headers={
            "X-Hub-Signature-256": "sha256=irrelevant",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 200
    assert dispatched == []


def test_normal_sized_body_still_reaches_signature_check(monkeypatch):
    dispatched = []

    async def _fake_dispatch(msg):
        dispatched.append(msg)

    monkeypatch.setattr(gateway, "_dispatch_to_orchestrator", _fake_dispatch)

    small_body = b'{"entry": []}'
    client = TestClient(gateway.app)
    response = client.post(
        "/webhook/whatsapp",
        content=small_body,
        headers={
            "X-Hub-Signature-256": "sha256=irrelevant",
            "content-type": "application/json",
        },
    )

    assert response.status_code == 403
