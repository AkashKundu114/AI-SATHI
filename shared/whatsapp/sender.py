import logging
import uuid

import httpx

from shared.config.settings import get_settings

logger = logging.getLogger("whatsapp_sender")

WA_API = "https://graph.facebook.com/v19.0/{phone_id}/messages"
_TIMEOUT = 15.0


async def _post(payload: dict) -> dict:
    s = get_settings()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                WA_API.format(phone_id=s.wa_phone_number_id),
                headers={"Authorization": f"Bearer {s.wa_access_token}"},
                json=payload,
            )
            if r.status_code >= 400:
                logger.warning("whatsapp send failed: %s %s", r.status_code, r.text[:500])
            return r.json()
    except Exception as exc:
        logger.error("whatsapp send raised: %s", exc)
        return {"error": str(exc)}


async def send_text(to: str, body: str) -> dict:
    return await _post(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": body[:4096], "preview_url": False},
        }
    )


async def send_document(to: str, url: str, filename: str, caption: str = "") -> dict:
    return await _post(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {"link": url, "filename": filename, "caption": caption[:1024]},
        }
    )


async def send_image(to: str, url: str, caption: str = "") -> dict:
    return await _post(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": url, "caption": caption[:1024]},
        }
    )


async def send_flow(
    to: str,
    *,
    flow_id: str,
    header_text: str,
    body_text: str,
    cta_text: str,
    screen_id: str,
    screen_data: dict,
    footer_text: str = "",
) -> dict:
    """Sends a WhatsApp Flow message — the piece ledger_confirm_flow.json
    needed to ever actually reach a user (Pass 2 built the JSON and the
    node that consumes a tap reply; nothing could send the form itself
    until this function existed).

    OPEN VERIFICATION ITEM, same honesty standard as this codebase's other
    unverified integrations (Sarvam Vision's product-photo scope,
    Flux Pro's endpoint shape — see model_router.py and
    flux_poster_client.py): the payload shape below follows Meta's
    documented "flow_action: navigate" pattern for a STATIC flow (no
    server-side data-exchange endpoint, no flow encryption keys needed) —
    the same category of Flow this repo's existing
    scheme_eligibility_flow.json already assumes, since nothing in this
    codebase implements the Flow data-exchange webhook Meta requires for
    DYNAMIC flows. Confirm against your app's current Flow configuration
    (published vs. draft, endpoint URI set or not) before relying on this
    in production. If Meta rejects the payload, this function returns
    whatever error body Meta sent (visible in the return dict / logs) —
    it does not silently pretend to succeed.

    Falls back to plain text if `flow_id` is blank (Flow not configured) —
    callers should check `settings.wa_ledger_confirm_flow_id` before
    calling this, but this function itself refuses rather than sending a
    malformed request with an empty flow_id.
    """
    if not flow_id:
        raise ValueError("send_flow called with an empty flow_id — check WA_LEDGER_CONFIRM_FLOW_ID is set")

    flow_token = uuid.uuid4().hex  # opaque per-send token; not currently used to
    # correlate a response back to server-side state beyond what the Flow's
    # own returned payload already carries (confirmation_choice) — see the
    # note in ledger_confirm_flow_node.py. A dynamic flow with a real
    # data-exchange endpoint would use this token for session binding;
    # this static flow doesn't need to.

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "header": {"type": "text", "text": header_text[:60]},
            "body": {"text": body_text[:1024]},
            "footer": {"text": footer_text[:60]} if footer_text else None,
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_token": flow_token,
                    "flow_id": flow_id,
                    "flow_cta": cta_text[:20],
                    "flow_action": "navigate",
                    "flow_action_payload": {
                        "screen": screen_id,
                        "data": screen_data,
                    },
                },
            },
        },
    }
    # Meta rejects a null "footer" key rather than just ignoring it.
    if payload["interactive"]["footer"] is None:
        del payload["interactive"]["footer"]

    return await _post(payload)
