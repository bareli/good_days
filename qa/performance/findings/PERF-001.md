# PERF-001 ws good_days/upcoming renders every event in the window before applying limit: 27.5 ms on the event loop at days=400 with 500 family dates

| | |
|---|---|
| Type | PERFORMANCE RISK |
| Severity | LOW |
| Status | OPEN |
| Issue | [#12](https://github.com/bareli/good_days/issues/12) |
| Feature | Card / `good_days/upcoming` |
| Test case | PERF-001 |
| Environment | dev |
| Branch / commit | main @ 1eea680 |
| Detected by | qa-performance-engineer |
| Detected | 2026-09-30 |
| Model | sonnet |
| Evidence basis | MEASURED (harness script, not a live instance) |

## Summary

`ws_upcoming` runs on the event loop. It calls `runtime.render()` for every holiday and family event in the window, sorts, and only then cuts to `limit` (max 100). `render` calls `periods_overlapping`, a linear scan of all cached holiday events, for every family item, and the handler scans periods a second time per family item.

## Measurement

Venv314 Python 3.14 on the dev machine (Windows, other QA agents running HA instances at the same time), warm, median of 5 runs. Data: 500 family dates (167 yahrzeit), Israel, cached window 737 days (189 holiday events, 999 family events). Script replicated the handler body (minus the WS layer).

| days | limit | items rendered | loop time | payload |
|---|---|---|---|---|
| 30 (card default) | 100 | 56 | 1.4 ms | 28.7 KB |
| 400 (card editor maximum) | 100 | 603 | 27.5 ms (26.5..29.7) | 51.3 KB (100 items) |

The threshold used for "blocks the loop" is 10 ms synchronous. Fetch happens every 5 min per open card plus on every `calendar.good_days*` `last_updated` change. The split between `render` and the periods scans was not profiled.

## Scale implication

Cost grows with (events in window) x (holiday events in cache, up to 730 days). Default card config is fine. A card set to days=400 on a household at the 500-date cap blocks the loop about 28 ms per fetch per open dashboard. Low because it is bounded and periodic.

## Likely root cause

Render before truncate, and O(events) `periods_overlapping` per item (`runtime.py` `render`, `websocket.py` `ws_upcoming`).

## Recommended remediation

Merge and sort the raw events by start first, slice to `limit`, then render only those. Compute `conflicts_shabbat` with a bisect over the sorted period list (or once per handler). Keep the external-calendar merge order unchanged (external items still need sorting with the local ones before the cut).

## Suggested regression

Test with 500 dates, days=400, limit=10: assert `render` is called at most `limit` (plus external) times.

## Relevant files

`custom_components/good_days/websocket.py` (`ws_upcoming`), `custom_components/good_days/runtime.py` (`render`, `periods_overlapping`), `custom_components/good_days/www/card.js` (days max 400).
