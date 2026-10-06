"""Assist intents: what's coming this week, the next holiday, Shabbat times, the Omer count,
fast times (en / he speech)."""
from __future__ import annotations

import datetime as dt

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import intent
from homeassistant.util import dt as dt_util

from .const import (
    CAT_EREV,
    CAT_ROSH_CHODESH,
    DOMAIN,
    INTENT_FAST,
    INTENT_NEXT_HOLIDAY,
    INTENT_OMER,
    INTENT_SHABBAT,
    INTENT_UPCOMING,
)
from .engine import norm_language, omer_text
from .websocket import resolve_runtime

REGISTERED_KEY = f"{DOMAIN}_intents_registered"
WEEK_DAYS = 7
MAX_SPOKEN = 5

WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "he": ["ביום שני", "ביום שלישי", "ביום רביעי", "ביום חמישי", "ביום שישי", "בשבת", "ביום ראשון"],
}
TEXT = {
    "not_loaded": ("Good Days is not set up.", "ימים טובים לא מוגדר."),
    "week_empty": ("Nothing special in the coming week.", "אין אירועים מיוחדים בשבוע הקרוב."),
    "week": ("Coming up: {items}.", "בשבוע הקרוב: {items}."),
    "today": ("today", "היום"),
    "tomorrow": ("tomorrow", "מחר"),
    "on_day": ("on {day}", "{day}"),
    "evening": ("{when} evening", "{when} בערב"),
    "next_holiday": ("{title}, {when}.", "{title}, {when}."),
    "in_days": ("in {n} days, {on}", "בעוד {n} ימים, {on}"),
    "now": ("{title} is today.", "{title} היום."),
    "none": ("No holiday found in the coming year.", "לא נמצא חג בשנה הקרובה."),
    "shabbat": (
        "Candle lighting {cl_when} at {cl}, havdalah {hv_when} at {hv}.",
        "הדלקת נרות {cl_when} ב-{cl}, הבדלה {hv_when} ב-{hv}.",
    ),
    "shabbat_now": ("{title} ends at {hv}.", "{title} יוצאת ב-{hv}."),
    "yom_tov_now": ("{title} ends at {hv}.", "{title} יוצא ב-{hv}."),
    "title": (" {t}.", " {t}."),
    "omer": ("{text}.", "{text}."),
    "no_omer": ("The Omer is not being counted now.", "עכשיו לא סופרים את העומר."),
    "fast": ("{title} begins {when} at {start} and ends at {end}.", "{title}: תחילת הצום {when} ב-{start}, סוף הצום ב-{end}."),
    "fast_now": ("{title} ends at {end}.", "{title}: הצום מסתיים ב-{end}."),
    "no_fast": ("No fast found in the coming year.", "לא נמצא צום בשנה הקרובה."),
    "and": (" and ", " ו"),
}


def _t(key: str, lang: str, **kw) -> str:
    en, he = TEXT[key]
    return (he if lang == "he" else en).format(**kw)


def _when(day: dt.date, today: dt.date, lang: str) -> str:
    diff = (day - today).days
    if diff <= 0:
        return _t("today", lang)
    if diff == 1:
        return _t("tomorrow", lang)
    return _t("on_day", lang, day=WEEKDAYS[lang][day.weekday()])


def _join(items: list[str], lang: str) -> str:
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + _t("and", lang) + items[-1]


def _hhmm(value: dt.datetime) -> str:
    return dt_util.as_local(value).strftime("%H:%M")


def speech_upcoming(runtime, lang: str, now: dt.datetime) -> str:
    today = dt_util.as_local(now).date()
    end = now + dt.timedelta(days=WEEK_DAYS)
    cats = runtime.categories - {CAT_ROSH_CHODESH, CAT_EREV}
    events = [e for e in runtime.events if e.category in cats and e.end > now and e.start < end]
    events += [e for e in runtime.family_events if e.end > now and e.start < end]
    events.sort(key=lambda e: e.start)
    if not events:
        return _t("week_empty", lang)
    parts = []
    for event in events[:MAX_SPOKEN]:
        day = dt_util.as_local(event.start).date() if not event.all_day else event.first_day
        when = _when(max(day, today), today, lang)
        if not event.all_day and dt_util.as_local(event.start).hour >= 15 and event.start > now:
            when = _t("evening", lang, when=when)  # Shabbat / Yom Tov / yahrzeit begin in the evening
        parts.append(f"{event.title(lang)} {when}")
    return _t("week", lang, items=_join(parts, lang))


def speech_next_holiday(runtime, lang: str, now: dt.datetime) -> str:
    event = runtime.next_holiday(now)
    if event is None:
        return _t("none", lang)
    title = event.title(lang)
    today = dt_util.as_local(now).date()
    if event.covers_day(today) or event.start <= now:
        return _t("now", lang, title=title)
    days = (event.first_day - today).days
    on = _t("on_day", lang, day=WEEKDAYS[lang][event.first_day.weekday()])
    when = _when(event.first_day, today, lang) if days <= 1 else _t("in_days", lang, n=days, on=on)
    return _t("next_holiday", lang, title=title, when=when)


def speech_shabbat(runtime, lang: str, now: dt.datetime) -> str:
    event = runtime.next_shabbat(now)
    if event is None or not event.candle_lighting or not event.havdalah:
        return _t("none", lang)
    title = event.title(lang)
    if event.start <= now:
        key = "yom_tov_now" if event.category == "yom_tov" else "shabbat_now"
        return _t(key, lang, title=title, hv=_hhmm(event.havdalah))
    today = dt_util.as_local(now).date()
    text = _t(
        "shabbat",
        lang,
        cl_when=_when(dt_util.as_local(event.candle_lighting).date(), today, lang),
        cl=_hhmm(event.candle_lighting),
        hv_when=_when(dt_util.as_local(event.havdalah).date(), today, lang),
        hv=_hhmm(event.havdalah),
    )
    # "Shabbat Parashat Tetzaveh (Zachor)", or the holiday name when Yom Tov is part of the period.
    if event.parasha or event.specials or event.category == "yom_tov":
        text += _t("title", lang, t=title)
    return text


def speech_omer(runtime, lang: str, now: dt.datetime) -> str:
    day, _, _ = runtime.omer(now)
    if not day:
        return _t("no_omer", lang)
    return _t("omer", lang, text=omer_text(day, lang, runtime.settings.nusach))


def speech_fast(runtime, lang: str, now: dt.datetime) -> str:
    event = runtime.next_fast(now)
    if event is None or event.all_day:
        return _t("no_fast", lang)
    title = event.title(lang)
    if event.start <= now:
        return _t("fast_now", lang, title=title, end=_hhmm(event.end))
    today = dt_util.as_local(now).date()
    day = dt_util.as_local(event.start).date()
    days = (day - today).days
    when = (
        _when(day, today, lang)
        if days < WEEK_DAYS
        else _t("in_days", lang, n=days, on=_t("on_day", lang, day=WEEKDAYS[lang][day.weekday()]))
    )
    if dt_util.as_local(event.start).hour >= 15:
        when = _t("evening", lang, when=when)  # Tisha B'Av / Yom Kippur begin the evening before
    return _t("fast", lang, title=title, when=when, start=_hhmm(event.start), end=_hhmm(event.end))


class _GoodDaysIntent(intent.IntentHandler):
    def __init__(self, intent_type: str, description: str, speech) -> None:
        self.intent_type = intent_type
        self.description = description
        self._speech = speech

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        lang = norm_language(intent_obj.language or intent_obj.hass.config.language)
        response = intent_obj.create_response()
        try:
            runtime = resolve_runtime(intent_obj.hass)
        except HomeAssistantError:
            response.async_set_speech(_t("not_loaded", lang))
            return response
        response.async_set_speech(self._speech(runtime, lang, dt_util.now()))
        return response


@callback
def async_register_intents(hass: HomeAssistant) -> None:
    if hass.data.get(REGISTERED_KEY):
        return
    hass.data[REGISTERED_KEY] = True
    for intent_type, description, speech in (
        (INTENT_UPCOMING, "What is coming up in the next week (holidays and family dates)", speech_upcoming),
        (INTENT_NEXT_HOLIDAY, "When is the next Jewish holiday", speech_next_holiday),
        (INTENT_SHABBAT, "Candle lighting and havdalah times of the next Shabbat", speech_shabbat),
        (INTENT_OMER, "Today's count of the Omer", speech_omer),
        (INTENT_FAST, "When the next fast begins and ends", speech_fast),
    ):
        intent.async_register(hass, _GoodDaysIntent(intent_type, description, speech))
