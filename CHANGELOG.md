# Changelog

## v0.3.0 (2026-09-30)

Reminders, Assist, blueprint.

- Family-date reminders: notify targets, reminder time, per-date days before (on the day, 1 / 3 / 7 days in the panel). A yahrzeit's "on the day" is the evening it begins, an hour before sunset, with the candle time in the message. Phones get **Got it** / **Remind me tomorrow** buttons. Reminders due on Shabbat or Yom Tov wait until after havdalah (option). Sent reminders are remembered across restarts; no burst of old reminders on first run.
- `good_days_reminder` event for automations.
- Assist intents `GoodDaysUpcoming`, `GoodDaysNextHoliday`, `GoodDaysShabbatTimes` with ready-made English and Hebrew sentences (`docs/assist`).
- Blueprint: lights on before candle lighting, optionally off after havdalah.
- Times now always use sea-level sunset, like printed calendars. hdate 1.2 (Home Assistant 2026.9+) would otherwise add the elevation and move candle lighting about 3 minutes later in Jerusalem. The elevation field was removed from the settings.

## v0.2.0 (2026-09-30)

Family dates by Hebrew date.

- Birthdays, yahrzeits, anniversaries and other dates that repeat by Hebrew date, stored per instance.
- Rules per date: plain Adar in a leap year (defaults: birthdays Adar II, yahrzeits Adar I; or Adar I / Adar II / both), Adar I / II dates in plain years, missing 30 Cheshvan / Kislev / Adar I (1st of next month or 29th).
- Yahrzeits are timed events from sunset the evening before to sunset; others all-day. Age / number of years when the Hebrew year is known.
- `calendar.good_days_family`, `sensor.good_days_next_family_date`.
- Sidebar panel **Good Days**: list with next occurrence and countdown, add / edit dialog (Hebrew or Gregorian date with after-sunset converter), delete confirmation, inline validation matching the server, en/he RTL, keyboard and screen-reader friendly.
- Services `add_date`, `update_date`, `remove_date`, `list_dates`; WebSocket `good_days/dates/*`.
- Card: family dates merged by default (category `family`), kind icons, "falls on Shabbat" badge for family dates too.
- Hebrew dates write Adar I / II with a geresh (אדר א׳ / אדר ב׳).

## v0.1.1 (2026-09-30)

- CI: HACS validation skipped while the repository is private (it downloads files unauthenticated). No functional changes.

## v0.1.0 (2026-09-30)

First release.

- Holiday engine on `hdate` (offline): Shabbat and Yom Tov as timed periods (candle lighting to havdalah, adjacent days merged), other holidays as all-day spans (Chanukah, Chol HaMoed, Rosh Chodesh named by month). Israel or diaspora. Works with hdate 1.1.2 and 1.2.x.
- `calendar.good_days_holidays` with category filter; ranges outside the cached window are computed on demand.
- Sensors `next_shabbat` (timestamp, havdalah, parasha, days until, in effect) and `next_holiday`; binary sensor `holiday_today`.
- WebSocket `good_days/upcoming`: holidays merged with external calendars (`calendar.get_events`), sorted, limited, with Hebrew date, in-effect and Shabbat-conflict flags; unreadable calendars reported, not fatal.
- Config flow with server-side validation; defaults copied once from the core Jewish Calendar entry if present. Options flow (location, offsets, language, categories, look-ahead) merges into existing options.
- `custom:good-days-card`: day groups with Hebrew dates, countdown chips, candle lighting, Now banner during Shabbat / Yom Tov, expandable details, compact one-line variant, visual editor, en/he with RTL, keyboard focus kept across refreshes. Auto-registered as a Lovelace resource.
- English and Hebrew translations generated from one table (`scripts/gen_strings.py`).
