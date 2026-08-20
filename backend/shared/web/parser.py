from dataclasses import dataclass

@dataclass
class ParsedMessage:
    message_id: str
    from_number: str
    message_type: str
    text: str | None = None
    audio_bytes: bytes | None = None
    image_bytes: bytes | None = None
    interactive_payload: dict | None = None

def parse_webhook_payload(payload: dict) -> ParsedMessage | None:
    # Dummy parser for Web UI webhooks
    if not payload:
        return None
    return ParsedMessage(
        message_id=payload.get("id", "test-123"),
        from_number=payload.get("from", "web-user"),
        message_type=payload.get("type", "text"),
        text=payload.get("text", "")
    )
