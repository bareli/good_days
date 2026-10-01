"""Repository conventions (SPEC §6.4 / §10) enforced as tests."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "good_days"
BIDI_CONTROLS = {chr(c) for c in (0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A))}


def _sources():
    yield from (ROOT / "www").glob("*.js")
    yield from (ROOT / "translations").glob("*.json")
    yield ROOT / "strings.json"
    yield from ROOT.glob("*.py")
    yield from (ROOT.parent.parent / "tests").glob("*.py")


def test_no_literal_bidi_control_characters():
    """Use escapes (\\u2068 ... \\u2069) in source, never the invisible characters."""
    offenders = {
        path.name: sorted({hex(ord(ch)) for ch in path.read_text(encoding="utf-8") if ch in BIDI_CONTROLS})
        for path in _sources()
    }
    assert {k: v for k, v in offenders.items() if v} == {}


def test_frontend_has_no_console_or_inner_html():
    for path in (ROOT / "www").glob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert "console." not in text, path.name
        assert "innerHTML" not in text, path.name
