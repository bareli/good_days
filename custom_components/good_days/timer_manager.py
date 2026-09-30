"""Runs Shabbat Home timers: schedules the planned actions, fires each once, keeps history."""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import condition
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .storage import TimerStore
from .timers import PlannedAction, conflicts, expand

if TYPE_CHECKING:
    from .runtime import GoodDaysRuntime

LOG = logging.getLogger(__name__)
GRACE = dt.timedelta(minutes=10)  # missed while Home Assistant was down: still run
PLAN_PERIODS = 2
SERVICE_TIMEOUT = 30
SIGNAL_TIMERS = f"{DOMAIN}_timers_{{}}"

STATUS_DONE = "done"
STATUS_LATE = "late"  # run after a restart, within the grace window
STATUS_SKIPPED = "skipped"  # master off, skipped period, or conditions false
STATUS_MISSED = "missed"  # Home Assistant was down for longer than the grace window
STATUS_FAILED = "failed"


class TimerManager:
    def __init__(self, runtime: GoodDaysRuntime) -> None:
        self.runtime = runtime
        self.hass: HomeAssistant = runtime.hass
        self.store = TimerStore(runtime.hass, runtime.entry.entry_id)
        self._unsubs: list[Callable[[], None]] = []
        self._signature: tuple = ()
        self._lock = asyncio.Lock()
        self.planned: list[PlannedAction] = []

    @property
    def signal(self) -> str:
        return SIGNAL_TIMERS.format(self.runtime.entry.entry_id)

    async def async_start(self) -> None:
        await self.store.async_load()
        await self.async_replan(startup=True)

    @callback
    def async_stop(self) -> None:
        self._cancel()

    def _cancel(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()

    # Planning -----------------------------------------------------------------

    def periods(self, now: dt.datetime, count: int = PLAN_PERIODS) -> list:
        found = [e for e in self.runtime.events if e.period and not e.all_day and e.end > now]
        return found[:count]

    def plan(self, now: dt.datetime, profile: str | None = None, count: int = PLAN_PERIODS) -> list[PlannedAction]:
        return expand(
            self.store.rules,
            self.periods(now, count),
            self.runtime.settings.time_zone,
            profile or self.store.active_profile,
        )

    async def async_replan(self, startup: bool = False) -> None:
        """Recompute and reschedule when rules, settings or the upcoming periods changed."""
        async with self._lock:
            now = dt_util.now()
            planned = self.plan(now)
            signature = (
                tuple(p.key for p in planned),
                self.store.enabled,
                tuple(self.store.skip),
            )
            if signature == self._signature and not startup:
                return
            self._signature = signature
            self.planned = planned
            self._cancel()
            late = []
            for action in planned:
                if action.key in self.store.done:
                    continue
                if action.when > now:
                    self._unsubs.append(
                        async_track_point_in_time(self.hass, partial(self._async_due, action), action.when)
                    )
                elif now - action.when <= GRACE:
                    late.append(action)
                elif startup:
                    self._record(action, STATUS_MISSED, "Home Assistant was not running")
            self._prune(now)
            await self.store.async_save()
        for action in late:
            await self._async_run(action, late=True)
        async_dispatcher_send(self.hass, self.signal)

    def _prune(self, now: dt.datetime) -> None:
        live = {p.uid for p in self.periods(now, 10)}
        self.store.skip = [uid for uid in self.store.skip if uid in live]
        cutoff = (now - dt.timedelta(days=14)).isoformat()
        self.store.done = {k: v for k, v in self.store.done.items() if v >= cutoff}

    # Running ------------------------------------------------------------------

    async def _async_due(self, action: PlannedAction, _now: dt.datetime) -> None:
        await self._async_run(action)

    async def _async_run(self, action: PlannedAction, late: bool = False) -> None:
        if action.key in self.store.done:
            return
        rule = self.store.get(action.rule_id)
        reason = None
        if not self.store.enabled:
            reason = "Shabbat timers are off"
        elif action.period_uid in self.store.skip:
            reason = "This Shabbat / Chag is skipped"
        elif rule is None or not rule.get("enabled", True) or rule.get("profile") != self.store.active_profile:
            reason = "Rule changed"
        elif rule.get("conditions") and not await self._async_conditions_pass(rule):
            reason = "Conditions not met"
        if reason:
            self._record(action, STATUS_SKIPPED, reason)
        else:
            try:
                await self.async_execute(action.action, list(action.targets))
                self._record(action, STATUS_LATE if late else STATUS_DONE)
            except (HomeAssistantError, TimeoutError) as err:
                self._record(action, STATUS_FAILED, str(err) or type(err).__name__)
        await self.store.async_save()
        async_dispatcher_send(self.hass, self.signal)

    async def async_execute(self, action: str, targets: list[str]) -> None:
        """Switch the targets; raises when any target has no such service (nothing was done to it)."""
        service = "turn_on" if action == "on" else "turn_off"
        # homeassistant.turn_on / off only logs a warning for these, which would read as "done".
        unsupported = sorted(t for t in targets if not self.hass.services.has_service(t.split(".")[0], service))
        supported = [t for t in targets if t not in unsupported]
        if supported:
            async with asyncio.timeout(SERVICE_TIMEOUT):
                await self.hass.services.async_call(
                    "homeassistant", service, {"entity_id": supported}, blocking=True
                )
        if unsupported:
            raise HomeAssistantError(f"Cannot turn {action}: {', '.join(unsupported)}")

    async def async_validate_conditions(self, conditions: list[dict[str, Any]]) -> bool:
        try:
            await condition.async_validate_conditions_config(self.hass, conditions)
        except (HomeAssistantError, vol.Invalid, ValueError, TypeError, KeyError):
            return False
        return True

    async def _async_conditions_pass(self, rule: dict[str, Any]) -> bool:
        try:
            validated = await condition.async_validate_conditions_config(self.hass, rule["conditions"])
            checker = await condition.async_from_config(
                self.hass, {"condition": "and", "conditions": validated}
            )
        except Exception as err:  # noqa: BLE001 - a broken condition skips the action, never crashes
            LOG.warning("Good Days timer %s: invalid conditions: %s", rule.get("name"), err)
            return False
        try:
            return bool(checker(self.hass, {}))
        finally:
            if hasattr(checker, "async_unload"):
                checker.async_unload()

    def _record(self, action: PlannedAction, status: str, reason: str | None = None) -> None:
        self.store.done[action.key] = action.when.isoformat()
        self.store.add_history(
            {
                "at": dt_util.now().isoformat(),
                "when": action.when.isoformat(),
                "rule_id": action.rule_id,
                "rule_name": action.rule_name,
                "action": action.action,
                "targets": list(action.targets),
                "status": status,
                "reason": reason,
            }
        )

    # Views --------------------------------------------------------------------

    def next_action(self, now: dt.datetime) -> PlannedAction | None:
        if not self.store.enabled:
            return None
        return next(
            (
                p
                for p in self.planned
                if p.when > now and p.key not in self.store.done and p.period_uid not in self.store.skip
            ),
            None,
        )

    def preview(self, now: dt.datetime, lang: str, profile: str | None = None) -> list[dict[str, Any]]:
        """The next Shabbat / Chag periods with every planned action (a dry run)."""
        planned = self.plan(now, profile)
        result = []
        for period in self.periods(now):
            actions = [p for p in planned if p.period_uid == period.uid]
            result.append(
                {
                    "uid": period.uid,
                    "title": period.title(lang),
                    "start": period.start.isoformat(),
                    "end": period.end.isoformat(),
                    "skipped": period.uid in self.store.skip,
                    "actions": [
                        {
                            "key": p.key,
                            "when": p.when.isoformat(),
                            "action": p.action,
                            "targets": list(p.targets),
                            "rule_id": p.rule_id,
                            "rule_name": p.rule_name,
                            "outside": p.outside,
                            "done": p.key in self.store.done,
                        }
                        for p in actions
                    ],
                    "conflicts": conflicts(actions),
                }
            )
        return result
