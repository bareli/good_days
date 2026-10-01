"""#43 (UX-018): label and citation stay together; a special reading that replaces the weekly one is marked."""
from __future__ import annotations

import datetime as dt

from custom_components.good_days.engine import HAFTARAH_MARKS, EngineSettings, compute
from custom_components.good_days.haftarah import ASHKENAZI, SEPHARDI, reading_key, replacing_special
from custom_components.good_days.haftarah_data import SPECIAL

from .test_v07 import DIASPORA, ISRAEL

NBSP = chr(0xA0)
ISRAEL_SEPHARDI = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, 40, 0, nusach=SEPHARDI)


def _shabbat(settings: EngineSettings, day: dt.date):
    return [e for e in compute(settings, day, day) if e.is_shabbat][0]


def test_issue_43_machar_chodesh_is_marked():
    event = _shabbat(ISRAEL, dt.date(2026, 10, 10))  # Bereshit 5787, Sunday is Rosh Chodesh
    assert event.haftarah_reading("en") == "I Samuel 20:18–42 (Machar Chodesh)"
    assert event.haftarah_reading("he") == "שמואל א׳ כ:יח–מב (מחר חודש)"
    assert f"Haftarah:{NBSP}I Samuel 20:18–42 (Machar Chodesh)" in event.description("en")
    assert f"הפטרה:{NBSP}שמואל א׳ כ:יח–מב (מחר חודש)" in event.description("he")


def test_issue_43_specials_are_marked_weekly_is_not():
    assert _shabbat(ISRAEL, dt.date(2027, 3, 6)).haftarah_reading("he").endswith("(שקלים)")
    assert _shabbat(ISRAEL, dt.date(2026, 12, 5)).haftarah_reading("he").endswith("(שבת חנוכה)")
    assert _shabbat(ISRAEL, dt.date(2027, 1, 9)).haftarah_reading("he").endswith("(ראש חודש)")
    weekly = _shabbat(ISRAEL, dt.date(2026, 10, 17))  # Noach
    assert weekly.haftarah_special is None
    assert weekly.haftarah_reading("en") == weekly.haftarah_text("en") == "Isaiah 54:1–55:5"


def test_issue_43_citation_style_kept():
    # No geresh in verse numbers, the repeated book name stays (owner's ruling).
    yitro = next(e for e in compute(ISRAEL, dt.date(2027, 1, 1), dt.date(2027, 3, 1)) if e.parasha == "yitro")
    assert yitro.haftarah_text("he") == "ישעיהו ו:א–ז:ו; ישעיהו ט:ה–ו"


def test_issue_43_every_special_reading_has_a_mark():
    assert set(HAFTARAH_MARKS) == set(SPECIAL)
    assert all(en and he for en, he in HAFTARAH_MARKS.values())


def test_issue_43_no_mark_when_the_special_equals_the_weekly_reading():
    # Kedoshim after a special Shabbat: Ashkenazim read Acharei Mot's haftarah; the Sephardi one is unchanged.
    found = 0
    for settings in (ISRAEL, DIASPORA):
        for event in compute(settings, dt.date(2024, 1, 1), dt.date(2040, 12, 31)):
            if event.parasha != "kedoshim":
                continue
            day = event.first_day if event.first_day.weekday() == 5 else event.last_day
            if reading_key(day, event.parasha, event.specials) == "Kedoshim following Special Shabbat":
                assert replacing_special(day, event.parasha, event.specials, ASHKENAZI) == "Kedoshim following Special Shabbat"
                assert replacing_special(day, event.parasha, event.specials, SEPHARDI) is None
                found += 1
    assert found
