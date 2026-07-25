import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.knowledge.negotiation_playbook import choose_tactic, tactic_for, TACTICS
from services.orchestrator.nodes.cross_verify import check_numeric_integrity
from shared.knowledge.context import find_life_event, life_events_by_community, LIFE_EVENTS


# --- negotiation_playbook.choose_tactic (now wired into negotiation_node) --

def test_first_turn_always_anchors():
    t = choose_tactic(turn=1, offer_vs_floor_ratio=0.5)
    assert t.slug == "anchor_high"


def test_close_to_floor_uses_reciprocity():
    t = choose_tactic(turn=2, offer_vs_floor_ratio=0.97)
    assert t.slug == "reciprocity"


def test_far_below_floor_uses_value_justification():
    t = choose_tactic(turn=2, offer_vs_floor_ratio=0.5)
    assert t.slug == "justify_with_value"


def test_repeat_customer_near_floor_gets_goodwill():
    t = choose_tactic(turn=2, offer_vs_floor_ratio=0.95, is_repeat_customer=True)
    assert t.slug == "repeat_customer_goodwill"


def test_repeat_customer_far_below_floor_still_justifies_value():
    # Being a repeat customer doesn't override a genuinely low offer.
    t = choose_tactic(turn=2, offer_vs_floor_ratio=0.4, is_repeat_customer=True)
    assert t.slug == "justify_with_value"


def test_every_tactic_has_a_non_empty_coaching_line():
    for t in TACTICS:
        assert t.coaching_line_bengali.strip()


def test_tactic_for_unknown_slug_returns_none():
    assert tactic_for("does_not_exist") is None


# --- cross_verify.check_numeric_integrity (deterministic half of Pass 4's
# cross-agent verification -- the dignity half needs a live model call and
# isn't tested offline here) -----------------------------------------------

def test_numeric_integrity_passes_when_amount_matches():
    result = check_numeric_integrity("প্রস্তাব: ₹৩০০।", allowed_amounts=[300.0])
    assert result["numeric_ok"] is True
    assert result["unmatched_amounts"] == []


def test_numeric_integrity_catches_invented_amount():
    # The model was only ever told about 300 and 500 -- if it writes 999,
    # that's a hallucinated number that must not reach the user.
    result = check_numeric_integrity("প্রস্তাব: ₹৯৯৯।", allowed_amounts=[300.0, 500.0])
    assert result["numeric_ok"] is False
    assert 999.0 in result["unmatched_amounts"]


def test_numeric_integrity_within_rounding_tolerance():
    result = check_numeric_integrity("₹৩০০.৫", allowed_amounts=[300.0], tolerance=1.0)
    # Bengali digits don't include a decimal point in the regex; this
    # should still extract 300 as the integer part via digit matching.
    assert result["numeric_ok"] is True


def test_numeric_integrity_no_amounts_in_text_is_trivially_ok():
    result = check_numeric_integrity("ধন্যবাদ, শীঘ্রই যোগাযোগ করব।", allowed_amounts=[300.0])
    assert result["numeric_ok"] is True
    assert result["found_amounts"] == []


# --- context.py life_events_by_community (Pass 4: Muslim Bengali entries) --

def test_muslim_bengali_events_present():
    events = life_events_by_community("muslim_bengali")
    slugs = {e.slug for e in events}
    assert {"nikah", "walima", "aqiqah"}.issubset(slugs)


def test_shared_event_not_duplicated_into_either_community_list():
    # Gaye Holud is "shared", not "hindu_bengali" or "muslim_bengali" --
    # callers combine explicitly, it's not silently duplicated.
    hindu = {e.slug for e in life_events_by_community("hindu_bengali")}
    muslim = {e.slug for e in life_events_by_community("muslim_bengali")}
    assert "gaye_holud" not in hindu
    assert "gaye_holud" not in muslim
    assert find_life_event("gaye_holud").community == "shared"


def test_every_life_event_has_a_source_note():
    # Every entry must document where its information came from -- no
    # fabricated occasions without at least a general-knowledge label.
    for e in LIFE_EVENTS:
        assert e.source_note.strip()
