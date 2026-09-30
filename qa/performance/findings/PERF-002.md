# PERF-002 good_days/dates/list recomputes next_occurrence per record: 265 ms executor, 412 KB payload at 500 dates, and the panel rebuilds all 500 rows on every load

| | |
|---|---|
| Type | SCALABILITY RISK |
| Severity | LOW |
| Status | CLOSED, verified 2026-10-01 (merged from fix/qa-2026-09-30) |
| Issue | [#13](https://github.com/bareli/good_days/issues/13) |
| Feature | Panel dates tab / `good_days/dates/list` |
| Test case | PERF-001 |
| Environment | dev |
| Branch / commit | main @ 1eea680 |
| Detected by | qa-performance-engineer |
| Detected | 2026-09-30 |
| Model | sonnet |
| Evidence basis | MEASURED server side; panel DOM cost ANALYTICAL (no browser run) |

## Summary

`ws_dates_list` calls `family.next_occurrence` for each record, each a full `compute_family` over about 420 days (3 Hebrew years), although the runtime already holds the next occurrence of every date in `runtime.family_events` (730 days). The panel then renders every row with no pagination and rebuilds the whole shadow root on every `_load` (panel open, every 10 min, after every save or delete) and on every dialog close.

## Measurement

Venv314, Windows dev machine (shared, loaded), warm, 500 family dates (167 yahrzeit), Israel, median of 3 runs of the handler body:

- `ws_dates_list` body for 500 records: 265 ms (263..273), payload 412,279 bytes.
- single `next_occurrence`: 0.06-0.08 ms birthday, 0.37-0.76 ms yahrzeit (sunset computed twice per occurrence).
- each save or delete also runs `async_refresh_family` (`compute_family` 500 dates, 730 days: 291 ms median, 285..295; about 390 ms for a New York profile), so one edit is about 0.55 s of pure-Python CPU plus one 412 KB reload.

Panel DOM: `_renderRow` creates about 12 elements, 1 `ha-icon` and 2 listeners per row; 500 rows is about 6,000 nodes and 1,000 listeners rebuilt by `root.textContent = ""` plus full re-append. Evidence unavailable for the rebuild time: no browser measurement was made (depth: source and test only).

## Scale implication

At the 500-date cap: 265 ms of executor CPU that contends for the GIL with the event loop (pure Python, so the loop gets 5 ms slices; loop latency impact not measured) and a 412 KB websocket message on each panel open and each edit. A scripted bulk import of 500 dates through the add service or WS costs 500 x about 0.3 s of refresh CPU, growing with N, with no debounce.

## Likely root cause

Per-record recomputation instead of reading the cached family events; no pagination or incremental DOM update in the panel.

## Recommended remediation

Build `next` from `runtime.family_events` (first event with `end > now` per `date_id`), falling back to `next_occurrence` only for records with nothing in the window. Panel: render rows in pages, or update the affected row instead of a full rebuild after save. Optional: skip the sunset calls for yahrzeit occurrences outside the requested window in `compute_family` (167 yahrzeit records alone took 291-350 ms; the other 333 records took 24-40 ms).

## Suggested regression

Test that `ws_dates_list` does not call `compute_family` per record (count calls with 50 records).

## Relevant files

`custom_components/good_days/websocket.py` (`ws_dates_list`, `_date_view`), `custom_components/good_days/family.py` (`next_occurrence`, `compute_family`), `custom_components/good_days/www/panel.js` (`_load`, `_render`, `_renderRow`).
