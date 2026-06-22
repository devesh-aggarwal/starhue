"""Gorgeous, dependency-free SVG export.

Two showcase renderers:

* :func:`star_card_svg` — a glowing star disc, its stats, and the Planck curve
  painted with the visible-spectrum rainbow and a Wien-peak marker.
* :func:`gradient_strip_svg` — a smooth bar sweeping the blackbody locus across
  a temperature range.

Everything is built from plain strings, so there are no runtime dependencies and
the output opens in any browser.
"""

from __future__ import annotations

from typing import List, Tuple

from . import color as _color
from .star import Star

__all__ = ["star_card_svg", "gradient_strip_svg"]

_BG_TOP = "#0b0e16"
_BG_BOTTOM = "#05070d"
_FG = "#e8ecf4"
_MUTED = "#8b93a7"
_GRID = "#222838"
_FONT = "'Segoe UI', 'Helvetica Neue', Arial, system-ui, sans-serif"
_MONO = "'SF Mono', 'JetBrains Mono', 'Menlo', monospace"


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _spectrum_stops(lo_nm: float, hi_nm: float, step: float = 8.0) -> str:
    """Gradient stops painting the plot band with the perceived spectrum colour."""
    stops: List[str] = []
    n = max(2, int((hi_nm - lo_nm) / step) + 1)
    for i in range(n):
        w = lo_nm + (hi_nm - lo_nm) * i / (n - 1)
        if _color.VISIBLE_LO_NM <= w <= _color.VISIBLE_HI_NM:
            r, g, b = _color.wavelength_to_rgb(w)
        else:
            r, g, b = 60, 64, 78  # IR / UV — outside the eye's window
        off = i / (n - 1) * 100.0
        stops.append(f'<stop offset="{off:.2f}%" stop-color="rgb({r},{g},{b})"/>')
    return "".join(stops)


def _curve_points(
    star: Star, lo_nm: float, hi_nm: float, x0: float, x1: float, y0: float, y1: float, n: int
) -> List[Tuple[float, float]]:
    """Sample the normalised Planck curve into plot pixel coordinates."""
    pts = star.spectrum(lo_nm, hi_nm, samples=n, normalize=True)
    out = []
    for w, level in pts:
        px = x0 + (w - lo_nm) / (hi_nm - lo_nm) * (x1 - x0)
        py = y1 - level * (y1 - y0)
        out.append((px, py))
    return out


def _path_d(points: List[Tuple[float, float]]) -> str:
    return "M " + " L ".join(f"{px:.2f},{py:.2f}" for px, py in points)


def star_card_svg(star: Star, width: int = 760, height: int = 480) -> str:
    """Render a star as a self-contained showcase SVG (returns the markup)."""
    hexc = star.hex
    rgb = star.rgb
    st = star.spectral_type
    x_chrom, y_chrom = star.chromaticity

    # --- glowing star (top-left) -------------------------------------------
    # Two crossed diffraction spikes: each is a long, thin rect (the long axis
    # 340 px, the short axis 2.2 px) centred on the star.
    cx, cy, core_r = 130.0, 130.0, 40.0
    long_half, short_half, long_len, short_len = 170.0, 1.1, 340.0, 2.2
    spikes = []
    for horizontal in (True, False):
        w, h = (long_len, short_len) if horizontal else (short_len, long_len)
        x = cx - (long_half if horizontal else short_half)
        y = cy - (short_half if horizontal else long_half)
        spikes.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="url(#spike)" opacity="0.55"/>'
        )

    # --- spectrum plot (bottom) --------------------------------------------
    lo_nm, hi_nm = 300.0, 1000.0
    px0, px1 = 60.0, width - 40.0
    py0, py1 = 250.0, height - 56.0
    curve = _curve_points(star, lo_nm, hi_nm, px0, px1, py0, py1, 160)
    area = _path_d(curve) + f" L {px1:.2f},{py1:.2f} L {px0:.2f},{py1:.2f} Z"
    line = _path_d(curve)

    # x-axis ticks
    ticks = []
    for w in (300, 400, 500, 600, 700, 800, 900, 1000):
        tx = px0 + (w - lo_nm) / (hi_nm - lo_nm) * (px1 - px0)
        ticks.append(f'<line x1="{tx:.1f}" y1="{py1:.1f}" x2="{tx:.1f}" y2="{py1 + 5:.1f}" stroke="{_MUTED}"/>')
        ticks.append(
            f'<text x="{tx:.1f}" y="{py1 + 18:.1f}" fill="{_MUTED}" font-size="11" '
            f'font-family="{_MONO}" text-anchor="middle">{w}</text>'
        )
    # visible-band bracket shading
    vlo = px0 + (_color.VISIBLE_LO_NM - lo_nm) / (hi_nm - lo_nm) * (px1 - px0)
    vhi = px0 + (_color.VISIBLE_HI_NM - lo_nm) / (hi_nm - lo_nm) * (px1 - px0)

    # Wien peak marker
    peak = star.peak_wavelength_nm
    peak_marks = ""
    if lo_nm <= peak <= hi_nm:
        pxk = px0 + (peak - lo_nm) / (hi_nm - lo_nm) * (px1 - px0)
        peak_marks = (
            f'<line x1="{pxk:.1f}" y1="{py0 - 6:.1f}" x2="{pxk:.1f}" y2="{py1:.1f}" '
            f'stroke="{_FG}" stroke-width="1" stroke-dasharray="3 3" opacity="0.7"/>'
            f'<text x="{pxk:.1f}" y="{py0 - 12:.1f}" fill="{_FG}" font-size="11" '
            f'font-family="{_MONO}" text-anchor="middle">λ_max {peak:.0f} nm</text>'
        )

    text_x = 250.0
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{_FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{_BG_TOP}"/>
      <stop offset="100%" stop-color="{_BG_BOTTOM}"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{hexc}" stop-opacity="1"/>
      <stop offset="28%" stop-color="{hexc}" stop-opacity="0.85"/>
      <stop offset="60%" stop-color="{hexc}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{hexc}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="spike" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{hexc}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{hexc}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="spectrum" x1="0" y1="0" x2="1" y2="0">
      {_spectrum_stops(lo_nm, hi_nm)}
    </linearGradient>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#bg)"/>

  <!-- glowing star -->
  <circle cx="{cx}" cy="{cy}" r="110" fill="url(#glow)"/>
  {''.join(spikes)}
  <circle cx="{cx}" cy="{cy}" r="{core_r}" fill="{hexc}"/>
  <circle cx="{cx - 11}" cy="{cy - 11}" r="{core_r * 0.42:.1f}" fill="#ffffff" opacity="0.30"/>

  <!-- headline -->
  <text x="{text_x}" y="78" fill="{_FG}" font-size="48" font-weight="700">{star.temperature:g} K</text>
  <text x="{text_x}" y="108" fill="{_MUTED}" font-size="16">class {st.letter} — {_esc(st.description)}</text>
  <text x="{text_x}" y="150" fill="{_FG}" font-size="15" font-family="{_MONO}">{hexc}   rgb({rgb[0]}, {rgb[1]}, {rgb[2]})</text>
  <text x="{text_x}" y="174" fill="{_MUTED}" font-size="14">{_esc(star.appearance)}  ·  CIE xy ({x_chrom:.4f}, {y_chrom:.4f})</text>
  <text x="{text_x}" y="198" fill="{_MUTED}" font-size="14">peak λ {star.peak_wavelength_nm:.1f} nm  ·  exitance {star.radiant_exitance / 1e6:.2f} MW/m²</text>

  <!-- spectrum plot -->
  <rect x="{vlo:.1f}" y="{py0:.1f}" width="{vhi - vlo:.1f}" height="{py1 - py0:.1f}" fill="#ffffff" opacity="0.03"/>
  <line x1="{px0}" y1="{py1:.1f}" x2="{px1:.1f}" y2="{py1:.1f}" stroke="{_GRID}"/>
  <line x1="{px0}" y1="{py0:.1f}" x2="{px0}" y2="{py1:.1f}" stroke="{_GRID}"/>
  {''.join(ticks)}
  <path d="{area}" fill="url(#spectrum)" opacity="0.78"/>
  <path d="{line}" fill="none" stroke="{_FG}" stroke-width="2" opacity="0.9"/>
  {peak_marks}
  <text x="{(px0 + px1) / 2:.1f}" y="{height - 12}" fill="{_MUTED}" font-size="12" text-anchor="middle">spectral radiance vs. wavelength (nm) — Planck's law</text>
</svg>
"""


def gradient_strip_svg(
    t_min: float,
    t_max: float,
    steps: int = 64,
    width: int = 900,
    height: int = 200,
) -> str:
    """Render a smooth blackbody-locus gradient strip across a temperature range."""
    if steps < 2:
        raise ValueError("steps must be >= 2")
    stops = []
    for i in range(steps):
        t = t_min + (t_max - t_min) * i / (steps - 1)
        r, g, b = _color.temperature_to_rgb(t)
        off = i / (steps - 1) * 100.0
        stops.append(f'<stop offset="{off:.3f}%" stop-color="rgb({r},{g},{b})"/>')

    bar_y, bar_h = 30, height - 90
    ticks = []
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        t = t_min + (t_max - t_min) * frac
        tx = 20 + frac * (width - 40)
        anchor = "start" if frac == 0.0 else "end" if frac == 1.0 else "middle"
        ticks.append(
            f'<line x1="{tx:.1f}" y1="{bar_y + bar_h}" x2="{tx:.1f}" y2="{bar_y + bar_h + 6}" stroke="{_MUTED}"/>'
            f'<text x="{tx:.1f}" y="{bar_y + bar_h + 24:.0f}" fill="{_MUTED}" font-size="13" '
            f'font-family="{_MONO}" text-anchor="{anchor}">{round(t)} K</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{_FONT}">
  <defs>
    <linearGradient id="strip" x1="0" y1="0" x2="1" y2="0">
      {''.join(stops)}
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="{_BG_BOTTOM}"/>
  <text x="20" y="22" fill="{_FG}" font-size="14" font-weight="600">blackbody colour · {round(t_min)}–{round(t_max)} K</text>
  <rect x="20" y="{bar_y}" width="{width - 40}" height="{bar_h}" rx="10" fill="url(#strip)"/>
  {''.join(ticks)}
</svg>
"""
