"""Golden dates for the holiday engine (no Home Assistant needed)."""
from __future__ import annotations

import datetime as dt

import pytest

from custom_components.good_days.engine import EngineSettings, compute, hebrew_date

D = dt.date
ISRAEL = EngineSettings(31.778, 35.235, 754, "Asia/Jerusalem", False, 40, 0)
TEL_AVIV = EngineSettings(32.0853, 34.7818, 0, "Asia/Jerusalem", False, 18, 0)
NEW_YORK = EngineSettings(40.7128, -74.0060, 10, "America/New_York", True, 18, 0)


def by_key(events, key):
    return [e for e in events if key in e.keys]


def year(settings, start=D(2022, 9, 1), end=D(2023, 8, 31)):
    return compute(settings, start, end)


@pytest.mark.parametrize(
    ("key", "first_day"),
    [
        ("rosh_hashana_i", D(2022, 9, 26)),
        ("yom_kippur", D(2022, 10, 5)),
        ("sukkot", D(2022, 10, 10)),
        ("pesach", D(2023, 4, 6)),
        ("shavuot", D(2023, 5, 26)),
    ],
)
def test_yom_tov_dates(key, first_day):
    (event,) = by_key(year(ISRAEL), key)
    assert event.first_day == first_day
    assert event.category == "yom_tov"
    assert not event.all_day and event.period


def test_rosh_hashana_is_one_two_day_period():
    (event,) = by_key(year(ISRAEL), "rosh_hashana_i")
    assert event.keys[:2] == ("rosh_hashana_i", "rosh_hashana_ii")
    assert event.days == 2
    assert event.title("en") == "Rosh Hashana"
    assert event.start.date() == D(2022, 9, 25)  # candle lighting on erev
    assert event.end.date() == D(2022, 9, 27)  # havdalah after day 2


def test_sukkot_israel_one_day_diaspora_two():
    (israel,) = by_key(year(ISRAEL), "sukkot")
    (diaspora,) = by_key(year(NEW_YORK), "sukkot")
    assert israel.days == 1
    assert diaspora.days == 2 and "sukkot_ii" in diaspora.keys
    assert diaspora.start.tzinfo is not None and str(diaspora.start.tzinfo) == "America/New_York"


def test_pesach_2023_israel_first_day_then_chol_hamoed():
    events = year(ISRAEL)
    (pesach,) = by_key(events, "pesach")
    assert (pesach.first_day, pesach.days) == (D(2023, 4, 6), 1)
    (chol,) = by_key(events, "hol_hamoed_pesach")
    assert chol.all_day and chol.category == "chol_hamoed"
    assert (chol.first_day, chol.last_day) == (D(2023, 4, 7), D(2023, 4, 11))
    (seventh,) = by_key(events, "pesach_vii")
    assert seventh.first_day == D(2023, 4, 12)


def test_chanukah_is_one_eight_day_span():
    (chanukah,) = by_key(year(ISRAEL), "chanukah")
    assert chanukah.first_day == D(2022, 12, 19)
    assert chanukah.days == 8
    assert chanukah.all_day and chanukah.category == "minor"


def test_purim_and_shushan_purim():
    events = year(ISRAEL)
    assert [e.first_day for e in by_key(events, "purim")] == [D(2023, 3, 7)]
    assert [e.first_day for e in by_key(events, "shushan_purim")] == [D(2023, 3, 8)]


def test_tisha_bav_nidche_moves_to_sunday():
    events = compute(ISRAEL, D(2022, 7, 1), D(2022, 8, 31))
    (fast,) = by_key(events, "tisha_bav")
    assert fast.first_day == D(2022, 8, 7)  # 9 Av 5782 was Shabbat
    assert fast.first_day.weekday() == 6
    assert fast.category == "fast"


def test_shabbat_period_has_parasha_and_times():
    events = compute(ISRAEL, D(2026, 10, 5), D(2026, 10, 11))
    (shabbat,) = [e for e in events if e.category == "shabbat"]
    assert shabbat.first_day == D(2026, 10, 10)
    assert shabbat.parasha == "bereshit"
    assert shabbat.title("en") == "Shabbat Parashat Bereshit"
    assert shabbat.title("he") == "שבת פרשת בראשית"
    assert shabbat.candle_lighting.date() == D(2026, 10, 9)
    assert shabbat.havdalah.date() == D(2026, 10, 10)
    assert shabbat.start == shabbat.candle_lighting and shabbat.end == shabbat.havdalah
    assert shabbat.uid == "shabbat-2026-10-10"


def test_jerusalem_vs_tel_aviv_candle_lighting():
    jlm = [e for e in compute(ISRAEL, D(2026, 10, 5), D(2026, 10, 11)) if e.category == "shabbat"][0]
    tlv = [e for e in compute(TEL_AVIV, D(2026, 10, 5), D(2026, 10, 11)) if e.category == "shabbat"][0]
    diff = (tlv.candle_lighting - jlm.candle_lighting).total_seconds() / 60
    # 22 minutes of offset difference, a few minutes of sunset difference between the cities.
    assert 18 <= diff <= 26
    assert dt.time(16, 30) < jlm.candle_lighting.time() < dt.time(18, 0)
    assert jlm.havdalah > jlm.candle_lighting + dt.timedelta(hours=24)


def test_yom_tov_next_to_shabbat_is_one_period():
    events = compute(ISRAEL, D(2026, 9, 10), D(2026, 9, 15))
    (rh,) = by_key(events, "rosh_hashana_i")
    assert "shabbat" in rh.keys
    assert rh.title("en") == "Rosh Hashana · Shabbat"
    assert not [e for e in events if e.category == "shabbat"]


def test_rosh_chodesh_two_days_named_by_new_month():
    events = compute(ISRAEL, D(2026, 10, 10), D(2026, 10, 14))
    (rc,) = by_key(events, "rosh_chodesh")
    assert (rc.first_day, rc.days) == (D(2026, 10, 11), 2)
    assert rc.title("en") == "Rosh Chodesh Marcheshvan"


def test_window_boundaries_and_uid_stability():
    wide = compute(ISRAEL, D(2026, 12, 1), D(2026, 12, 31))
    narrow = compute(ISRAEL, D(2026, 12, 10), D(2026, 12, 10))
    uids = {e.uid for e in wide}
    assert {e.uid for e in narrow} <= uids
    # Chanukah started before the narrow window but overlaps it, and is not cut.
    (chanukah,) = by_key(narrow, "chanukah")
    assert (chanukah.first_day, chanukah.days) == (D(2026, 12, 5), 8)
    assert all(e.start < e.end for e in wide)
    assert [e.start for e in wide] == sorted(e.start for e in wide)


def test_hebrew_date_formatting():
    assert hebrew_date(D(2026, 9, 26), "he") == "ט״ו תשרי תשפ״ז"
    assert hebrew_date(D(2026, 9, 26), "en") == "15 Tishrei 5787"


def test_sunset_is_sea_level_whatever_the_elevation():
    """Printed calendars use sea-level sunset; hdate >= 1.2 would shift it by the elevation."""
    high = EngineSettings(31.778, 35.235, 3000, "Asia/Jerusalem", False, 40, 0)
    low = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, 40, 0)
    first = [e for e in compute(high, D(2026, 10, 5), D(2026, 10, 11)) if e.category == "shabbat"][0]
    second = [e for e in compute(low, D(2026, 10, 5), D(2026, 10, 11)) if e.category == "shabbat"][0]
    assert first.candle_lighting == second.candle_lighting
    assert first.candle_lighting.strftime("%H:%M") == "17:34"

