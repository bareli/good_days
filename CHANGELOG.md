# Changelog

## v0.6.1 (2026-10-01)

- Calendar link: family notes are no longer included by default; an admin can opt in with "Include family notes" in the panel (they become visible to the calendar provider). Existing links keep working; notes disappear from them until opted in.

## v0.6.0 (2026-10-01)

Fixes from a full QA cycle on a real Home Assistant (29 issues, #6 to #34).

- **Shabbat timers**: saving, deleting, duplicating and "run now" from the panel work again (the panel's language field was rejected) (#17). Non-admin users can no longer switch timers off, skip a Shabbat or change the profile through the entities; automations still can (#6). Targets are limited to devices that switch on and off (scripts, automations, locks, covers and valves removed); a device that cannot be switched is logged as failed, not done (#9). Several timers firing together write the store once (#14).
- **Panel**: view and edit another profile's timers without making it active; profiles show a timer count and can be renamed (#23). A skipped Shabbat is shown as skipped and the reset is explained (#25). Non-admins see why the timers are read-only (#26). "Run now" names what it does (#24). Two Good Days instances are told apart by name (#34). The Hebrew year accepts letters (תש״ע) (#22). Device picker, colours and long names are accessible (#11, #15, #16, #19). Faster with many family dates (#13).
- **Card**: keyboard focus stays in place across refreshes (#10). A clear summary of the next Shabbat / Chag with candle lighting and havdalah, readable on a wall tablet (#20). Compact mode shows the next candle lighting, not a holiday already in progress (#21). Day headers in gematria (#31). Yahrzeit rows say what the time means (#29). The editor shows the categories really in use (#28). Findable as "ימים טובים" in the card picker (#27). Merges a second Good Days instance's calendar (#33). Contrast and narrow screens (#15, #16, #19).
- **Settings**: the Shabbat reminder option now says reminders are sent before candle lighting (#18); reminder time without seconds and clearer units (#30).
- **Robustness**: reminder buttons only act on real dates (#7); NaN / Infinity inputs give a field error instead of a crash (#8); "upcoming" cuts to the limit before building items (#12).
- **Hebrew in English titles**: family names are isolated so they keep their order (#32). Note: sensor states such as `sensor.good_days_next_family_date` now contain invisible direction marks around names; an automation comparing that state to a plain string must strip them.
- **New**: `sensor.good_days_next_candle_lighting` stays; new websocket `good_days/entries`; `good_days/upcoming` returns the effective `categories`.

## v0.5.0 (2026-09-30)

Shabbat timers.

- New **Shabbat timers** tab in the panel: turn devices on / off around candle lighting and havdalah, or at a time on each holy day (every day / first / last / Erev); applies to Shabbat, Yom Tov and / or Yom Kippur; multi-day Chag + Shabbat handled as one stretch.
- Conditions per timer (Home Assistant conditions, checked when it fires), profiles with an active-profile select (new profile can copy another), duplicate, presets (hot plate, urn, evening / morning lights, AC), run now.
- Preview (dry run) of the next Shabbat / Chag with exact times, before-candle-lighting / after-havdalah marks and conflict reports; history of the last 100 runs.
- Fires once and never fights a manual change; after a restart, actions up to 10 minutes late still run, older ones are logged as missed.
- Entities: `switch.good_days_shabbat_timers`, `switch.good_days_skip_next_shabbat_or_chag`, `select.good_days_timer_profile`, `sensor.good_days_next_timer_action`.
- Changing timers needs an admin; everyone can see them.
- Source files now use escape sequences for bidi isolates (they held the invisible characters); a test enforces it.

## v0.4.0 (2026-09-30)

Torah details, calendar subscription, polish.

- Special Shabbatot computed from the Hebrew calendar (Adar II in leap years, Chazon on Tisha B'Av when it falls on Shabbat): Shuva, Shekalim, Zachor, Parah, HaChodesh, HaGadol, Chazon, Nachamu, Shira, Rosh Chodesh, Chanukah, Chol HaMoed in the Shabbat title ("Shabbat Parashat Mishpatim (Shekalim)"); Mevarchim Chodesh and Machar Chodesh in the details. New `special_shabbat` attribute on `sensor.good_days_next_shabbat`; Assist reads the full title.
- Calendar subscription: private ICS link of family dates (optionally Shabbat and holidays) for Google Calendar / phones, managed by admins in the panel (on / off, include holidays, new link). Off by default.
- Panel: date rows no longer squeeze names on phones.
- New `sensor.good_days_next_candle_lighting` (Shabbat or Yom Tov). The blueprint now uses it: before, Shabbat was missed when an all-day event (Chanukah, a Friday fast, Chol HaMoed) was on the calendar that Friday. Re-import the blueprint.
- Reminders due on Shabbat / Yom Tov are sent an hour before candle lighting (before: held until havdalah, and lost when the date itself had ended by then).
- Yahrzeit that begins on Shabbat / Yom Tov: "light before candle lighting" (was: before sunset, which is already Shabbat); begins as Shabbat ends: "light after havdalah". Evening reminders say "Tonight".
- 30 Adar I in a plain year falls on 30 Shvat (first day of Rosh Chodesh Adar), not 1 Nisan.
- A calendar failing with any error (timeouts, CalDAV) no longer blanks the card; it is listed as unreadable.
- Card: refreshes arriving during a fetch are no longer dropped; all-day items use the display time zone (were off by hours when browser and server zones differ).
- Panel: date converter ignores stale answers. ICS: bare carriage returns escaped; feed cached per day.

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
