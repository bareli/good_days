"""Shabbat haftarah (pure, no Home Assistant imports).

Ports Hebcal leyning's rules (specialReadings2 / getHaftaraKey, BSD-2-Clause, Copyright (c) 2020
hebcal) for a Shabbat with a weekly parasha. Shabbatot inside Yom Tov / Chol HaMoed have no parasha
and are not covered. Verified against Hebcal for every Shabbat 2024-2040 (tests/test_haftarah.py).
"""
from __future__ import annotations

import datetime as dt

from hdate import HebrewDate
from hdate.hebrew_date import Months

from .haftarah_data import PARASHA, SPECIAL

ASHKENAZI = "ashkenazi"
SEPHARDI = "sephardi"
NUSACH = (ASHKENAZI, SEPHARDI)

# A combined parasha reads the second one's haftarah, except these two.
COMBINED_HAFTARAH = {
    "vayakhel_pekudei": "pekudei",
    "tazria_metzora": "metzora",
    "achrei_mot_kedoshim": "achrei_mot_kedoshim",
    "behar_bechukotai": "bechukotai",
    "chukat_balak": "balak",
    "matot_masei": "masei",
    "nitzavim_vayeilech": "nitzavim",
}

SPECIAL_KEYS = {
    "shekalim": "Shabbat Shekalim",
    "zachor": "Shabbat Zachor",
    "parah": "Shabbat Parah",
    "hachodesh": "Shabbat HaChodesh",
    "hagadol": "Shabbat HaGadol",
}

BOOKS_HE = {
    "Amos": "עמוס",
    "Ezekiel": "יחזקאל",
    "Hosea": "הושע",
    "I Kings": "מלכים א׳",
    "I Samuel": "שמואל א׳",
    "II Kings": "מלכים ב׳",
    "II Samuel": "שמואל ב׳",
    "Isaiah": "ישעיהו",
    "Jeremiah": "ירמיהו",
    "Joel": "יואל",
    "Joshua": "יהושע",
    "Judges": "שופטים",
    "Malachi": "מלאכי",
    "Micah": "מיכה",
    "Obadiah": "עובדיה",
    "Zechariah": "זכריה",
}

Part = tuple[str, str, str]


def _hd(day: dt.date) -> HebrewDate:
    return HebrewDate.from_gdate(day)


def reading_key(day: dt.date, parasha: str | None, specials: tuple[str, ...]) -> str | None:
    """Hebcal's key for the haftarah of this Shabbat: a SPECIAL key, or 'parasha:<key>'."""
    if not parasha:
        return None
    hd = _hd(day)
    if "chanukah" in specials:
        if hd.day in (30, 1):
            return "Shabbat Rosh Chodesh Chanukah"
        first = HebrewDate(hd.year, Months.KISLEV, 25).to_gdate()
        return "Chanukah Day 8 (on Shabbat)" if (day - first).days + 1 == 8 else "Chanukah Day 1 (on Shabbat)"
    for special in ("shekalim", "zachor", "parah", "hachodesh", "hagadol"):
        if special in specials:
            return SPECIAL_KEYS[special]
    if "shuva" in specials and parasha in ("vayeilech", "haazinu"):
        return "Shabbat Shuva (with Vayeilech)" if parasha == "vayeilech" else "Shabbat Shuva (with Ha'azinu)"
    if parasha == "pinchas" and hd.day > 17:
        return "Pinchas occurring after 17 Tammuz"
    if hd.day in (30, 1):
        return "Masei on Shabbat Rosh Chodesh" if parasha in ("masei", "matot_masei") else "Shabbat Rosh Chodesh"
    if parasha == "ki_teitzei" and hd.day == 14:
        return "Ki Teitzei with 3rd Haftarah of Consolation"
    if parasha == "kedoshim" and hd.day in (26, 28, 6):
        return "Kedoshim following Special Shabbat"
    if hd.month != Months.AV and _hd(day + dt.timedelta(days=1)).day in (30, 1):
        return "Shabbat Machar Chodesh"
    return f"parasha:{COMBINED_HAFTARAH.get(parasha, parasha)}"


def haftarah(day: dt.date, parasha: str | None, specials: tuple[str, ...], nusach: str = ASHKENAZI) -> tuple[Part, ...]:
    key = reading_key(day, parasha, specials)
    if key is None:
        return ()
    ashkenazi, sephardi = PARASHA.get(key[8:], ((), ())) if key.startswith("parasha:") else SPECIAL[key]
    return sephardi if nusach == SEPHARDI else ashkenazi


def replacing_special(
    day: dt.date, parasha: str | None, specials: tuple[str, ...], nusach: str = ASHKENAZI
) -> str | None:
    """The SPECIAL key read this Shabbat when it differs from the weekly parasha's own haftarah."""
    key = reading_key(day, parasha, specials)
    if key is None or key.startswith("parasha:"):
        return None
    weekly = PARASHA.get(COMBINED_HAFTARAH.get(parasha, parasha), ((), ()))
    own = weekly[1] if nusach == SEPHARDI else weekly[0]
    return None if haftarah(day, parasha, specials, nusach) == own else key


def _verse(ref: str, lang: str, gematria) -> str:
    chapter, verse = ref.split(":")
    if lang == "he":
        # Citation style: plain letters (נד:א), without geresh / gershayim.
        def plain(n: int) -> str:
            return gematria(n).replace("׳", "").replace("״", "")

        return f"{plain(int(chapter))}:{plain(int(verse))}"
    return ref


def format_parts(parts: tuple[Part, ...], lang: str, gematria) -> str:
    """'Isaiah 42:5–43:10' / 'ישעיהו מב:ה–מג:י'; parts joined by '; '. `gematria(int) -> str`."""
    out = []
    for book, begin, end in parts:
        name = BOOKS_HE.get(book, book) if lang == "he" else book
        first = _verse(begin, lang, gematria)
        if begin.split(":")[0] == end.split(":")[0]:
            last = _verse(end, lang, gematria).split(":")[1]
        else:
            last = _verse(end, lang, gematria)
        out.append(f"{name} {first}–{last}" if begin != end else f"{name} {first}")
    return "; ".join(out)
