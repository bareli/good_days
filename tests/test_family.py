"""Family dates: Hebrew-date recurrence rules and validation (no Home Assistant needed)."""
from __future__ import annotations

import datetime as dt

import pytest
from hdate import HebrewDate
from hdate.hebrew_date import Months

from custom_components.good_days.engine import EngineSettings
from custom_components.good_days.family import (
    compute_family,
    hebrew_from_gregorian,
    next_occurrence,
    occurrences_in_year,
)
from custom_components.good_days.storage import validate_date

D = dt.date
ISRAEL = EngineSettings(31.778, 35.235, 754, "Asia/Jerusalem", False, 40, 0)


def rec(**kw):
    return {"id": "x", "name": "Noa", "kind": "birthday", "hebrew_day": 14, "hebrew_month": "adar", **kw}


def test_plain_adar_birthday_goes_to_adar_ii_in_leap_year():
    assert occurrences_in_year(rec(), 5785) == [D(2025, 3, 14)]  # plain year: Purim
    assert occurrences_in_year(rec(), 5784) == [D(2024, 3, 24)]  # leap: 14 Adar II


def test_plain_adar_yahrzeit_defaults_to_adar_i():
    assert occurrences_in_year(rec(kind="yahrzeit"), 5784) == [D(2024, 2, 23)]  # Purim Katan


def test_adar_rule_both_and_override():
    assert occurrences_in_year(rec(kind="yahrzeit", adar_rule="both"), 5784) == [D(2024, 2, 23), D(2024, 3, 24)]
    assert occurrences_in_year(rec(adar_rule="adar_i"), 5784) == [D(2024, 2, 23)]


def test_leap_year_adar_i_date_in_plain_year_is_adar():
    record = rec(hebrew_month="adar_i")
    assert occurrences_in_year(record, 5784) == [D(2024, 2, 23)]
    assert occurrences_in_year(record, 5785) == [D(2025, 3, 14)]


def test_30_cheshvan_in_short_year():
    record = rec(hebrew_day=30, hebrew_month="marcheshvan")
    assert Months.MARCHESHVAN.days(5784) == 29
    assert occurrences_in_year(record, 5784) == [HebrewDate(5784, Months.KISLEV, 1).to_gdate()]
    assert occurrences_in_year({**record, "day30_rule": "29"}, 5784) == [
        HebrewDate(5784, Months.MARCHESHVAN, 29).to_gdate()
    ]
    assert occurrences_in_year(record, 5785) == [HebrewDate(5785, Months.MARCHESHVAN, 30).to_gdate()]


def test_30_adar_i_in_plain_year_moves_to_nisan():
    record = rec(hebrew_day=30, hebrew_month="adar_i")
    assert occurrences_in_year(record, 5785) == [HebrewDate(5785, Months.NISAN, 1).to_gdate()]


def test_birthday_all_day_with_age():
    (event,) = compute_family([rec(original_year=5745)], ISRAEL, D(2025, 3, 1), D(2025, 3, 31))
    assert event.all_day and event.first_day == D(2025, 3, 14)
    assert event.years == 40
    assert event.title("en") == "Noa's birthday (40)"
    assert event.title("he") == "יום הולדת 40 לNoa"
    assert event.uid == "family-x-2025-03-14"


def test_yahrzeit_is_timed_from_sunset_the_evening_before():
    record = rec(kind="yahrzeit", name="Saba", hebrew_day=10, hebrew_month="tevet", original_year=5770)
    (event,) = compute_family([record], ISRAEL, D(2026, 12, 1), D(2026, 12, 31))
    assert event.first_day == D(2026, 12, 20)  # 10 Tevet 5787
    assert not event.all_day
    assert event.start.date() == D(2026, 12, 19) and event.end.date() == D(2026, 12, 20)
    assert dt.time(16, 0) < event.start.time() < dt.time(17, 30)
    assert event.years == 17
    assert event.title("en") == "Yahrzeit: Saba (17)"


def test_occurrences_before_the_original_year_are_skipped():
    record = rec(kind="yahrzeit", original_year=5787, hebrew_month="nisan", hebrew_day=1)
    assert compute_family([record], ISRAEL, D(2026, 1, 1), D(2026, 12, 31)) == []


def test_next_occurrence_and_converter():
    now = dt.datetime(2025, 3, 15, 12, tzinfo=dt.timezone.utc)
    nxt = next_occurrence(rec(), ISRAEL, now)
    assert nxt.first_day == D(2026, 3, 3)  # 14 Adar 5786
    assert hebrew_from_gregorian(D(2024, 3, 24)) == {
        "hebrew_day": 14, "hebrew_month": "adar_ii", "hebrew_year": 5784, "leap_year": True,
    }
    assert hebrew_from_gregorian(D(2024, 3, 23), after_sunset=True)["hebrew_day"] == 14


@pytest.mark.parametrize(
    ("patch", "field", "error"),
    [
        ({"name": " "}, "name", "invalid_name"),
        ({"kind": "party"}, "kind", "invalid_kind"),
        ({"hebrew_month": "adar_iii"}, "hebrew_month", "invalid_month"),
        ({"hebrew_day": 30, "hebrew_month": "tevet"}, "hebrew_day", "invalid_day"),
        ({"hebrew_day": 0}, "hebrew_day", "invalid_day"),
        ({"hebrew_day": 2.5}, "hebrew_day", "invalid_day"),
        ({"original_year": 1990}, "original_year", "invalid_year"),
        ({"adar_rule": "adar_iii"}, "adar_rule", "invalid_adar_rule"),
        ({"day30_rule": "30"}, "day30_rule", "invalid_day30_rule"),
        ({"reminder_days": [1, 90]}, "reminder_days", "invalid_reminder_days"),
        ({"reminder_days": ["x"]}, "reminder_days", "invalid_reminder_days"),
        ({"notes": "n" * 501}, "notes", "invalid_notes"),
        ({"gregorian_date": "2024-13-01"}, "gregorian_date", "invalid_date"),
    ],
)
def test_validation_errors(patch, field, error):
    _, errors = validate_date({**rec(), **patch})
    assert errors == {field: error}


def test_validation_cleans_and_converts_gregorian():
    clean, errors = validate_date(
        {"name": "  Noa ", "kind": "birthday", "gregorian_date": "2024-03-23", "after_sunset": True, "reminder_days": [3, "1", 1]}
    )
    assert errors == {}
    assert clean["name"] == "Noa"
    assert (clean["hebrew_day"], clean["hebrew_month"], clean["original_year"]) == (14, "adar_ii", 5784)
    assert clean["reminder_days"] == [1, 3]


def test_validation_patch_keeps_existing_fields():
    existing = {**rec(), "original_year": 5745, "reminder_days": [1], "notes": "", "adar_rule": None, "day30_rule": None}
    clean, errors = validate_date({"name": "Noa B."}, existing)
    assert errors == {}
    assert clean["name"] == "Noa B." and clean["original_year"] == 5745 and clean["hebrew_day"] == 14
