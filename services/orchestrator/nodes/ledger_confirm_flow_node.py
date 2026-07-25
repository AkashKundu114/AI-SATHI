from __future__ import annotations

"""Handles the WhatsApp Flow ('ledger_confirm_flow.json') tap-to-confirm
response, as an alternative front door to the same save/correct/discard
logic already in ledger_confirm_node.py.

WHY THIS EXISTS: the person asked that "before taking any db entry, the
tool would verify using whatsapp flows showing them the form and when they
tap yes to save it stores in a permanent db." The existing ledger_confirm_node
already has a confirm/correct/discard loop, but it's driven by free-typed
"হ্যাঁ"/"না" replies — which themselves can be mistyped or mis-transcribed.
A tapped Flow choice removes that specific failure mode: there's no text
to mis-hear or mis-type, just three visible buttons over the exact
numbers that will be saved.

This node does NOT duplicate the save/correction logic — it reuses
ledger_confirm_node's `_save` and the LEDGER_CONFIRM state fields directly,
so there is exactly one code path that ever writes to `ledger_entries`.
Wiring note (graph.py): route a `message_type == "interactive"` turn to
this node instead of `ledger_confirm_node` whenever
`state["awaiting_confirmation"]` is true AND the interactive payload
contains `confirmation_choice` (i.e. it came from this specific Flow, not
the scheme-eligibility Flow) — check `payload.get("confirmation_choice")`
before routing here.
"""

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
