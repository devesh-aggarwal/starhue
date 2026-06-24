"""Terminal rendering: truecolor swatches and a rainbow spectrum sparkline,
wrapped into a star "trading card". Pure stdlib, no dependencies.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, Sequence, Tuple

from . import color as _color
from .star import Star

__all__ = [
    "supports_color",
    "swatch",
    "spectrum_sparkline",
    "star_card",
]

_RESET = "\x1b[0m"
_BLOCKS = " ▁▂▃▄▅▆▇█"  # index 0 == empty, 1..8 == rising eighths
_FULL = "█"


def supports_color(stream: Optional[object] = None) -> bool:
    """Best-effort detection of 24-bit terminal color support.

    Honours the ``NO_COLOR`` and ``FORCE_COLOR`` conventions.
    """
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    stream = stream if stream is not None else sys.stdout
    try:
        return bool(stream.isatty())  # type: ignore[attr-defined]
    except Exception:
        return False


def _bg(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"\x1b[48;2;{r};{g};{b}m"


def _fg(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m"


def _mix(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )


def swatch(rgb: Tuple[int, int, int], width: int = 6, *, color: bool = True) -> str:
    """A solid bar of ``width`` cells in ``rgb``."""
    if not color:
        return _FULL * width
    return _bg(rgb) + " " * width + _RESET


def _column_color(w_nm: float) -> Tuple[int, int, int]:
    """Foreground tint for a spectrum column at wavelength ``w_nm``."""
    dim = (70, 70, 78)  # IR/UV: outside the eye's reach, drawn as cool gray
    if not _color.VISIBLE_LO_NM <= w_nm <= _color.VISIBLE_HI_NM:
        return dim
    base = _color.wavelength_to_color(w_nm, "rgb")
    # Lift very dark spectral tails so the silhouette stays visible.
    return _mix(dim, base, max(0.35, max(base) / 255.0))


def spectrum_sparkline(
    star: Star,
    width: int = 48,
    lo_nm: float = 300.0,
    hi_nm: float = 1100.0,
    *,
    color: bool = True,
) -> str:
    """One-line Unicode sparkline of the Planck curve, tinted by wavelength."""
    pts = star.spectrum(lo_nm, hi_nm, samples=width, normalize=True)
    out = []
    for w_nm, level in pts:
        ch = _BLOCKS[max(0, min(8, round(level * 8)))]
        out.append(f"{_fg(_column_color(w_nm))}{ch}{_RESET}" if color else ch)
    return "".join(out)


def _peak_marker_row(star: Star, width: int, lo_nm: float, hi_nm: float, *, color: bool) -> str:
    """A row with a caret under the column closest to the Wien peak."""
    peak = star.peak_wavelength_nm
    row = [" "] * width
    if lo_nm <= peak <= hi_nm:
        idx = round((peak - lo_nm) / (hi_nm - lo_nm) * (width - 1))
        idx = max(0, min(width - 1, idx))
        if color:
            row[idx] = f"{_fg(_color.wavelength_to_color(peak, 'rgb'))}▲{_RESET}"
        else:
            row[idx] = "^"
    return "".join(row)


def _human_exitance(value: float) -> str:
    if value >= 1e6:
        return f"{value / 1e6:.2f} MW/m²"
    if value >= 1e3:
        return f"{value / 1e3:.2f} kW/m²"
    return f"{value:.2f} W/m²"


def _frame(lines: Sequence[str], widths: Sequence[int]) -> str:
    """Wrap pre-measured lines (text, visible-width) in a rounded box."""
    inner = max(widths)
    top = "╭" + "─" * (inner + 2) + "╮"
    bottom = "╰" + "─" * (inner + 2) + "╯"
    body = []
    for text, w in zip(lines, widths):
        body.append("│ " + text + " " * (inner - w) + " │")
    return "\n".join([top, *body, bottom])


def star_card(star: Star, *, color: bool = True, spectrum: bool = True, width: int = 46) -> str:
    """A multi-line "trading card" for a star: swatch, stats and spectrum.

    Returns a string ready to ``print``. When ``color`` is false it degrades to
    a clean monochrome layout (useful for logs and non-TTY output).
    """
    rgb = star.rgb
    st = star.spectral_type
    sw = swatch(rgb, 8, color=color)

    # (visible text, visible width) pairs — width excludes ANSI escapes.
    rows: List[Tuple[str, int]] = []

    title = f"★  {star.temperature:g} K"
    klass = f"class {st.letter}"
    pad = width - len(title) - len(klass)
    rows.append((title + " " * max(1, pad) + klass, width))

    stats = f"{star.hex}  rgb{rgb}"
    rows.append((f"{sw}  {stats}", 8 + 2 + len(stats)))

    desc = f"{st.description} · {star.appearance}"
    rows.append((desc, len(desc)))

    rows.append(("", 0))

    peak = f"peak λ    {star.peak_wavelength_nm:.1f} nm  ·  {star.peak_frequency_hz:.3e} Hz"
    rows.append((peak, len(peak)))
    exit_line = f"exitance  {_human_exitance(star.radiant_exitance)}"
    rows.append((exit_line, len(exit_line)))

    if spectrum:
        rows.append(("", 0))
        lo, hi = 300.0, 1100.0
        spark = spectrum_sparkline(star, width, lo, hi, color=color)
        rows.append((spark, width))
        rows.append((_peak_marker_row(star, width, lo, hi, color=color), width))
        lo_label, hi_label = f"{lo:g}nm", f"{hi:g}nm"
        axis = lo_label + " " * (width - len(lo_label) - len(hi_label)) + hi_label
        rows.append((axis, width))

    texts = [t for t, _ in rows]
    widths = [w for _, w in rows]
    return _frame(texts, widths)
