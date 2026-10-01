"""#40 (UX-015): a Shabbat glued to Yom Tov labels its reading "Shabbat haftarah" / "הפטרת שבת"."""
from __future__ import annotations

import datetime as dt

from homeassistant.core import HomeAssistant

from custom_components.good_days.const import DOMAIN
from custom_components.good_days.engine import compute

from .conftest import make_entry, setup_entry
from .test_v07 import ISRAEL

NBSP = chr(0xA0)


def _shabbat(start: dt.date, end: dt.date):
    return [e for e in compute(ISRAEL, start, end) if e.is_shabbat][0]


def test_issue_40_shavuot_shabbat_labels_the_shabbat_haftarah():
    # Shavuot 5787 (Friday 11 June 2027, Israel) runs into Shabbat Naso: one period titled by the holiday.
    event = _shabbat(dt.date(2027, 6, 10), dt.date(2027, 6, 12))
    assert event.title("en") == "Shavuot · Shabbat"
    assert event.haftarah_label("en") == "Shabbat haftarah"
    assert event.haftarah_label("he") == "הפטרת שבת"
    assert f"Parashat Nasso · Shabbat{NBSP}haftarah:{NBSP}Judges 13:2–25" in event.description("en")
    assert f"הפטרת{NBSP}שבת:{NBSP}שופטים יג:ב–כה" in event.description("he")


def test_issue_40_plain_shabbat_keeps_haftarah_label():
    event = _shabbat(dt.date(2026, 10, 15), dt.date(2026, 10, 17))
    assert event.haftarah_label("en") == "Haftarah"
    assert event.haftarah_label("he") == "הפטרה"
    assert f"Haftarah:{NBSP}Isaiah 54:1–55:5" in event.description("en")


async def test_issue_40_ws_sends_the_label(hass: HomeAssistant, israel, hass_ws_client) -> None:
    ws = await hass_ws_client(hass)
    await setup_entry(hass, make_entry(hass, language="he"))
    await ws.send_json_auto_id({"type": f"{DOMAIN}/upcoming", "days": 400, "limit": 100, "language": "he"})
    items = (await ws.receive_json())["result"]["items"]
    shavuot = next(i for i in items if i["uid"] == "yom_tov-2027-06-11")
    assert shavuot["haftarah_label"] == "הפטרת שבת"
    assert shavuot["haftarah"] == "שופטים יג:ב–כה"
    plain = next(i for i in items if i["category"] == "shabbat" and i["haftarah"])
    assert plain["haftarah_label"] == "הפטרה"
    assert all(i["haftarah_label"] is None for i in items if not i["haftarah"])
