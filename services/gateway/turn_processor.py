from __future__ import annotations

import logging

from services.orchestrator.graph import get_compiled_graph
from shared.whatsapp.sender import send_text

logger = logging.getLogger("turn_processor")


async def process_turn_and_dispatch(whatsapp_number: str, turn_input: dict) -> None:
    try:
        graph = await get_compiled_graph()
        config = {"configurable": {"thread_id": whatsapp_number}}
        state_update = {"whatsapp_number": whatsapp_number, **turn_input}
        result = await graph.ainvoke(state_update, config=config)
    except Exception:
        logger.exception("process_turn failed for %s", whatsapp_number)
        await send_text(whatsapp_number, "দুঃখিত, একটু সমস্যা হয়েছে। আবার চেষ্টা করুন।")
        return

    for msg in result.get("outbound_messages", []):
        try:
            if msg["type"] == "text":
                await send_text(whatsapp_number, msg["body"])
            elif msg["type"] == "document":
                from shared.whatsapp.sender import send_document

                await send_document(whatsapp_number, msg["url"], msg["filename"], msg.get("caption", ""))
            elif msg["type"] == "image":
                from shared.whatsapp.sender import send_image

                await send_image(whatsapp_number, msg["url"], msg.get("caption", ""))
            elif msg["type"] == "flow":
                from shared.whatsapp.sender import send_flow

                response = await send_flow(
                    whatsapp_number,
                    flow_id=msg["flow_id"],
                    header_text=msg["header_text"],
                    body_text=msg["body_text"],
                    cta_text=msg["cta_text"],
                    screen_id=msg["screen_id"],
                    screen_data=msg["screen_data"],
                )
                if response.get("error") or "messages" not in response:
                    logger.warning(
                        "flow send failed for %s, falling back to plain text confirmation: %s",
                        whatsapp_number, response,
                    )
                    fallback_text = (
                        f"{msg['body_text']}\n\n"
                        f"{msg['screen_data'].get('income_lines', '')}\n"
                        f"{msg['screen_data'].get('expense_lines', '')}\n"
                        f"{msg['screen_data'].get('net_profit_line', '')}\n\n"
                        "ঠিক আছে? (হ্যাঁ/না)"
                    )
                    await send_text(whatsapp_number, fallback_text)
        except Exception:
            logger.exception("failed to deliver one outbound message to %s", whatsapp_number)
