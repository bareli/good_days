# Good Days test plan (v0.5.0)

Stable IDs. Never renumber; add new ones at the end of a series.

## CFG - config and options flow
- CFG-001 Add integration from Settings; defaults from HA location / country; entry created.
- CFG-002 Jewish Calendar entry present: its location, diaspora, candle / havdalah minutes pre-fill once.
- CFG-003 Server-side validation errors (location, minutes, language) shown inline, nothing saved.
- CFG-004 Options: categories, lookahead, notify targets (only existing notify services), reminder time, quiet on Shabbat; merge keeps unknown keys; entry reloads.
- CFG-005 Hebrew and English strings present for every field, error and selector option.

## CAL - holiday engine and calendar
- CAL-001 Shabbat timed event candle lighting to havdalah, parasha title, special Shabbat names.
- CAL-002 Yom Tov + adjacent Shabbat = one event (e.g. Rosh Hashana 5787 Fri-Sun).
- CAL-003 Israel vs diaspora (Sukkot 1 vs 2 days).
- CAL-004 All-day spans (Chanukah 8 days, Chol HaMoed, Rosh Chodesh by month).
- CAL-005 Categories filter the calendar and sensors; next holiday / next Shabbat / next candle lighting sensors.
- CAL-006 DST change weeks (Israel end Oct, start Mar) times correct.
- CAL-007 Calendar panel month view far outside the cached window.

## FAM - family dates
- FAM-001 Add / edit / delete in the panel (Hebrew and Gregorian input, after-sunset converter).
- FAM-002 Adar rules, 30th-day rules, Adar I in plain year.
- FAM-003 Yahrzeit timed sunset to sunset; years count; titles he / en.
- FAM-004 Validation inline (client and server), limits (name 100, notes 500).
- FAM-005 Services add / update / remove / list_dates.

## REM - reminders
- REM-001 Due at reminder time N days before; once; mobile actions.
- REM-002 Due on Shabbat / Yom Tov -> sent before candle lighting.
- REM-003 Yahrzeit evening reminder; begins on Shabbat / after havdalah wording.
- REM-004 Ack stops, snooze repeats; restart does not duplicate or burst.

## TMR - Shabbat timers
- TMR-001 Create timer (editor, device picker = HA ha-selector in real HA), preview times correct.
- TMR-002 Presets create on + off; names in UI language.
- TMR-003 Fires once at the planned time; manual change not re-asserted; history row.
- TMR-004 Master switch, skip next, profile select (entities and panel agree).
- TMR-005 Conditions editor (HA ha-selector condition) saves and is evaluated.
- TMR-006 Conflicts reported; outside-period marks; Yom Kippur applies_to.
- TMR-007 Non-admin: reads timers, cannot change them (panel read-only, WS refuses).
- TMR-008 Restart: <=10 min late runs, older missed.

## ICS
- ICS-001 Off by default; enable / include holidays / new link / off (admin only).
- ICS-002 Feed validity (RFC 5545), Hebrew text, folding; imports into a calendar app.
- ICS-003 Token secrecy: wrong / old / other-entry tokens 404; no auth needed with the right one.

## CARD - Lovelace card
- CARD-001 Card resource auto-registered; card added from the picker; visual editor saves.
- CARD-002 Merges holidays, family dates and an external calendar; countdowns; Hebrew dates; RTL.
- CARD-003 Now banner during Shabbat; compact mode; details disclosure.
- CARD-004 Broken external calendar listed, card still renders.

## PANEL - sidebar panel
- PANEL-001 Sidebar entry, tabs, keyboard (arrows follow RTL), focus return after dialogs.
- PANEL-002 Multi-instance picker when two entries.

## WS / AST / BP
- WS-001 Every WS command validates input (types, ranges) and returns errors, not exceptions.
- AST-001 Intents speech en / he (pytest; conversation not available in the dev instance).
- BP-001 Blueprint imports; lights on N min before candle lighting even when an all-day event is on.

## Cross-cutting
- MOBILE-001 Panel and card usable at 320 px (no horizontal scroll, controls reachable).
- I18N-001 Hebrew RTL rendering, bidi of times / numbers, no mixed-direction garbling.
- A11Y-001 WCAG 2.1 AA: keyboard, focus visible, names / roles, dialogs, contrast, screen-reader text.
- SEC-001 Admin-only boundaries (ICS, timers writes) against a non-admin token.
- SEC-002 ICS route: token guessing, timing, path traversal, other entries, headers / caching.
- SEC-003 Stored input rendered safely (names, notes, rule names with markup) in card, panel, ICS, notifications.
- PERF-001 Engine compute time for lookahead 730 and 500 family dates; tick cost; storage growth (history, done).

## Regression cases from QA run 2026-09-30 (one per confirmed defect)
- SEC-004 Non-admin cannot change timers through switch / select entities (#6).
- SEC-005 Reminder notification actions ignore unknown date ids / days (#7).
- WS-002 Numeric fields reject NaN / Infinity with a field error (#8).
- TMR-009 Timer targets limited to what the rules allow; no silent "done" on unsupported domains (#9).
- CARD-005 Card keeps keyboard focus after activating an item and across the 60 s refresh (#10).
- TMR-010 Timer editor device picker labelled, hint / error associated, focused on error (#11).
- PERF-002 upcoming applies the limit before rendering (#12).
- PERF-003 dates/list cost at 500 dates (#13).
- PERF-004 Timer action persistence cost at 200 rules (#14).
- A11Y-002 Contrast of warning, primary and error colours, light and dark (#15, #16).
- TMR-011 Panel timer Save / Delete / Duplicate / Run now succeed (panel sends `language`) (#17).
- CFG-006 Options wording matches reminder hold behaviour (#18).
- MOBILE-002 Long names readable at 320 px / 200 % zoom (#19).
- I18N-002 Hebrew day headers in gematria (#31); mixed Hebrew names in English titles keep order (#32).
- CARD-006 Card merges (or reports) a second Good Days entry's calendar (#33).


## HAF: haftarah (v0.7)

- HAF-01 Next Shabbat shows its haftarah in the card details, the calendar event description, the ICS feed and `sensor.good_days_next_shabbat` attribute `haftarah`; Hebrew citation in Hebrew UI, English in English.
- HAF-02 Options: "Haftarah custom" Ashkenazi / Sephardi; switching changes every surface (sensor, WS, calendar, ICS) without restart.
- HAF-03 Special cases visible in the next weeks / months of the calendar: Machar Chodesh, Rosh Chodesh, special Shabbatot (Shekalim, Zachor, Parah, HaChodesh, HaGadol), Shabbat Chanukah, Shuva; a Shabbat next to Yom Tov keeps its parasha (title of the combined period unchanged).
- HAF-04 Shabbat Chol HaMoed / Shabbat that is Yom Tov: no haftarah and no broken text.
- HAF-05 Hebrew rendering: book names, letters without geresh, en dash, bidi correct inside RTL descriptions with mixed English.
- HAF-06 Regression: titles, specials, Mevarchim / Machar Chodesh notes, candle lighting / havdalah times unchanged for plain Shabbatot.

## TIM-P: timer presets (v0.7)

- TIM-P-01 Presets "Electric water heater", "Porch light", "Bedroom AC at night" listed in he / en; creating each makes an on and an off rule with the expected anchors / times; the preview shows them for the next Shabbat and a Chag.
