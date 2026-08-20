from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class IncomingMessage:
    message_id: str
    from_number: str
    timestamp: int
    message_type: Literal["text", "audio", "image", "document", "interactive"]
    text: Optional[str] = None
    audio_id: Optional[str] = None
    audio_mime_type: Optional[str] = None
    image_id: Optional[str] = None
    caption: Optional[str] = None
    interactive_payload: Optional[dict] = None
    audio_bytes: Optional[bytes] = None
    image_bytes: Optional[bytes] = None


ParsedMessage = IncomingMessage


def parse_webhook_payload(payload: dict) -> Optional[IncomingMessage]:
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]["value"]
        if "messages" not in change:
            return None

        msg = change["messages"][0]
        base = IncomingMessage(
            message_id=msg["id"],
            from_number=msg["from"],
            timestamp=int(msg.get("timestamp", 0)),
            message_type=msg["type"],
        )

        if msg["type"] == "text":
            base.text = msg.get("text", {}).get("body", "")
        elif msg["type"] == "audio":
            base.audio_id = msg.get("audio", {}).get("id")
            base.audio_mime_type = msg.get("audio", {}).get("mime_type")
        elif msg["type"] == "image":
            base.image_id = msg.get("image", {}).get("id")
            base.caption = msg.get("image", {}).get("caption")
        elif msg["type"] == "interactive" and msg.get("interactive", {}).get("type") == "nfm_reply":
            import json

            base.interactive_payload = json.loads(msg["interactive"]["nfm_reply"]["response_json"])

        return base
    except (KeyError, IndexError, TypeError, ValueError):
        pass

    # Support generic web payload format as fallback
    try:
        if "message_id" in payload or "id" in payload:
            return IncomingMessage(
                message_id=payload.get("message_id") or payload.get("id", "web-msg-id"),
                from_number=payload.get("from_number") or payload.get("from", "web-user"),
                timestamp=int(payload.get("timestamp", 0)),
                message_type=payload.get("message_type") or payload.get("type", "text"),
                text=payload.get("text"),
                audio_bytes=payload.get("audio_bytes"),
                image_bytes=payload.get("image_bytes"),
                interactive_payload=payload.get("interactive_payload"),
            )
    except Exception:
        pass

    return None
