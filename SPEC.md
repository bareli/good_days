# Good Days (ימים טובים) — Product & Technical Spec

Status: draft v1, 2026-09-30. Owner: Bar Eli (Victor), bareli@gmail.com.
Sister projects: `dud_shemesh` (v0.6.1), `schedule_wizard`. Reuse their patterns (see §10).

---

## 1. One-liner

A Home Assistant integration + Lovelace card that shows **what's coming up**: Shabbat, Jewish holidays and fasts, **family events from any HA calendar**, and **Hebrew-date birthdays and yahrzeits**, each with a live countdown, in Hebrew or English.

## 2. Why (the gap)

- HA core's **Jewish Calendar** integration only exposes sensors / binary sensors (today's holiday, the upcoming candle lighting / havdalah, `issur_melacha_in_effect`). Its platforms are `BINARY_SENSOR` and `SENSOR` only: **no calendar entity, no list of future holidays.** Verified in HA 2026.2 source.
- Generic agenda cards exist (HA built-in calendar card, Atomic Calendar Revive in HACS), but none are Jewish-calendar aware, Hebrew/RTL-first, or countdown-style.
- **No calendar product handles recurrence by Hebrew date** (birthdays by Hebrew date, yahrzeits). Google Calendar cannot. *(Speculative: re-check HACS before building.)*

Target users: Israeli households and religious Jewish families abroad (US, UK), Hebrew and English.

## 3. Goals / non-goals

Goals
1. Answer at a glance: "When is the next Shabbat / holiday, how long until it, when do we light candles?"
2. One family view that merges holidays + everyone's calendars, with countdowns.
3. Hebrew-date recurring personal dates with reminders.
4. Works offline (no external API needed for holidays).
5. Automation-friendly: calendar entities and sensors usable in HA automations.

Non-goals (v0.x)
- Replacing Google Calendar / editing Gregorian events (read-only for external calendars).
- Full zmanim dashboard (Jewish Calendar already covers zmanim sensors).
- Shabbat device timers (that is the later "Shabbat Home" product; this project's calendar engine should be reusable by it).

## 4. User stories

- As a parent, I see on the kitchen tablet: "Shabbat in 2 days, candle lighting Fri 17:52", "Hanukkah in 12 days", "Noa's birthday (Hebrew) in 5 days", "Dentist tomorrow 16:00".
- While it's Shabbat/Yom Tov, the card shows "Now: Shabbat, ends 18:49".
- I add Grandpa's yahrzeit once (Hebrew date), and every year I get a reminder the day before: "Yahrzeit tomorrow, light a candle tonight".
- I see a warning when a calendar event falls on Shabbat or Yom Tov.
- An automation turns on the porch light 10 min before candle lighting using the calendar entity trigger.
- I ask Assist "מה יש השבוע?" and hear the next items (v0.3).

## 5. Architecture

```
Good Days integration (custom_components/good_days)
 ├─ calendar.good_days_holidays    Shabbatot, holidays, fasts, Rosh Chodesh (configurable),
 │                                  with candle lighting / havdalah in the event data
 ├─ calendar.good_days_family      Hebrew-date recurring personal dates (v0.2)
 ├─ sensor.good_days_next_holiday  name; attrs: start, days_until, type, candle_lighting
 ├─ sensor.good_days_next_shabbat  candle lighting (timestamp); attrs: havdalah, parasha, days_until
 ├─ sensor.good_days_next_family   next personal date (v0.2)
 ├─ binary_sensor.good_days_today_is_holiday   (optional, cheap)
 └─ WS: good_days/upcoming         merged, pre-computed list for the card (see §7.3)

good-days-card (www/card.js, auto-registered Lovelace resource)
 merges: good_days calendars + any user-selected calendar.* entities
```

### 5.1 Holiday engine
- Library: **`hdate[astral]`**, the same package HA core's Jewish Calendar uses (core pins `hdate[astral]==1.1.2` in HA 2026.2). Declare a compatible requirement in `manifest.json` (do **not** pin a version that conflicts with core; use a range or match core).
- API used by core (verify signatures against the installed version before coding):
  - `from hdate import HDateInfo, Location, Zmanim`
  - `HDateInfo(date, diaspora=...)` → `.holidays` (list; each has `.name`, `.type` (HolidayTypes enum)), `.upcoming_shabbat`, `.upcoming_shabbat_or_yom_tov` (`.first_day`, `.last_day`, `.previous_day`, `.gdate`), `.hdate`, `.upcoming_shabbat.parasha`
  - `Zmanim(date=..., location=Location(...), candle_lighting_offset=..., havdalah_offset=...)` → `.candle_lighting`, `.havdalah`
- **Settings source**: if the Jewish Calendar integration is configured, read its location / `diaspora` / `candle_lighting_minutes_before_sunset` / `havdalah_minutes_after_sunset` (from its config entry data/options) so the user configures once. Otherwise fall back to HA's home location and our own options (Israel default: diaspora false, candle 18 min before sunset in most cities, Jerusalem 40; havdalah 0 → use tzeit).
- Pre-compute events for a rolling window (default 400 days) on startup and daily at 00:05; recompute on options change. Cache in memory; no storage needed for holidays.
- Multi-day holidays become one calendar event spanning the days (e.g. Pesach first days), with `candle_lighting` of the eve and `havdalah` of the last day in the description / extra data.
- Holiday categories (filterable): `shabbat`, `yom_tov`, `chol_hamoed`, `minor` (Hanukkah, Purim, Tu BiShvat, Lag BaOmer...), `fast`, `rosh_chodesh`, `modern` (Yom HaAtzmaut, Yom HaZikaron...), `memorial`. Map from hdate `HolidayTypes` (check actual enum values).

### 5.2 Calendar entities
- Implement `CalendarEntity` with `async_get_events(hass, start, end)` and `event` (current/next).
- Holiday events: all-day for day-level holidays; **timed** for Shabbat/Yom Tov (candle lighting → havdalah) so HA calendar triggers ("start" offset -10 min) work for automations.
- Event `uid` stable per (type, gregorian start date) so automations/cards can de-duplicate.
- Localized summaries (Hebrew/English per HA language), `description` includes candle lighting / havdalah times and parasha for Shabbat.

### 5.3 Family (Hebrew-date) dates — v0.2
- Stored with HA `Store` per config entry: `{id, name, kind: birthday|yahrzeit|anniversary|custom, hebrew_day, hebrew_month, original_year?, adar_rule, reminder_days: [1], notes}`.
- Recurrence rules:
  - Adar in non-leap/leap years: configurable `adar_rule` (`adar_i`, `adar_ii`, `both`); defaults: birthdays → Adar II in leap years; yahrzeits → follow common custom (default Adar II, configurable). *(Halachic customs differ; make it a setting, don't hard-code.)*
  - 30 Cheshvan / 30 Kislev in years where the month has 29 days → configurable fallback (1 of next month vs 29). Default: common custom, configurable.
  - Yahrzeit shown the evening before (starts at sunset) as a timed event; birthdays all-day.
- Management UI: small editor in the card's config dialog **or** a sidebar panel page (decide in v0.2; panel preferred for a family list). Services: `good_days.add_date`, `update_date`, `remove_date`, `list_dates` (response).
- Optional: Gregorian → Hebrew converter in the editor ("born 12 Mar 1985 after sunset" → Hebrew date).

### 5.4 Reminders — v0.3
- Per date `reminder_days` + time (default 09:00 and, for yahrzeit, before sunset the evening before).
- Notify via selected `notify.*` services; mobile_app actionable buttons (dismiss / remind tomorrow) — reuse Dud Shemesh `_notify` pattern.
- Texts in Hebrew/English by HA language.

## 6. The card (`custom:good-days-card`)

### 6.1 Data
- Preferred: WS `good_days/upcoming` with `{calendars: [...entity_ids], days: 30, limit: 10, categories: [...]}` → server merges good_days events + external calendars via `calendar.get_events` (service with response), sorts, adds `hebrew_date`, `countdown`, `conflicts_shabbat` flags. Single round-trip, no CORS/permission issues, consistent timezone.
- Fallback (if integration not installed): read any calendars via REST `GET /api/calendars/<entity_id>?start=&end=` (`hass.callApi`). Holidays then unavailable; show a hint.

### 6.2 Layout
- Header: title (configurable) + optional "Now" banner when Shabbat/Yom Tov is in effect ("שבת שלום · יוצאת ב-18:49").
- Items grouped by day: "היום / מחר / יום ה׳ 3.10" (Hebrew date small underneath: "א׳ תשרי").
- Each item: color dot per source calendar, title, time (or "כל היום"), countdown chip ("בעוד 3 ימים", "בעוד 2 ש׳", "עכשיו"), badges: 🕯 candle lighting time for Shabbat/Yom Tov, ⚠ "falls on Shabbat" for external events overlapping Shabbat/Yom Tov (v0.2), category icon for holidays.
- Compact variant (single line "Next: Shabbat in 2d · 17:52") for small dashboards.
- Tap item → details dialog (description, location, calendar).
- Countdown refresh: 60 s tick client-side; data refresh every 5 min or on `calendar` state change.

### 6.3 Config (visual editor required, `getConfigElement` + `getStubConfig`)
```yaml
type: custom:good-days-card
title: What's coming
calendars:              # external calendars to merge
  - calendar.family
  - calendar.school
colors: { calendar.family: "#4caf50" }
days: 30                # look-ahead
limit: 10
categories: [shabbat, yom_tov, minor, fast, family]   # holiday filters
show_hebrew_date: true
show_candle_lighting: true
compact: false
entry_id: <optional, multi-instance>
```

### 6.4 i18n / RTL / a11y (hard requirements, lessons from dud_shemesh)
- Full English + Hebrew UI; `dir="rtl"` and `lang` on the card root for Hebrew.
- Bidi: wrap mixed number/unit fragments with Unicode isolates using **escape sequences** in source (`⁦…⁩`, `⁨…⁩`), never literal invisible chars. Avoid "+" prefixes on Hebrew labels.
- Timeline/time axes stay LTR.
- Keyboard: every control is a real `button`; focus retained across re-renders (data-focus-key pattern); visible focus rings; `prefers-reduced-motion`.
- No `console.*` in committed code; no `innerHTML` with dynamic text.

## 7. Backend details

### 7.1 Config flow
- Step user: use Jewish Calendar settings (auto-detected) **or** own: location (defaults to HA home), diaspora (bool), candle lighting minutes, havdalah minutes / tzeit, language for event names (auto from HA).
- Options: holiday categories to include, include Rosh Chodesh, include modern Israeli days, look-ahead days.
- Validate everything server-side (`errors` on the form), per global form-validation rule.

### 7.2 Multi-instance
- Allowed (e.g. two locations). Per-entry storage key `good_days.<entry_id>`. Services/WS take optional `entry_id`, default first entry in config order (dud_shemesh `_resolve_entry` pattern).

### 7.3 WS `good_days/upcoming` response item
```json
{
  "uid": "yom_tov-2026-10-02",
  "source": "holidays | family | calendar.family",
  "title": "סוכות",
  "start": "2026-10-02T17:52:00+03:00",
  "end": "2026-10-03T18:49:00+03:00",
  "all_day": false,
  "category": "yom_tov",
  "hebrew_date": "ט״ו תשרי תשפ״ז",
  "candle_lighting": "2026-10-02T17:52:00+03:00",
  "havdalah": "2026-10-03T18:49:00+03:00",
  "in_effect": false,
  "conflicts_shabbat": false
}
```
(Example values illustrative; compute real dates with hdate.)

### 7.4 Permissions
- Reading upcoming events: any user. Adding/removing family dates: any user (household data) unless it proves sensitive; options/config: admin (HA default).

## 8. Milestones

| Version | Scope |
|---|---|
| **v0.1** | Holidays calendar entity (+ Shabbat timed events with candle/havdalah), sensors (next holiday, next Shabbat), WS `upcoming`, card merging holidays + external calendars, countdowns, Hebrew/English, RTL, visual editor, tests, HACS + hassfest CI. |
| v0.2 | Family Hebrew-date dates (storage, services, editor/panel), `calendar.good_days_family`, Shabbat-conflict badges for external events, compact card variant. |
| v0.3 | Reminders (notify + actionable buttons), Assist intent ("מה יש השבוע?" / "When is the next holiday?") with ready-made en/he sentences, blueprint "porch light before candle lighting". |
| later | Feed "Shabbat Home" timers product; Hebcal-style Torah reading/parasha details; ICS export of family dates. |

## 9. Testing (required before every commit)

- `pytest-homeassistant-custom-component`; tests in `tests/`, CI job runs them (copy dud_shemesh `.github/workflows/validate.yml`, incl. frontend requirement install for panel_custom/lovelace deps).
- Golden tests for dates (run with a fixed clock via `freezer`):
  - Rosh Hashana, Yom Kippur, Sukkot (Israel 1 day Yom Tov vs diaspora 2 days), Pesach, Shavuot, Hanukkah, Purim (and Shushan Purim for Jerusalem if location-based: decide), fasts that move when falling on Shabbat (e.g. Tisha B'Av nidche).
  - Candle lighting/havdalah for Shabbat in Jerusalem vs Tel Aviv offsets.
  - Leap-year Adar rules and 30 Cheshvan/Kislev fallback for family dates (v0.2).
  - Calendar entity `async_get_events` window boundaries, multi-day spans, uid stability.
  - WS `upcoming` merge ordering, limit, categories, external calendar via mocked `calendar.get_events`.
- Card: node `--check` + a Playwright harness with fake `hass` (same approach as dud_shemesh scratch harness) for en/he, desktop/mobile screenshots.
- Windows dev note: HA doesn't import on native Windows (`fcntl`, `resource`); use CI/Linux, or local stubs + socket unblock + `home-assistant-frontend` in a throwaway venv (see dud_shemesh CLAUDE.md "Tests").

## 10. Conventions to carry over from dud_shemesh

- Repo layout: `custom_components/good_days/` (`__init__.py`, `manifest.json`, `const.py`, `config_flow.py`, `calendar.py`, `sensor.py`, `entity.py` base, `storage.py`, `services.yaml`, `strings.json`, `translations/{en,he}.json`, `www/card.js`, `brand/`), `tests/`, `docs/`, `hacs.json`, `info.md`, `README.md`, `CHANGELOG.md`, `CLAUDE.md`, `.github/workflows/validate.yml`, `requirements_test.txt`, `pytest.ini`.
- Card auto-registered as a Lovelace `module` resource with `?v=<version>` cache-busting; delete stale URLs on setup.
- Entity base class: **never** name a property `options` on an entity (shadows `SensorEntity.options` / `SelectEntity.options`); use `cfg`.
- Translations for config flow + entity names generated from one table (en/he) so `strings.json`, `en.json`, `he.json` never drift.
- Options flow must **merge** into existing options, never replace.
- Never `open()` synchronously in the event loop; cache manifest version.
- Always populate state before creating tasks that read it (eager tasks since HA 2024.x).
- Git: small fixes on `main` → patch tag; features on a feature branch → merge → minor tag; run tests first; push `main` + tag, force-push `main:master`; GitHub Release via `gh`. Always ask "anything else for this version?" before tag + release.
- Replies to Victor: caveman mode, Hebrew or English matching his message, no em-dashes, metric, confidence % at the end.

## 11. Open questions (resolve at project start)

1. `hdate` license: confirm (I don't know it). Runtime dependency like HA core does is the common pattern either way.
2. HACS check: search for an existing Jewish holiday calendar / countdown card and Hebrew-date recurrence integration before building (web search on 2026-09-30 found none, but re-check).
3. Reuse Jewish Calendar config vs own config: read its config entry directly (internal data, may change) or just copy its defaults into our flow? Prefer: offer "import from Jewish Calendar" once, store our own copy.
4. Family dates editor location: card dialog vs sidebar panel.
5. Adar / 30-Cheshvan defaults: confirm the customs to default to (user-configurable either way).
6. Name/branding: "Good Days" / "ימים טובים" (repo `good_days`), icon needed.
