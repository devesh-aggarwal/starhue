"""Inverse direction: a color → its correlated color temperature (CCT).

The CCT of a color is *defined* as the temperature of the blackbody whose
chromaticity is closest to it in the CIE 1960 UCS ``(u, v)`` plane. We find it by
searching our own Planckian locus, so ``T → color → T`` round-trips cleanly.
"""

from __future__ import annotations

import math
from typing import Tuple, Union

from . import color as _color

__all__ = ["color_to_temperature"]

#: Temperature range over which CCT is meaningful, in kelvin.
T_MIN = 1000.0
T_MAX = 40000.0


def _locus_uv(temperature_k: float) -> Tuple[float, float]:
    return _color.xy_to_uv(*_color.xyz_to_xy(*_color.spectrum_to_xyz(temperature_k)))


def _dist2_at_mired(mired: float, u: float, v: float) -> float:
    lu, lv = _locus_uv(1e6 / mired)
    return (u - lu) ** 2 + (v - lv) ** 2


def _golden_min(f, a: float, b: float, iters: int = 40) -> float:
    """Golden-section search for the minimizer of a unimodal ``f`` on ``[a, b]``."""
    inv_phi = (math.sqrt(5.0) - 1.0) / 2.0
    c = b - inv_phi * (b - a)
    d = a + inv_phi * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(iters):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - inv_phi * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + inv_phi * (b - a)
            fd = f(d)
    return (a + b) / 2.0


def _cct_from_uv(u: float, v: float) -> float:
    """Nearest blackbody temperature (K) for a CIE 1960 ``(u, v)`` color."""
    # Work in mired (10⁶/T): the Planckian locus is nearly straight there, so a
    # coarse grid reliably brackets the minimum before we refine.
    m_lo, m_hi = 1e6 / T_MAX, 1e6 / T_MIN
    grid = 80
    best_i, best_d2 = 0, float("inf")
    mireds = [m_lo + (m_hi - m_lo) * i / (grid - 1) for i in range(grid)]
    for i, m in enumerate(mireds):
        d2 = _dist2_at_mired(m, u, v)
        if d2 < best_d2:
            best_i, best_d2 = i, d2

    a = mireds[max(0, best_i - 1)]
    b = mireds[min(grid - 1, best_i + 1)]
    m_best = _golden_min(lambda m: _dist2_at_mired(m, u, v), a, b)
    return 1e6 / m_best


def color_to_temperature(color: Union[str, Tuple[float, float, float]]) -> float:
    """Correlated color temperature (K) of a color — the nearest blackbody on the
    Planckian locus.

    Round-trips with ``starhue.temperature_to_color``.

    Args:
        color (str | tuple[float, float, float]): A ``#rrggbb`` hex string or an
            sRGB ``(r, g, b)`` triple (0–255).

    Returns:
        float: The correlated color temperature in kelvin.
    """
    rgb = _color.hex_to_rgb(color) if isinstance(color, str) else color
    return _cct_from_uv(*_color.xy_to_uv(*_color.rgb_to_xy(rgb)))
