"""Holiday engine: Shabbat / Yom Tov periods and holiday days, computed offline with hdate.

Pure Python (no Home Assistant imports) so it runs in an executor and in plain unit tests.
"""
from __future__ import annotations

import contextvars
import datetime as dt
from collections.abc import Iterator
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from hdate import HebrewDate, Location, Zmanim
from hdate.hebrew_date import Months, is_leap_year
from hdate.gematria import hebrew_number
from hdate.holidays import HolidayDatabase, HolidayTypes
from hdate.parasha import ParashaDatabase

from .haftarah import ASHKENAZI, format_parts, haftarah as _haftarah
from hdate.translations import TRANSLATIONS
from hdate.translator import set_language

from .const import (
    CAT_CHOL_HAMOED,
    CAT_EREV,
    CAT_FAST,
    CAT_MEMORIAL,
    CAT_MINOR,
    CAT_MODERN,
    CAT_ROSH_CHODESH,
    CAT_SHABBAT,
    CAT_YOM_TOV,
    CATEGORIES,
    DEFAULT_CANDLE_LIGHTING,
    DEFAULT_HAVDALAH,
)

ONE_DAY = dt.timedelta(days=1)
# Longest all-day span is Chanukah (8 days); Shabbat / Yom Tov periods are at most 3 days.
# Padding the scan by more than that means no event inside the window is ever cut.
PAD_DAYS = 10
SHABBAT = "shabbat"
ROSH_CHODESH = "rosh_chodesh"
SATURDAY = 5

TYPE_CATEGORY = {
    "YOM_TOV": CAT_YOM_TOV,
    "EREV_YOM_TOV": CAT_EREV,
    "HOL_HAMOED": CAT_CHOL_HAMOED,
    "MELACHA_PERMITTED_HOLIDAY": CAT_MINOR,
    "MINOR_HOLIDAY": CAT_MINOR,
    "FAST_DAY": CAT_FAST,
    "MODERN_HOLIDAY": CAT_MODERN,
    "ISRAEL_NATIONAL_HOLIDAY": CAT_MEMORIAL,
    "MEMORIAL_DAY": CAT_MEMORIAL,
    "ROSH_CHODESH": CAT_ROSH_CHODESH,
}
NAME_CATEGORY = {
    # hdate types these as erev days; for a family view they are Chol HaMoed.
    "hoshana_raba": CAT_CHOL_HAMOED,
    "hol_hamoed_pesach": CAT_CHOL_HAMOED,
    # Major Israeli days, not the minor memorial days.
    "yom_hazikaron": CAT_MODERN,
    "yom_hashoah": CAT_MODERN,
}

# Titles of Shabbat / Yom Tov periods: consecutive days of one festival share a title.
PERIOD_GROUP = {
    "rosh_hashana_i": "rosh_hashana",
    "rosh_hashana_ii": "rosh_hashana",
    "sukkot_ii": "sukkot",
    "pesach_ii": "pesach",
    "pesach_viii": "pesach_vii",
    "shavuot_ii": "shavuot",
}
PERIOD_TITLES = {
    SHABBAT: ("Shabbat", "שבת"),
    "rosh_hashana": ("Rosh Hashana", "ראש השנה"),
    "yom_kippur": ("Yom Kippur", "יום כיפור"),
    "sukkot": ("Sukkot", "סוכות"),
    "shmini_atzeret": ("Shmini Atzeret", "שמיני עצרת"),
    "simchat_torah": ("Simchat Torah", "שמחת תורה"),
    "pesach": ("Pesach", "פסח"),
    "pesach_vii": ("Shvi'i shel Pesach", "שביעי של פסח"),
    "shavuot": ("Shavuot", "שבועות"),
}
TEXT = {
    "parashat": ("Parashat", "פרשת"),
    "haftarah": ("Haftarah", "הפטרה"),
    "rosh_chodesh": ("Rosh Chodesh", "ראש חודש"),
    "candle_lighting": ("Candle lighting", "הדלקת נרות"),
    "havdalah": ("Havdalah", "הבדלה"),
}
SEPARATOR = " · "

# Special Shabbatot. Title ones are appended in parentheses; notes only go to the description.
SPECIAL_TITLE = ["shuva", "shekalim", "zachor", "parah", "hachodesh", "hagadol", "chazon",
                 "nachamu", "shira", "rosh_chodesh", "chanukah", "chol_hamoed"]
SPECIAL_NOTE = ["machar_chodesh", "mevarchim"]
SPECIALS = {
    "shuva": ("Shuva", "שובה"),
    "shekalim": ("Shekalim", "שקלים"),
    "zachor": ("Zachor", "זכור"),
    "parah": ("Parah", "פרה"),
    "hachodesh": ("HaChodesh", "החודש"),
    "hagadol": ("HaGadol", "הגדול"),
    "chazon": ("Chazon", "חזון"),
    "nachamu": ("Nachamu", "נחמו"),
    "shira": ("Shira", "שירה"),
    "rosh_chodesh": ("Rosh Chodesh", "ראש חודש"),
    "chanukah": ("Chanukah", "חנוכה"),
    "chol_hamoed": ("Chol HaMoed", "חול המועד"),
    "machar_chodesh": ("Machar Chodesh", "מחר חודש"),
    "mevarchim": ("Mevarchim Chodesh {month}", "מברכים חודש {month}"),
}


def norm_language(language: str | None) -> str:
    """'he' for any Hebrew locale, otherwise 'en'."""
    return "he" if str(language or "").lower().startswith("he") else "en"


def _t(table: dict, key: str, lang: str) -> str:
    en, he = table[key]
    return he if lang == "he" else en


def _hdate_tr(section: str, key: str, lang: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(section, {}).get(key, key)


@dataclass(frozen=True)
class EngineSettings:
    latitude: float
    longitude: float
    elevation: float  # kept for compatibility; zmanim use sea level
    time_zone: str
    diaspora: bool
    candle_lighting: int = DEFAULT_CANDLE_LIGHTING
    havdalah: int = DEFAULT_HAVDALAH
    nusach: str = ASHKENAZI  # haftarah custom: ashkenazi | sephardi


@dataclass(frozen=True)
class HolyEvent:
    """One calendar event: a Shabbat / Yom Tov period (timed) or a holiday span (all-day)."""

    uid: str
    category: str
    keys: tuple[str, ...]  # hdate holiday names, plus "shabbat"
    first_day: dt.date  # first Gregorian day of the holiday itself (not the erev)
    days: int
    start: dt.datetime  # aware; local midnight of first_day when all_day
    end: dt.datetime  # aware, exclusive
    all_day: bool
    period: bool  # Shabbat / Yom Tov with candle lighting and havdalah
    candle_lighting: dt.datetime | None = None
    havdalah: dt.datetime | None = None
    parasha: str | None = None  # hdate Parasha key, plain Shabbat only
    month: str | None = None  # hdate Months key: Rosh Chodesh, or the month blessed (Mevarchim)
    specials: tuple[str, ...] = ()  # SPECIALS keys of the run's Shabbat (when it is not Yom Tov)
    haftarah: tuple[tuple[str, str, str], ...] = ()  # (book, from, to) parts, Shabbat with a parasha

    @property
    def last_day(self) -> dt.date:
        return self.first_day + dt.timedelta(days=self.days - 1)

    @property
    def is_shabbat(self) -> bool:
        return SHABBAT in self.keys

    def overlaps(self, start: dt.datetime, end: dt.datetime) -> bool:
        return self.start < end and self.end > start

    def covers_day(self, day: dt.date) -> bool:
        return self.first_day <= day <= self.last_day

    def parasha_name(self, lang: str) -> str | None:
        return _hdate_tr("Parasha", self.parasha, lang) if self.parasha else None

    def title(self, lang: str) -> str:
        if self.period:
            groups: list[str] = []
            for key in self.keys:
                group = PERIOD_GROUP.get(key, key)
                if group not in groups:
                    groups.append(group)
            if groups == [SHABBAT]:
                title = _t(PERIOD_TITLES, SHABBAT, lang)
                shown = [self.special_name(k, lang) for k in self.specials if k in SPECIAL_TITLE]
                if self.parasha:
                    title = f"{title} {_t(TEXT, 'parashat', lang)} {self.parasha_name(lang)}"
                    return f"{title} ({', '.join(shown)})" if shown else title
                return f"{title} {', '.join(shown)}" if shown else title
            return SEPARATOR.join(
                _t(PERIOD_TITLES, g, lang) if g in PERIOD_TITLES else _hdate_tr("Holiday", g, lang)
                for g in groups
            )
        if self.keys[0] == ROSH_CHODESH and self.month:
            return f"{_t(TEXT, 'rosh_chodesh', lang)} {_hdate_tr('Months', self.month, lang)}"
        return _hdate_tr("Holiday", self.keys[0], lang)

    def special_name(self, key: str, lang: str) -> str:
        month = _hdate_tr("Months", self.month, lang) if self.month else ""
        return _t(SPECIALS, key, lang).format(month=month)

    def haftarah_text(self, lang: str) -> str | None:
        return format_parts(self.haftarah, lang, _gematria) if self.haftarah else None

    def description(self, lang: str) -> str:
        parts = [hebrew_date(self.first_day, lang)]
        parts += [self.special_name(k, lang) for k in self.specials if k in SPECIAL_NOTE]
        if self.parasha and self.category == CAT_YOM_TOV:
            # A Shabbat glued to Yom Tov: the title names the holiday, so name the parasha here.
            parts.append(f"{_t(TEXT, 'parashat', lang)} {self.parasha_name(lang)}")
        if self.haftarah:
            parts.append(f"{_t(TEXT, 'haftarah', lang)}: {self.haftarah_text(lang)}")
        if self.candle_lighting:
            parts.append(f"{_t(TEXT, 'candle_lighting', lang)} {self.candle_lighting:%H:%M}")
        if self.havdalah:
            parts.append(f"{_t(TEXT, 'havdalah', lang)} {self.havdalah:%H:%M}")
        return SEPARATOR.join(parts)


def _gematria(num: int) -> str:
    """Hebrew numerals with proper geresh / gershayim, without touching hdate's global language."""

    def run() -> str:
        set_language("he")
        return hebrew_number(num)

    return (
        contextvars.copy_context().run(run).replace('"', "״").replace("'", "׳")
    )


def hebrew_date(day: dt.date, lang: str) -> str:
    """'ט״ו תשרי תשפ״ז' in Hebrew, '15 Tishrei 5787' in English."""
    hd = HebrewDate.from_gdate(day)
    month = _hdate_tr("Months", hd.month.name.lower(), lang)
    if lang == "he":
        if hd.month.name in ("ADAR_I", "ADAR_II") and not month.endswith(("׳", "'")):
            month += "׳"  # hdate writes plain "אדר א" / "אדר ב"
        return f"{_gematria(hd.day)} {month} {_gematria(hd.year % 1000)}"
    return f"{hd.day} {month} {hd.year}"


def _category(name: str, type_name: str) -> str:
    return NAME_CATEGORY.get(name) or TYPE_CATEGORY.get(type_name, CAT_MINOR)


def _midnight(day: dt.date, tz: ZoneInfo) -> dt.datetime:
    return dt.datetime.combine(day, dt.time.min, tz)


def make_location(settings: EngineSettings) -> Location:
    return Location(
        name="Home",
        latitude=settings.latitude,
        longitude=settings.longitude,
        timezone=ZoneInfo(settings.time_zone),
        # Sea-level sunset, as printed calendars use. hdate >= 1.2 would otherwise add the
        # elevation and make candle lighting later (about 3 min in Jerusalem).
        altitude=0,
        diaspora=settings.diaspora,
    )


def compute(settings: EngineSettings, start: dt.date, end: dt.date) -> list[HolyEvent]:
    """All events overlapping the local days start..end (inclusive), sorted by start."""
    tz = ZoneInfo(settings.time_zone)
    holidays_db = HolidayDatabase(settings.diaspora)
    parasha_db = ParashaDatabase(settings.diaspora)
    location = make_location(settings)

    days: list[tuple[dt.date, HebrewDate, list]] = []
    day = start - dt.timedelta(days=PAD_DAYS)
    while day <= end + dt.timedelta(days=PAD_DAYS):
        hd = HebrewDate.from_gdate(day)
        days.append((day, hd, holidays_db.lookup(hd)))
        day += ONE_DAY

    events = [
        *_periods(days, settings, location, parasha_db, tz),
        *_spans(days, tz),
    ]
    lo, hi = _midnight(start, tz), _midnight(end + ONE_DAY, tz)
    events = [e for e in events if e.overlaps(lo, hi)]
    events.sort(key=lambda e: (e.start, CATEGORIES.index(e.category), e.uid))
    return events


def _is_holy(day: dt.date, holidays: list) -> bool:
    return day.weekday() == SATURDAY or any(h.type == HolidayTypes.YOM_TOV for h in holidays)


def _periods(days, settings, location, parasha_db, tz) -> Iterator[HolyEvent]:
    holy = [_is_holy(d, hs) for d, _, hs in days]
    i = 0
    while i < len(days):
        if not holy[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(days) and holy[j + 1]:
            j += 1
        if i > 0 and j < len(days) - 1:  # runs cut by the padded range are outside the window
            yield _period(days[i : j + 1], settings, location, parasha_db, tz)
        i = j + 1


def _zmanim(day: dt.date, settings: EngineSettings, location: Location) -> Zmanim:
    return Zmanim(
        date=day,
        location=location,
        candle_lighting_offset=settings.candle_lighting,
        havdalah_offset=settings.havdalah,
    )


def _period(run, settings, location, parasha_db, tz) -> HolyEvent:
    keys: list[str] = []
    for _, _, holidays in run:
        for h in holidays:
            if h.type == HolidayTypes.YOM_TOV and h.name not in keys:
                keys.append(h.name)
    yom_tov = bool(keys)
    if any(d.weekday() == SATURDAY for d, _, _ in run):
        keys.append(SHABBAT)

    first_day, last_day = run[0][0], run[-1][0]
    try:
        candle = _zmanim(first_day - ONE_DAY, settings, location).candle_lighting
        havdalah = _zmanim(last_day, settings, location).havdalah
    except (ValueError, ArithmeticError):  # no sunset (polar day / night)
        candle = havdalah = None

    parasha, specials, blessed = None, (), None
    # The Shabbat of the run, when it is not itself Yom Tov (e.g. Shabbat right before Pesach or
    # right after Rosh Hashana): it keeps its weekly parasha and special Shabbatot.
    shabbat = next(
        (r for r in run if r[0].weekday() == SATURDAY and not any(h.type == HolidayTypes.YOM_TOV for h in r[2])),
        None,
    )
    if shabbat is not None:
        found = parasha_db.lookup(shabbat[1])
        if found.value:
            parasha = found.name.lower()
        specials, blessed = _specials(shabbat[0], shabbat[1], shabbat[2], parasha)
    reading = _haftarah(shabbat[0], parasha, specials, settings.nusach) if shabbat is not None else ()

    category = CAT_YOM_TOV if yom_tov else CAT_SHABBAT
    timed = candle is not None and havdalah is not None
    return HolyEvent(
        uid=f"{category}-{first_day.isoformat()}",
        category=category,
        keys=tuple(keys),
        first_day=first_day,
        days=len(run),
        start=candle if timed else _midnight(first_day, tz),
        end=havdalah if timed else _midnight(last_day + ONE_DAY, tz),
        all_day=not timed,
        period=True,
        candle_lighting=candle,
        havdalah=havdalah,
        parasha=parasha,
        specials=specials,
        month=blessed,
        haftarah=reading,
    )


def _gday(year: int, month: Months, day: int) -> dt.date:
    return HebrewDate(year, month, day).to_gdate()


def _specials(day: dt.date, hd: HebrewDate, holidays: list, parasha: str | None) -> tuple[tuple[str, ...], str | None]:
    """Special Shabbatot of a plain Shabbat, plus the month blessed on Shabbat Mevarchim."""
    year = hd.year
    purim_month = Months.ADAR_II if is_leap_year(year) else Months.ADAR
    names = {h.name for h in holidays}

    def before(target: dt.date) -> int:
        return (target - day).days

    found: list[str] = []
    if hd.month == Months.TISHREI and 3 <= hd.day <= 9:
        found.append("shuva")
    if 0 <= before(_gday(year, purim_month, 1)) <= 6:
        found.append("shekalim")
    if 1 <= before(_gday(year, purim_month, 14)) <= 6:
        found.append("zachor")
    nisan = before(_gday(year, Months.NISAN, 1))
    if 7 <= nisan <= 13:
        found.append("parah")
    if 0 <= nisan <= 6:
        found.append("hachodesh")
    if 1 <= before(_gday(year, Months.NISAN, 15)) <= 7:
        found.append("hagadol")
    tisha_bav = before(_gday(year, Months.AV, 9))
    if 0 <= tisha_bav <= 6:
        found.append("chazon")
    if -7 <= tisha_bav <= -1:
        found.append("nachamu")
    if parasha == "beshalach":
        found.append("shira")
    rosh_chodesh = ROSH_CHODESH in names
    if rosh_chodesh:
        found.append("rosh_chodesh")
    if "chanukah" in names:
        found.append("chanukah")
    if any(n.startswith("hol_hamoed") for n in names):
        found.append("chol_hamoed")

    blessed = None
    next_month = hd.month.next_month(year) if hd.month != Months.ELUL else None
    if next_month is not None and not rosh_chodesh:
        # Rosh Chodesh starts on the 30th when the month has 30 days.
        first_rc_day = (
            _gday(year, hd.month, 30) if hd.month.days(year) == 30 else _gday(year, next_month, 1)
        )
        to_rc = before(first_rc_day)
        if to_rc == 1:
            found.append("machar_chodesh")  # Sunday is Rosh Chodesh
        if 1 <= to_rc <= 7:
            found.append("mevarchim")
            blessed = next_month.name.lower()
    return tuple(found), blessed


def _spans(days, tz) -> Iterator[HolyEvent]:
    """Consecutive days of the same (non Yom Tov) holiday become one all-day event."""
    open_spans: dict[str, list] = {}
    closed: list[list] = []
    for day, hd, holidays in days:
        for h in holidays:
            if h.type == HolidayTypes.YOM_TOV:
                continue
            month = hd.month.name.lower() if h.name == ROSH_CHODESH else None
            span = open_spans.get(h.name)
            if span and span[1] == day - ONE_DAY:
                span[1] = day
                span[3] = month
                continue
            if span:
                closed.append(span)
            open_spans[h.name] = [day, day, h, month]
    closed.extend(open_spans.values())

    for first, last, h, month in closed:
        category = _category(h.name, h.type.name)
        yield HolyEvent(
            uid=f"{category}-{h.name}-{first.isoformat()}",
            category=category,
            keys=(h.name,),
            first_day=first,
            days=(last - first).days + 1,
            start=_midnight(first, tz),
            end=_midnight(last + ONE_DAY, tz),
            all_day=True,
            period=False,
            month=month,
        )
