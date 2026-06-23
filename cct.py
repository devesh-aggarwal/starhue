"""Inverse direction: a color → its correlated color temperature (CCT).

The CCT of a color is *defined* as the temperature of the blackbody whose
chromaticity is closest to it in the CIE 1960 UCS ``(u, v)`` plane. We find it by
searching our own Planckian locus, so ``T → color → T`` round-trips cleanly.

Alongside the temperature we report **Duv**: the signed distance from the locus.
``Duv ≈ 0`` means the color really does look like a blackbody; a large
``|Duv|`` means "nearest blackbody" is the best we can say (positive = the green
side of the locus, negative = the pink/magenta side).
"""

from __future__ import annotations

import math
from typing import NamedTuple, Tuple

from . import color as _color

__all__ = ["CCTResult", "cct_from_rgb", "cct_from_hex"]

#: Temperature range over which CCT is meaningful, in kelvin.
T_MIN = 1000.0
T_MAX = 40000.0


class CCTResult(NamedTuple):
    """Result of an inverse-CCT query."""

    temperature_k: float  #: nearest blackbody temperature, K
    duv: float            #: signed distance from the Planckian locus in CIE 1960 uv


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


def cct_from_uv(u: float, v: float) -> CCTResult:
    """Nearest blackbody temperature (and Duv) for a CIE 1960 ``(u, v)`` color."""
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
    t_best = 1e6 / m_best

    duv = _signed_duv(t_best, u, v)
    return CCTResult(t_best, duv)


def _signed_duv(temperature_k: float, u: float, v: float) -> float:
    """Signed offset from the locus: + on the green side, − on the pink side."""
    dt = max(1.0, temperature_k * 1e-3)
    u0, v0 = _locus_uv(temperature_k - dt)
    u1, v1 = _locus_uv(temperature_k + dt)
    lu, lv = _locus_uv(temperature_k)

    # As temperature rises the locus runs down-and-left in (u, v); the normal
    # (ty, −tx) therefore points up toward the green side, matching the ANSI/Ohno
    # convention (Duv > 0 above the locus). Project (point − locus) onto it.
    tx, ty = (u1 - u0), (v1 - v0)
    norm = math.hypot(tx, ty)
    if norm == 0:
        return math.hypot(u - lu, v - lv)
    nx, ny = ty / norm, -tx / norm
    return (u - lu) * nx + (v - lv) * ny


def cct_from_xy(x: float, y: float) -> CCTResult:
    """Nearest blackbody temperature (and Duv) for a CIE 1931 ``(x, y)`` color."""
    return cct_from_uv(*_color.xy_to_uv(x, y))


def cct_from_rgb(rgb: Tuple[float, float, float]) -> CCTResult:
    """Nearest blackbody temperature (and Duv) for an sRGB ``(r, g, b)`` 0–255 color."""
    return cct_from_xy(*_color.rgb_to_xy(rgb))


def cct_from_hex(value: str) -> CCTResult:
    """Nearest blackbody temperature (and Duv) for a ``#rrggbb`` color."""
    return cct_from_rgb(_color.hex_to_rgb(value))
