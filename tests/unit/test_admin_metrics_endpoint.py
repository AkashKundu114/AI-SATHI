from fastapi.testclient import TestClient

from services.gateway.main import app
from shared.config.settings import get_settings

client = TestClient(app)


def test_admin_metrics_email_unauthorized(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "admin_api_token", "secret_admin_token_123")

    # Missing token header
    response = client.post("/admin/metrics/email")
    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized"

    # Wrong token header
    response = client.post("/admin/metrics/email", headers={"X-Admin-Token": "wrong_token"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized"


def test_admin_metrics_email_authorized(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "admin_api_token", "secret_admin_token_123")

    response = client.post(
        "/admin/metrics/email?to=admin@example.com",
        headers={"X-Admin-Token": "secret_admin_token_123"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["message"] == "Metrics report email queued"
