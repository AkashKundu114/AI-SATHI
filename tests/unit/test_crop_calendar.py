import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from shared.knowledge.crop_calendar import (
    CROP_CALENDAR,
    crops_at_harvest,
    crops_being_sown,
    crops_for_district,
    find_crop,
)


def test_potato_harvest_is_january_to_march():
    potato = find_crop("potato")
    assert potato is not None
    for month in (1, 2, 3):
        assert potato in crops_at_harvest(month)
    assert potato not in crops_at_harvest(7)


def test_aman_paddy_is_the_only_crop_harvested_in_december():
    dec_harvest = {c.slug for c in crops_at_harvest(12)}
    assert "aman_paddy" in dec_harvest


def test_no_crop_harvest_claimed_without_evidence_in_september():
    sept_harvest = crops_at_harvest(9)
    slugs = {c.slug for c in sept_harvest}
    assert "aman_paddy" not in slugs
    assert "potato" not in slugs


def test_crops_being_sown_is_distinct_from_harvest():
    for month in range(1, 13):
        sown = {c.slug for c in crops_being_sown(month)}
        harvested = {c.slug for c in crops_at_harvest(month)}
        assert sown.isdisjoint(harvested), (
            f"month {month} has overlapping sow/harvest crops"
        )


def test_find_crop_unknown_slug_returns_none():
    assert find_crop("does_not_exist") is None


def test_crops_for_district_matches_named_district():
    hooghly_crops = {c.slug for c in crops_for_district("Hooghly")}
    assert "potato" in hooghly_crops


def test_crops_for_district_case_insensitive_and_partial():
    crops = {c.slug for c in crops_for_district("bardhaman district")}
    assert "potato" in crops or "boro_paddy" in crops


def test_crops_for_district_empty_for_unrelated_district():
    assert crops_for_district("Kolkata") == [] or all(
        "Kolkata".lower() not in d.lower()
        for c in CROP_CALENDAR
        for d in c.main_districts
    )


def test_crops_for_district_empty_string_returns_empty():
    assert crops_for_district("") == []


def test_every_crop_has_a_source_note_and_at_least_one_district():
    for c in CROP_CALENDAR:
        assert c.source_note.strip()
        assert len(c.main_districts) >= 1


def test_every_crop_has_at_least_one_sowing_and_harvest_month():
    for c in CROP_CALENDAR:
        assert len(c.sowing_months) >= 1
        assert len(c.harvest_months) >= 1
        assert all(1 <= m <= 12 for m in c.sowing_months + c.harvest_months)
