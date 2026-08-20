import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


_DEFAULTS = {
    "WA_PHONE_NUMBER_ID": "test-phone-id",
    "WA_ACCESS_TOKEN": "test-access-token",
    "WA_WEBHOOK_VERIFY_TOKEN": "test-verify-token",
    "WA_APP_SECRET": "test-app-secret",
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
    "REDIS_URL": "redis://localhost:6379/0",
    "SARVAM_API_KEY": "test-sarvam-key",
}

for key, value in _DEFAULTS.items():
    os.environ.setdefault(key, value)
