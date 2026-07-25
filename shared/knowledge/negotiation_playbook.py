from __future__ import annotations

"""Negotiation technique knowledge, shared by negotiation_node.py and the
new price_chat_node.py.

IMPORTANT — how this is used, to stay consistent with this codebase's
existing safety pattern (see docs/red-team-agents-v2.md CRIT-1 and
negotiation_node.py's module docstring): these are STRATEGY LABELS and
short coaching phrases, not templates that get filled with a number. The
LLM is told which strategy applies to the current turn and asked for a
digit-free line reflecting it; the actual price is always interpolated
from code (pricing_node._recommend / negotiation_node._compute_counter_offer).
This file never produces a price itself.

Techniques below are standard, widely-taught negotiation concepts
(anchoring, BATNA, reciprocity, silence, bundling, walk-away power) — not
proprietary or invented. Translated into short, warm Bengali phrasing
appropriate for a friendly seller coaching a WhatsApp bot, not a
boardroom.
"""

from dataclasses import dataclass


@dataclass
class NegotiationTactic:
    slug: str
    name_english: str
    when_to_use: str
    coaching_line_bengali: str


TACTICS: list[NegotiationTactic] = [
    NegotiationTactic(
        "anchor_high", "Anchoring",
        "Very first offer in a negotiation — before any counter has been made.",
        "প্রথমেই একটু বেশি দাম বলুন — পরে কমানোর জায়গা থাকবে।",
    ),
    NegotiationTactic(
        "know_your_floor", "BATNA / walk-away price",
        "Always, before any negotiation starts.",
        "সর্বনিম্ন দাম আগে থেকেই ঠিক করে রাখুন — তার নিচে কখনো রাজি হবেন না।",
    ),
    NegotiationTactic(
        "silence", "Strategic silence",
        "After stating a price — don't rush to fill the pause.",
        "দাম বলার পর একটু চুপ থাকুন — তাড়াহুড়ো করে কমাবেন না।",
    ),
    NegotiationTactic(
        "reciprocity", "Reciprocity — give a little, ask a little",
        "Customer is close to the floor but wants a small extra concession.",
        "একটু ছাড় দিলে পরিবর্তে কিছু চান — যেমন নগদে পুরো টাকা এখনই, বা বেশি পরিমাণে অর্ডার।",
    ),
    NegotiationTactic(
        "bundling", "Bundling",
        "Customer wants a lower unit price — offer volume instead of discount.",
        "দাম কমানোর বদলে বেশি পরিমাণে দিন — প্রতি ইউনিটে লাভ একই থাকবে।",
    ),
    NegotiationTactic(
        "justify_with_value", "Value justification, not apology",
        "Whenever holding firm or countering — explain quality/cost, don't sound defensive.",
        "দাম ধরে রাখার সময় পণ্যের মান বা তৈরির খরচ বলুন — ক্ষমা চাওয়ার সুরে নয়।",
    ),
    NegotiationTactic(
        "time_pressure_awareness", "Recognize urgency without exploiting it",
        "Seller has signaled they need cash soon (festival, family event) — don't let the bot itself pressure the seller into a bad price.",
        "তাড়াতাড়ি টাকা দরকার হলেও, সর্বনিম্ন দামের নিচে যাবেন না — এটা মনে করিয়ে দিন সহায়কভাবে।",
    ),
    NegotiationTactic(
        "graceful_walkaway", "Graceful walk-away",
        "Customer's offer stays below floor after the max negotiation turns.",
        "বিনয়ীভাবে জানান এই দামে সম্ভব না, পরে আবার যোগাযোগ করার সুযোগ খোলা রাখুন।",
    ),
    NegotiationTactic(
        "repeat_customer_goodwill", "Repeat-customer goodwill",
        "This buyer has negotiated/bought before (if known from prior CatalogCreation/negotiation history).",
        "পুরনো কাস্টমারকে সামান্য অগ্রাধিকার দেওয়া যেতে পারে, তবে সর্বনিম্ন দামের নিচে নয়।",
    ),
]


def tactic_for(situation_slug: str) -> NegotiationTactic | None:
    return next((t for t in TACTICS if t.slug == situation_slug), None)


def choose_tactic(turn: int, offer_vs_floor_ratio: float, is_repeat_customer: bool = False) -> NegotiationTactic:
    """Deterministic tactic selection — no LLM involved in picking the
    strategy, only in phrasing the chosen one. `offer_vs_floor_ratio` =
    offer / floor (e.g. 0.8 means offer is 20% below floor)."""
    if turn == 1:
        return tactic_for("anchor_high")
    if is_repeat_customer and offer_vs_floor_ratio >= 0.9:
        return tactic_for("repeat_customer_goodwill")
    if offer_vs_floor_ratio >= 0.95:
        return tactic_for("reciprocity")
    if offer_vs_floor_ratio < 0.7:
        return tactic_for("justify_with_value")
    return tactic_for("bundling")
