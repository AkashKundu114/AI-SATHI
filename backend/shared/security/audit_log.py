from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

audit_logger = logging.getLogger("security_audit")


def log_security_event(
    event_type: str,
    *,
    source_ip: str | None = None,
    user_id: str | None = None,
    phone_number: str | None = None,
    details: dict | None = None,
) -> None:

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "source_ip": source_ip or "unknown",
        "user_id": user_id or "anonymous",
        "phone_number": phone_number or "unknown",
        "details": details or {},
    }
    audit_logger.warning("SECURITY_EVENT: %s", json.dumps(payload))
