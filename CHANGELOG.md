# Changelog

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
