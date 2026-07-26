import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.knowledge.context import get_context_for_agents, DISTRICT_MELAS


def test_no_district_gives_no_melas():
    ctx = get_context_for_agents(month=1, district=None)
    assert ctx["upcoming_district_melas"] == []


def test_matching_district_and_month_surfaces_mela():
    ctx = get_context_for_agents(month=1, district="South 24 Parganas")
    slugs = {m["slug"] for m in ctx["upcoming_district_melas"]}
    assert "gangasagar_mela" in slugs


def test_matching_district_wrong_month_gives_no_mela():
    ctx = get_context_for_agents(month=6, district="South 24 Parganas")
    slugs = {m["slug"] for m in ctx["upcoming_district_melas"]}
    assert "gangasagar_mela" not in slugs


def test_district_match_is_case_insensitive_and_substring_tolerant():
    ctx = get_context_for_agents(month=1, district="birbhum district")
    slugs = {m["slug"] for m in ctx["upcoming_district_melas"]}
    assert "joydev_kenduli_mela" in slugs


def test_unrelated_district_gives_no_mela():
    ctx = get_context_for_agents(month=1, district="Murshidabad")
    assert ctx["upcoming_district_melas"] == []


def test_tusu_mela_spans_two_months_and_two_districts_worth_of_matching():
    dec_ctx = get_context_for_agents(month=12, district="Purulia")
    jan_ctx = get_context_for_agents(month=1, district="Purulia")
    dec_slugs = {m["slug"] for m in dec_ctx["upcoming_district_melas"]}
    jan_slugs = {m["slug"] for m in jan_ctx["upcoming_district_melas"]}
    assert "tusu_mela" in dec_slugs
    assert "tusu_mela" in jan_slugs


def test_every_district_mela_has_a_source_note():
    for m in DISTRICT_MELAS:
        assert m.source_note.strip()


def test_block_param_still_accepted_without_error_for_backward_compat():
    ctx = get_context_for_agents(month=1, block="Some Block")
    assert ctx["upcoming_district_melas"] == []
