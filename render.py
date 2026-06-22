"""Terminal rendering: truecolor swatches, a rainbow spectrum sparkline, and
gradient strips. Pure stdlib, no dependencies.
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
    "gradient_strip",
]

_RESET = "\x1b[0m"
_BLOCKS = " ▁▂▃▄▅▆▇█"  # index 0 == empty, 1..8 == rising eighths
_FULL = "█"


def supports_color(stream: Optional[object] = None) -> bool:
    """Best-effort detection of 24-bit terminal colour support.

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


def _spectrum_columns(
    star: Star, width: int, lo_nm: float, hi_nm: float
) -> List[Tuple[int, Tuple[int, int, int], float]]:
    """Per-column (block-level 0..8, foreground colour, wavelength) for the curve."""
    pts = star.spectrum(lo_nm, hi_nm, samples=width, normalize=True)
    cols: List[Tuple[int, Tuple[int, int, int], float]] = []
    dim = (70, 70, 78)  # IR/UV: outside the eye's reach, drawn as cool grey
    for w_nm, level in pts:
        idx = max(0, min(8, int(round(level * 8))))
        if _color.VISIBLE_LO_NM <= w_nm <= _color.VISIBLE_HI_NM:
            base = _color.wavelength_to_rgb(w_nm)
            # Lift very dark spectral tails so the silhouette stays visible.
            fg = _mix(dim, base, max(0.35, max(base) / 255.0))
        else:
            fg = dim
        cols.append((idx, fg, w_nm))
    return cols


def spectrum_sparkline(
    star: Star,
    width: int = 48,
    lo_nm: float = 300.0,
    hi_nm: float = 1100.0,
    *,
    color: bool = True,
) -> str:
    """One-line Unicode sparkline of the Planck curve, tinted by wavelength."""
    cols = _spectrum_columns(star, width, lo_nm, hi_nm)
    out = []
    for level, fg, _w in cols:
        ch = _BLOCKS[level]
        out.append(f"{_fg(fg)}{ch}{_RESET}" if color else ch)
    return "".join(out)


def _peak_marker_row(star: Star, width: int, lo_nm: float, hi_nm: float, *, color: bool) -> str:
    """A row with a caret under the column closest to the Wien peak."""
    peak = star.peak_wavelength_nm
    row = [" "] * width
    if lo_nm <= peak <= hi_nm:
        idx = round((peak - lo_nm) / (hi_nm - lo_nm) * (width - 1))
        idx = max(0, min(width - 1, idx))
        if color:
            tint = _color.wavelength_to_rgb(peak) if lo_nm <= peak <= hi_nm else (200, 200, 200)
            row[idx] = f"{_fg(tint)}▲{_RESET}"
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
    x, y = star.chromaticity
    sw = swatch(rgb, 8, color=color)

    # (visible text, visible width) pairs — width excludes ANSI escapes.
    rows: List[Tuple[str, int]] = []

    title = f"★  {star.temperature:g} K"
    klass = f"class {st.letter}"
    pad = width - len(title) - len(klass)
    rows.append((title + " " * max(1, pad) + klass, width))

    line2 = f"{sw}  {star.hex}  rgb{rgb}"
    line2_w = 8 + 2 + len(f"{star.hex}  rgb{rgb}")
    rows.append((line2, line2_w))

    desc = f"{st.description} · {star.appearance}"
    rows.append((desc, len(desc)))

    rows.append(("", 0))

    peak = f"peak λ    {star.peak_wavelength_nm:.1f} nm  ·  {star.peak_frequency_hz:.3e} Hz"
    rows.append((peak, len(peak)))
    exit_line = f"exitance  {_human_exitance(star.radiant_exitance)}"
    rows.append((exit_line, len(exit_line)))
    chroma = f"CIE xy    ({x:.4f}, {y:.4f})"
    rows.append((chroma, len(chroma)))

    if spectrum:
        rows.append(("", 0))
        lo, hi = 300.0, 1100.0
        spark = spectrum_sparkline(star, width, lo, hi, color=color)
        rows.append((spark, width))
        rows.append((_peak_marker_row(star, width, lo, hi, color=color), width))
        axis = f"{lo:g}nm" + " " * (width - len(f"{lo:g}nm") - len(f"{hi:g}nm")) + f"{hi:g}nm"
        rows.append((axis, width))

    texts = [t for t, _ in rows]
    widths = [w for _, w in rows]
    return _frame(texts, widths)


def gradient_strip(
    t_min: float,
    t_max: float,
    steps: int = 24,
    *,
    color: bool = True,
    labels: bool = True,
    cell_width: int = 2,
) -> str:
    """A horizontal bar sweeping the blackbody locus from ``t_min`` to ``t_max``.

    Each cell is one temperature step; with ``labels`` the endpoints and a
    couple of interior temperatures are annotated below.
    """
    if steps < 2:
        raise ValueError("steps must be >= 2")
    temps = [t_min + (t_max - t_min) * i / (steps - 1) for i in range(steps)]
    cells = []
    for t in temps:
        rgb = _color.temperature_to_rgb(t)
        cells.append(_bg(rgb) + " " * cell_width + _RESET if color else _FULL * cell_width)
    bar = "".join(cells)
    if not labels:
        return bar

    total = steps * cell_width
    marks = [0, steps // 2, steps - 1]
    label_row = [" "] * total
    for m in marks:
        text = f"{round(temps[m])}K"
        start = m * cell_width
        # keep the label on-screen
        start = min(start, total - len(text))
        start = max(0, start)
        for i, ch in enumerate(text):
            if start + i < total:
                label_row[start + i] = ch
    return bar + "\n" + "".join(label_row)
