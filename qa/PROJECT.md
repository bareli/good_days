# QA project profile: Good Days

The global QA kit (`~/.claude/qa-kit/`) holds process only. Everything that is true of THIS product
lives here and in `qa/CLAUDE.md` (environments, instances, traps) and `qa/knowledge/` (what QA learned).

Fill only what the code or the owner proves. A `TODO(ask owner)` is honest; a guess is a defect.

## Product

- Name: Good Days / ימים טובים (code: `custom_components/good_days`, domain `good_days`)
- What it does: Home Assistant custom integration (HACS) + Lovelace card + sidebar panel. Computes Shabbat,
  Jewish holidays, fasts and special Shabbatot offline (hdate), candle lighting / havdalah; Hebrew-date family
  dates (birthdays, yahrzeits, anniversaries) with reminders (notify + mobile actions); Shabbat timers that switch
  devices around candle lighting / havdalah; Assist intents; ICS subscription; blueprint.
- Owner (rules on UX/ENH decisions): Bar Eli ("Victor"), GitHub `bareli`
- Production: there is no hosted product. "Production" = each user's own Home Assistant after installing a
  release from HACS / GitHub. QA never touches anyone's real Home Assistant.
- Deploy: GitHub release tag `vX.Y.Z` on `bareli/good_days` (`main`, mirrored to `master`); users update via HACS.

## Users

Israeli households and religious Jewish families abroad running Home Assistant. Mixed expertise: the installer is
usually the household's tech person (admin); everyday users (family members, non-admin HA users) read the card on
a wall tablet or phone and manage family dates in the panel. TODO(ask owner): share of phone vs tablet vs desktop.

## Locale

Hebrew first (RTL), English second (LTR). UI language follows the HA user's language; entity text follows the
integration option `auto|he|en`. Hebrew dates in gematria (ט״ו תשרי תשפ״ז). Times 24 h, local HA time zone
(Asia/Jerusalem for Israel; diaspora users elsewhere). Realistic content: Hebrew names (נועה, סבא משה), parashot,
holidays; long Hebrew titles ("שמיני עצרת · שמחת תורה · שבת").

## Stack

Python custom integration on Home Assistant core (min 2025.7, CI on latest), `hdate[astral]` for the calendar,
HA `Store` JSON storage per config entry, websocket API, services, calendar/sensor/binary_sensor/switch/select
platforms, HA event helpers for timers. Front end: vanilla web components (`www/card.js`, `www/panel.js`, no build
step), HA frontend elements when present (`ha-card`, `ha-icon`, `ha-form`, `ha-selector`, `ha-menu-button`).

## Paths

- Application code (read-only for everyone except qa-developer): `custom_components/good_days/**`,
  `blueprints/**`, `scripts/gen_strings.py`
- Test project (finders may add a failing regression test only): `tests/`
- Build / test commands: no build. Tests: `pytest` (CI: `.github/workflows/validate.yml`, Python 3.14, latest
  pytest-homeassistant-custom-component); local Windows recipe in `qa/CLAUDE.md` §3.

## Roles

engineer, ux, accessibility, security, performance, developer: all apply. Performance is limited to the engine's
compute cost, the 1-minute tick, storage growth and websocket payloads (no database server).

## Always in scope

- Admin-only boundaries: `good_days/ics/*` and every `good_days/timers/*` write require admin; reads do not.
- The unauthenticated ICS route (`/api/good_days/ics/{entry_id}/{token}.ics`).
- Anything touching time zones / DST, Hebrew-date recurrence, or Shabbat / Yom Tov boundaries (timers and
  reminders act on them).

## Business outcomes

- Holidays: `calendar.good_days_holidays` events (timed candle lighting → havdalah for Shabbat / Yom Tov).
- Family dates: record in `.storage/good_days.<entry_id>`; occurrence in `calendar.good_days_family`.
- Reminders: `notify.<target>` call and `good_days_reminder` event, once per occurrence.
- Timers: a `homeassistant.turn_on/off` service call at the planned time, one history row, `done` key stored.
- ICS: 200 `text/calendar` only with the current token.

## Security shape

- Isolation: single household per HA; boundary is admin vs non-admin HA users (see *Always in scope*). Family-date
  services and `good_days/dates/*` WS are open to every authenticated user by design (household data).
- Public route: ICS feed, protected by a 256-bit token in `.storage/good_days.<entry_id>` (`ics.token`), off by
  default, compared with `hmac.compare_digest`, 404 for every failure.
- Personal data: family names, Hebrew birth / death dates, notes. Exposed through the ICS feed when enabled.
- Validation: server-side validators for config / options flow, family dates (`storage.validate_date`), timer
  rules (`timers.validate_rule` + HA condition validation). No CSRF surface beyond HA's own.
- Third-party credentials: none.

## Deliberate behaviour

- Times use sea-level sunset (elevation ignored) to match printed calendars (CHANGELOG v0.3).
- Reminders due on Shabbat / Yom Tov are sent an hour before candle lighting (v0.4).
- Timers fire once and never re-assert a manual change; actions up to 10 minutes late still run (SPEC §12.4).
- Adar / 30th-day rules are provisional customs, configurable per date (SPEC §11.5).
- Shushan Purim is shown everywhere (as hdate does).

## Accessibility

WCAG 2.1 AA. Israeli standard IS 5568 applies to Israeli public-facing services; this is a home-automation add-on.
TODO(ask owner): whether IS 5568 conformance is a goal.

## Scale target

One household: up to 500 family dates (hard cap), 200 timer rules (cap), 10 profiles, 1-3 config entries,
lookahead up to 730 days.

## Fix constraints

- Translations are generated: edit `scripts/gen_strings.py`, run it, never hand-edit `strings.json` /
  `translations/*.json`.
- Bidi isolates as escapes in source (`⁨..⁩`), never literal characters (tests/test_conventions.py).
- No `console.*`, no `innerHTML` with dynamic text in `www/*.js`.
- Options flow merges into existing options; never name an entity property `options` except SelectEntity's own.
- Server-side validation for every input path; inline client-side messages mirror it.
- Every change: tests pass on Python 3.13 / HA 2026.2 and Python 3.14 / latest HA (CI).
- Replies to the owner: see root `CLAUDE.md` (caveman mode, no em-dashes, confidence %).

## Test ID series

`CAL` (holiday engine / calendar), `FAM` (family dates), `REM` (reminders), `TMR` (Shabbat timers), `ICS`,
`CARD`, `PANEL`, `CFG` (config / options flow), `WS`, `AST` (Assist), `BP` (blueprint), `SEC`, `PERF`, `A11Y`,
`MOBILE`, `I18N`.

## Leak terms

- good_days
- Good Days
- ימים טובים
- dud_shemesh
- hdate
- candle_lighting_light
- GOODDAYS
