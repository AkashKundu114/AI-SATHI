from __future__ import annotations

import json

from services.orchestrator.state import ConversationState
from services.orchestrator.nodes.ledger_confirm_node import _save, _reset_with_message


async def ledger_confirm_flow_node(state: ConversationState) -> dict:
    pending = state.get("pending_ledger_entry")
    if not pending:
        return _reset_with_message("একটু সমস্যা হয়েছে। আবার হিসাব বলুন।", trace="ledger_confirm_flow_node:no_pending")

    try:
        payload = json.loads(state.get("raw_input_text") or "{}")
    except (json.JSONDecodeError, TypeError):
        payload = {}

    choice = payload.get("confirmation_choice")

    if choice == "confirm_save":
        return await _save(state, pending)

    if choice == "discard":
        return _reset_with_message(
            "হিসাবটা বাদ দেওয়া হলো। পরে আবার বলুন।",
            trace="ledger_confirm_flow_node:discarded_via_flow",
        )

    if choice == "needs_correction":
        return {
            "awaiting_confirmation": True,
            "ledger_confirmation_turns": state.get("ledger_confirmation_turns", 0),
            "outbound_messages": [
                {"type": "text", "body": "ঠিক আছে, কী ভুল হয়েছে ভয়েসে বা লিখে বলুন — যেমন: 'দাম ৪০০ টাকা, ৩০০ নয়'"}
            ],
            "trace": ["ledger_confirm_flow_node:awaiting_correction_text"],
        }

    return {
        "awaiting_confirmation": True,
        "ledger_confirmation_turns": state.get("ledger_confirmation_turns", 0),
        "outbound_messages": [{"type": "text", "body": "বুঝলাম না, আবার ফর্মে বেছে নিন।"}],
        "trace": ["ledger_confirm_flow_node:unrecognized_choice"],
    }
