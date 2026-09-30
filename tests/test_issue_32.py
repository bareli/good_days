"""#32 (BUG-009): a user-typed name inside a title is a bidi isolate (FSI ... PDI), so counts stay in place."""
from __future__ import annotations

import datetime as dt

from custom_components.good_days.family import FamilyEvent

FSI, PDI = "\u2068", "\u2069"
UTC = dt.timezone.utc


def _event(name: str, kind: str, years: int | None) -> FamilyEvent:
    start = dt.datetime(2026, 10, 2, tzinfo=UTC)
    return FamilyEvent(uid="u", date_id="d", name=name, kind=kind, first_day=start.date(), start=start,
                       end=start + dt.timedelta(days=1), all_day=True, years=years)


def test_issue_32_names_are_isolated_in_titles() -> None:
    assert _event("סבא משה", "yahrzeit", 17).title("en") == f"Yahrzeit: {FSI}סבא משה{PDI} (17)"
    assert _event("דני", "birthday", 37).title("en") == f"{FSI}דני{PDI}'s birthday (37)"
    assert _event("דני", "birthday", None).title("en") == f"{FSI}דני{PDI}'s birthday"
    assert _event("Grandpa Sam", "birthday", 80).title("he") == f"יום הולדת 80 ל{FSI}Grandpa Sam{PDI}"
    assert _event("Grandpa Sam", "birthday", None).title("he") == f"יום הולדת ל{FSI}Grandpa Sam{PDI}"
    assert _event("Sara & Avi", "anniversary", 5).title("he") == f"יום נישואין: {FSI}Sara & Avi{PDI} (5)"
    # A custom date's title is the name alone: nothing to keep apart.
    assert _event("Bar Mitzvah", "custom", None).title("en") == "Bar Mitzvah"
