# PERF-003 Each fired timer action rewrites the full timers store (about 160 KB at 200 rules) and fans out a state update; simultaneous rules multiply it

| | |
|---|---|
| Type | PERFORMANCE RISK |
| Severity | LOW |
| Status | OPEN |
| Issue | [#14](https://github.com/bareli/good_days/issues/14) |
| Feature | Shabbat timers (`timer_manager.py`) |
| Test case | PERF-001 |
| Environment | dev |
| Branch / commit | main @ 1eea680 |
| Detected by | qa-performance-engineer |
| Detected | 2026-09-30 |
| Model | sonnet |
| Evidence basis | ANALYTICAL for the write count (source); size and serialisation time MEASURED |

## Summary

`_async_run` ends with `await self.store.async_save()` and `async_dispatcher_send(self.signal)` for every single action, and `TimerStore.async_save` writes rules, done keys and history in full via `Store.async_save` (immediate, not `async_delay_save`). Rules that share an anchor and offset fire in the same second.

## Measurement

Synthetic store: 200 rules, `done` for 2 periods (400 keys), 100 history rows, Python 3.14. JSON size 159,813 bytes (indent 2, HA's on-disk format) or 124,777 compact; `json.dumps` 0.37 ms median of 20. Not measured: disk time and the number of concurrent saves on a live instance (no running instance; a real firing needs a Shabbat). The write count at identical fire time is taken from the code path, not observed.

## Scale implication

With 200 rules anchored to the same candle-lighting offset, one firing minute causes 200 saves of about 160 KB (about 32 MB) and 200 dispatcher fan-outs to every entity. On an SD-card Home Assistant host (common) that is avoidable write wear and a burst of executor work at the most time-sensitive moment. Households with 5-20 rules are unaffected.

## Likely root cause

Persist-per-action instead of batching.

## Recommended remediation

Use `Store.async_delay_save` (for example 1-2 s) on the `_record` path, or coalesce saves per firing batch. The `done` dedupe key must survive a restart, so the delay has to stay well inside the 10-minute grace window; decide that explicitly. Coalesce the dispatcher signal per batch.

## Suggested regression

Unit test: fire 50 planned actions at the same time and assert the store write count is well below 50.

## Relevant files

`custom_components/good_days/timer_manager.py` (`_async_run`, `_record`, `async_replan`), `custom_components/good_days/storage.py` (`TimerStore.async_save`).
