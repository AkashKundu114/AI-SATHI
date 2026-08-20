from __future__ import annotations

import json
import logging

from langgraph.graph import StateGraph, END


from services.orchestrator.state import ConversationState
from services.orchestrator.nodes.user_profile_node import load_user_profile_node
from services.orchestrator.nodes.input_guard_node import input_guard_node
from services.orchestrator.nodes.onboarding_node import onboarding_node
from services.orchestrator.nodes.intent_router import classify_intent
from services.orchestrator.nodes.ledger_node import ledger_extract_node
from services.orchestrator.nodes.ledger_confirm_node import ledger_confirm_node
from services.orchestrator.nodes.ledger_confirm_flow_node import ledger_confirm_flow_node
from services.orchestrator.nodes.ledger_report_node import ledger_report_node
from services.orchestrator.nodes.conversation_node import general_conversation_node
from services.orchestrator.nodes.market_predictor_node import market_predictor_node
from services.orchestrator.nodes.pricing_node import pricing_node
from services.orchestrator.nodes.negotiation_node import negotiation_node
from services.orchestrator.nodes.price_chat_node import price_chat_node
from services.orchestrator.nodes.catalog_node import catalog_node
from shared.config.settings import get_settings

logger = logging.getLogger("graph")


def _interactive_payload(state: ConversationState) -> dict:
    if state.get("last_message_type") != "interactive":
        return {}
    try:
        return json.loads(state.get("raw_input_text") or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}


def _route_after_profile_load(state: ConversationState) -> str:
    if state.get("is_new_user") or (
        state.get("onboarding_step") and state["onboarding_step"] != "DONE"
    ):
        return "onboarding"

    if state.get("awaiting_confirmation"):
        raw_text = (state.get("raw_input_text") or state.get("raw_input_transcript") or "").strip().lower()
        new_txn_indicators = [
            "bikri", "বিক্রি", "kheyechi", "খেয়েছি", "bechechi", "বেচেছি",
            "kinlam", "কিনলাম", "kinechi", "কিনেছি", "dhar diyechi", "ধার দিয়েছি",
            "bikro korechi", "বিক্রি করেছি"
        ]
        words = set(raw_text.split())
        is_simple_confirm = any(w in words for w in ["ha", "na", "yes", "no", "ok", "হবে", "হ্যাঁ", "না"])
        if any(ind in raw_text for ind in new_txn_indicators) and not is_simple_confirm:
            state["pending_ledger_entry"] = None
            state["awaiting_confirmation"] = False
            return "classify_intent"

        payload = _interactive_payload(state)
        if "confirmation_choice" in payload:
            return "ledger_confirm_flow"
        return "ledger_confirm"


    if state.get("awaiting_negotiation"):
        return "negotiation"

    if state.get("awaiting_price_chat"):
        return "price_chat"

    if state.get("last_message_type") == "image":
        return "catalog"

    return "classify_intent"


def _route_after_input_guard(state: ConversationState) -> str:
    if state.get("guardrail_blocked"):
        return "end"
    return _route_after_profile_load(state)


def _route_after_intent(state: ConversationState) -> str:
    feature = state.get("active_feature", "IDLE")
    if feature == "LEDGER":
        return "ledger"
    if feature == "LEDGER_REPORT":
        return "ledger_report"
    if feature == "MARKET":
        return "market"
    if feature == "PRICING":
        return "pricing"
    if feature == "NEGOTIATION":
        return "negotiation"
    if feature == "PRICE_CHAT":
        return "price_chat"
    return "unhandled"


def _route_after_price_chat(state: ConversationState) -> str:
    if not state.get("awaiting_price_chat") and state.get("agreed_price") is not None:
        return "catalog"
    return "end"


def build_graph() -> StateGraph:
    graph = StateGraph(ConversationState)

    graph.add_node("load_user_profile", load_user_profile_node)
    graph.add_node("input_guard", input_guard_node)
    graph.add_node("onboarding", onboarding_node)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("ledger", ledger_extract_node)
    graph.add_node("ledger_confirm", ledger_confirm_node)
    graph.add_node("ledger_confirm_flow", ledger_confirm_flow_node)
    graph.add_node("ledger_report", ledger_report_node)
    graph.add_node("unhandled", general_conversation_node)
    graph.add_node("catalog", catalog_node)
    graph.add_node("market", market_predictor_node)
    graph.add_node("pricing", pricing_node)
    graph.add_node("negotiation", negotiation_node)
    graph.add_node("price_chat", price_chat_node)

    graph.set_entry_point("load_user_profile")
    graph.add_edge("load_user_profile", "input_guard")

    graph.add_conditional_edges(
        "input_guard",
        _route_after_input_guard,
        {
            "onboarding": "onboarding",
            "ledger_confirm": "ledger_confirm",
            "ledger_confirm_flow": "ledger_confirm_flow",
            "classify_intent": "classify_intent",
            "negotiation": "negotiation",
            "price_chat": "price_chat",
            "catalog": "catalog",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "classify_intent",
        _route_after_intent,
        {
            "ledger": "ledger",
            "ledger_report": "ledger_report",
            "market": "market",
            "pricing": "pricing",
            "negotiation": "negotiation",
            "price_chat": "price_chat",
            "unhandled": "unhandled",
        },
    )
    graph.add_conditional_edges(
        "price_chat",
        _route_after_price_chat,
        {
            "catalog": "catalog",
            "end": END,
        },
    )

    graph.add_edge("onboarding", END)
    graph.add_edge("ledger", END)
    graph.add_edge("ledger_confirm", END)
    graph.add_edge("ledger_confirm_flow", END)
    graph.add_edge("ledger_report", END)
    graph.add_edge("unhandled", END)
    graph.add_edge("catalog", END)
    graph.add_edge("market", END)
    graph.add_edge("pricing", END)
    graph.add_edge("negotiation", END)

    return graph


_compiled_graph = None


async def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    s = get_settings()
    checkpointer = None
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        checkpointer_ctx = AsyncPostgresSaver.from_conn_string(s.database_url)
        checkpointer = await checkpointer_ctx.__aenter__()
        await checkpointer.setup()
    except Exception as exc:
        logger.info("PostgreSQL checkpointer unavailable (%s) — falling back to MemorySaver", exc)
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()

    graph = build_graph()
    _compiled_graph = graph.compile(checkpointer=checkpointer)
    return _compiled_graph
