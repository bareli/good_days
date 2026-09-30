"""#18 (BUG-006): the Shabbat hold option says what the code does (sent an hour before candle lighting)."""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "good_days"


def _init(lang: str) -> dict:
    data = json.loads((ROOT / "translations" / f"{lang}.json").read_text(encoding="utf-8"))
    return data["options"]["step"]["init"]


def test_issue_18_hold_wording_matches_behaviour() -> None:
    en, he = _init("en"), _init("he")
    assert en["data"]["quiet_on_shabbat"] == "No reminders during Shabbat and Yom Tov"
    assert en["data_description"]["quiet_on_shabbat"] == (
        "A reminder due on Shabbat or Yom Tov is sent an hour before candle lighting."
    )
    assert he["data"]["quiet_on_shabbat"] == "לא לשלוח תזכורות בשבת ובחג"
    assert he["data_description"]["quiet_on_shabbat"] == "תזכורת שחלה בשבת או בחג תישלח שעה לפני הדלקת הנרות."
    assert "havdalah" not in json.dumps(en["data_description"]["quiet_on_shabbat"])
