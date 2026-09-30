# Historical risk areas

From QA run 2026-09-30 (v0.5.0). Map changed files to these when scoping a risk-based run.

| Area | Files | Why it is risky | Issues |
|---|---|---|---|
| Panel <-> WS contract | `www/panel.js`, `websocket_timers.py`, `websocket.py` | The panel adds fields (e.g. `language`) that strict voluptuous schemas reject; unit tests call WS without them and the fake-hass harness accepts anything. Test every panel action against a real HA. | #17 |
| Admin boundary | `switch.py`, `select.py`, `websocket_timers.py`, `ics.py` | WS commands are admin-gated but entities that do the same thing are not. Any new entity touching timers/ICS needs an admin check. | #6 |
| Focus / re-render | `www/card.js`, `www/panel.js` | Full re-renders every 60 s; focus restore depends on HA custom elements having rendered. Fake-hass tests passed, real HA failed. | #10 |
| Bidi and Hebrew formatting | `engine.py`, `family.py`, `www/*.js` | Mixed-direction titles, gematria in browsers (`nu-hebr` unsupported in Chromium), literal isolate characters. | #31, #32 |
| Copy vs behaviour drift | `scripts/gen_strings.py`, README | Behaviour changed in v0.4 (reminder hold), options text did not. | #18 |
| Multi-instance | `www/card.js`, panel picker | Second config entry is rarely exercised. | #33, #34 |
