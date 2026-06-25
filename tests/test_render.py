"""Terminal rendering: color detection, swatches, the exitance humaniser and the
assembled star card. Color codes are ANSI escapes, so 'plain' output must carry
no ESC byte."""

from starhue import render
from starhue.render import _human_exitance, star_card, supports_color, swatch
from starhue.star import Star

ESC = "\x1b"
SUN = Star(5772.0)


class _FakeStream:
    def __init__(self, tty):
        self._tty = tty

    def isatty(self):
        return self._tty


# --------------------------------------------------------------------------
# supports_color
# --------------------------------------------------------------------------
def test_no_color_env_disables(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert supports_color(_FakeStream(True)) is False


def test_force_color_env_enables(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert supports_color(_FakeStream(False)) is True


def test_no_color_beats_force_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert supports_color(_FakeStream(True)) is False


def test_tty_detection(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert supports_color(_FakeStream(True)) is True
    assert supports_color(_FakeStream(False)) is False


def test_supports_color_swallows_broken_stream(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)

    class Broken:
        def isatty(self):
            raise RuntimeError("nope")

    assert supports_color(Broken()) is False


# --------------------------------------------------------------------------
# swatch
# --------------------------------------------------------------------------
def test_swatch_plain_is_full_blocks():
    assert swatch((255, 0, 0), 6, color=False) == "█" * 6


def test_swatch_color_has_ansi_and_reset():
    s = swatch((255, 0, 0), 6, color=True)
    assert "48;2;255;0;0" in s
    assert s.endswith("\x1b[0m")


# --------------------------------------------------------------------------
# _human_exitance
# --------------------------------------------------------------------------
def test_human_exitance_units():
    assert _human_exitance(500.0).endswith("W/m²")
    assert "kW/m²" in _human_exitance(5_000.0)
    assert "MW/m²" in _human_exitance(5_000_000.0)


# --------------------------------------------------------------------------
# star_card
# --------------------------------------------------------------------------
def test_card_plain_has_no_ansi():
    card = star_card(SUN, color=False, spectrum=False)
    assert ESC not in card


def test_card_contains_key_facts():
    card = star_card(SUN, color=False, spectrum=True)
    assert "5772 K" in card
    assert "class G" in card
    assert "#fff1ea" in card
    assert "neutral white" in card


def test_card_is_boxed():
    card = star_card(SUN, color=False, spectrum=False)
    assert card.startswith("╭")
    assert card.rstrip().endswith("╯")


def test_card_no_spectrum_drops_axis_labels():
    with_spec = star_card(SUN, color=False, spectrum=True)
    without = star_card(SUN, color=False, spectrum=False)
    assert "300nm" in with_spec and "1100nm" in with_spec
    assert "300nm" not in without


def test_card_color_mode_emits_ansi():
    assert ESC in star_card(SUN, color=True, spectrum=True)


def test_card_rows_are_padded_to_equal_width():
    lines = star_card(SUN, color=False, spectrum=True).splitlines()
    assert len({len(line) for line in lines}) == 1  # all rows equal visible width


# --------------------------------------------------------------------------
# spectrum_sparkline
# --------------------------------------------------------------------------
def test_sparkline_plain_length_matches_width():
    line = render.spectrum_sparkline(SUN, width=48, color=False)
    assert len(line) == 48
    assert ESC not in line
