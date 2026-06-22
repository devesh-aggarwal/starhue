"""From a Planck spectrum to a real sRGB colour.

The pipeline is the textbook colorimetry route:

1. Sample the Planck curve across the visible band.
2. Integrate against the CIE 1931 2° colour-matching functions → CIE XYZ.
3. Map XYZ → linear sRGB with the standard D65 matrix.
4. Clamp out-of-gamut negatives, normalise to constant luminance, gamma-encode.

The colour-matching functions use the analytic multi-lobe Gaussian fit of
Wyman, Sloan & Shirley, *"Simple Analytic Approximations to the CIE XYZ Colour
Matching Functions"*, JCGT 2(2), 2013. It reproduces the tabulated CIE curves
to within ~1% with no embedded data table.
"""

from __future__ import annotations

import math
from typing import Tuple

from .physics import planck_nm

__all__ = [
    "cie_1931_xyz",
    "spectrum_to_xyz",
    "xyz_to_xy",
    "xyz_to_srgb",
    "temperature_to_xyz",
    "temperature_to_rgb",
    "temperature_to_rgb01",
    "temperature_to_hex",
    "temperature_to_xy",
    "wavelength_to_rgb",
    "hex_to_rgb",
    "srgb_to_xyz",
    "rgb_to_xy",
    "xy_to_uv",
    "VISIBLE_LO_NM",
    "VISIBLE_HI_NM",
]

#: Lower / upper bounds of the integration band, nm. The Gaussian lobes have
#: negligible weight outside this, matching the usual 360–830 nm CIE table.
VISIBLE_LO_NM = 360.0
VISIBLE_HI_NM = 830.0

# Linear-sRGB → CIE XYZ is well conditioned; we want the inverse (XYZ → linear
# sRGB) under a D65 white point. These are the canonical IEC 61966-2-1 values.
_XYZ_TO_RGB = (
    (3.2406255, -1.5372080, -0.4986286),
    (-0.9689307, 1.8757561, 0.0415175),
    (0.0557101, -0.2040211, 1.0569959),
)

# The forward direction (linear sRGB → CIE XYZ, D65), used to read the
# chromaticity *out* of a colour for inverse-CCT work.
_RGB_TO_XYZ = (
    (0.4123908, 0.3575843, 0.1804808),
    (0.2126390, 0.7151687, 0.0721923),
    (0.0193308, 0.1191948, 0.9505322),
)


def _gauss(x: float, mu: float, s1: float, s2: float) -> float:
    """Piecewise (asymmetric) Gaussian lobe used by the Wyman et al. fit."""
    t = (x - mu) * (s1 if x < mu else s2)
    return math.exp(-0.5 * t * t)


def _matmul3(
    m: Tuple[Tuple[float, float, float], ...], v0: float, v1: float, v2: float
) -> Tuple[float, float, float]:
    """Multiply a 3×3 matrix ``m`` by the column vector ``(v0, v1, v2)``."""
    return (
        m[0][0] * v0 + m[0][1] * v1 + m[0][2] * v2,
        m[1][0] * v0 + m[1][1] * v1 + m[1][2] * v2,
        m[2][0] * v0 + m[2][1] * v1 + m[2][2] * v2,
    )


def cie_1931_xyz(wavelength_nm: float) -> Tuple[float, float, float]:
    """CIE 1931 2° colour-matching functions ``(x̄, ȳ, z̄)`` at one wavelength.

    Analytic multi-lobe Gaussian approximation (Wyman, Sloan & Shirley 2013).
    """
    w = wavelength_nm
    x = (
        1.056 * _gauss(w, 599.8, 0.0264, 0.0323)
        + 0.362 * _gauss(w, 442.0, 0.0624, 0.0374)
        - 0.065 * _gauss(w, 501.1, 0.0490, 0.0382)
    )
    y = 0.821 * _gauss(w, 568.8, 0.0213, 0.0247) + 0.286 * _gauss(w, 530.9, 0.0613, 0.0322)
    z = 1.217 * _gauss(w, 437.0, 0.0845, 0.0278) + 0.681 * _gauss(w, 459.0, 0.0385, 0.0725)
    return x, y, z


def spectrum_to_xyz(temperature_k: float, step_nm: float = 1.0) -> Tuple[float, float, float]:
    """Integrate a blackbody spectrum against the CMFs to get CIE XYZ.

    The absolute scale is irrelevant for hue (we normalise later), so the
    integration constant is dropped.
    """
    if step_nm <= 0:
        raise ValueError("step_nm must be positive")
    x_sum = y_sum = z_sum = 0.0
    w = VISIBLE_LO_NM
    while w <= VISIBLE_HI_NM + 1e-9:
        power = planck_nm(w, temperature_k)
        xb, yb, zb = cie_1931_xyz(w)
        x_sum += power * xb
        y_sum += power * yb
        z_sum += power * zb
        w += step_nm
    return x_sum * step_nm, y_sum * step_nm, z_sum * step_nm


def xyz_to_xy(x: float, y: float, z: float) -> Tuple[float, float]:
    """CIE XYZ → chromaticity coordinates ``(x, y)``."""
    total = x + y + z
    if total <= 0:
        return 0.0, 0.0
    return x / total, y / total


def _gamma_encode(c: float) -> float:
    """Linear-light channel → gamma-companded sRGB (IEC 61966-2-1)."""
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def xyz_to_srgb(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """CIE XYZ → display sRGB as three floats in ``[0, 1]``.

    Out-of-gamut negatives are clamped to zero and the result is normalised to
    constant maximum luminance, so the returned colour is the *hue* of the
    blackbody at full brightness (the conventional way to show star colours).
    """
    r, g, b = _matmul3(_XYZ_TO_RGB, x, y, z)

    # Clamp impossible (negative) colours back into gamut.
    r, g, b = max(0.0, r), max(0.0, g), max(0.0, b)

    # Normalise to constant luminance: brightest primary becomes 1.0.
    peak = max(r, g, b)
    if peak > 0:
        r, g, b = r / peak, g / peak, b / peak

    return _gamma_encode(r), _gamma_encode(g), _gamma_encode(b)


def temperature_to_xyz(temperature_k: float, step_nm: float = 1.0) -> Tuple[float, float, float]:
    """Convenience: temperature → CIE XYZ tristimulus values."""
    return spectrum_to_xyz(temperature_k, step_nm)


def temperature_to_xy(temperature_k: float, step_nm: float = 1.0) -> Tuple[float, float]:
    """Temperature → CIE 1931 chromaticity ``(x, y)`` on the Planckian locus."""
    return xyz_to_xy(*spectrum_to_xyz(temperature_k, step_nm))


def temperature_to_rgb01(temperature_k: float, step_nm: float = 1.0) -> Tuple[float, float, float]:
    """Temperature → display sRGB as three floats in ``[0, 1]``."""
    return xyz_to_srgb(*spectrum_to_xyz(temperature_k, step_nm))


def temperature_to_rgb(temperature_k: float, step_nm: float = 1.0) -> Tuple[int, int, int]:
    """Temperature → display sRGB as a ``(r, g, b)`` triple of 0–255 ints."""
    r, g, b = temperature_to_rgb01(temperature_k, step_nm)
    return _to_8bit(r), _to_8bit(g), _to_8bit(b)


def temperature_to_hex(temperature_k: float, step_nm: float = 1.0) -> str:
    """Temperature → ``#rrggbb`` sRGB hex string."""
    r, g, b = temperature_to_rgb(temperature_k, step_nm)
    return f"#{r:02x}{g:02x}{b:02x}"


def wavelength_to_rgb(wavelength_nm: float) -> Tuple[int, int, int]:
    """Display colour of a single monochromatic wavelength (0–255).

    Used to paint spectrum plots. The hue follows the spectral ramp
    (violet→blue→cyan→green→yellow→red) across the ~400–700 nm visible window,
    held at full brightness so the visible edges stay vivid. Past that window the
    colour dims smoothly to black — through the UV below 400 nm and the infrared
    above 700 nm — because those wavelengths are invisible to the eye.

    The violet end stops at a true blue-violet rather than running all the way to
    magenta: pink/magenta is non-spectral (no single wavelength looks pink), so
    no star and no rainbow should show it.

    The CIE colour-matching functions are deliberately *not* used for the hue:
    their near-zero tails past ~700 nm cross over, and once renormalised to full
    brightness that flips deep red back to pure green (the ȳ tail outlives x̄).
    """
    wh = min(700.0, max(400.0, wavelength_nm))  # hue plateau: violet 400 → red 700
    if wh < 450:
        r, g, b = 0.4 * (450 - wh) / 50.0, 0.0, 1.0  # blue-violet, capped short of magenta
    elif wh < 490:
        r, g, b = 0.0, (wh - 450) / 40.0, 1.0
    elif wh < 510:
        r, g, b = 0.0, 1.0, (510 - wh) / 20.0
    elif wh < 580:
        r, g, b = (wh - 510) / 70.0, 1.0, 0.0
    elif wh < 645:
        r, g, b = 1.0, (645 - wh) / 65.0, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0

    # Brightness envelope: full across the visible band, fading to black through
    # the UV (400 → 300 nm) and infrared (700 → 1000 nm).
    w = wavelength_nm
    if w < 400.0:
        f = max(0.0, (w - 300.0) / 100.0)
    elif w > 700.0:
        f = max(0.0, (1000.0 - w) / 300.0)
    else:
        f = 1.0

    gamma = 0.8  # mild lift for a richer, poster-like rainbow
    return _to_8bit((r * f) ** gamma), _to_8bit((g * f) ** gamma), _to_8bit((b * f) ** gamma)


def _to_8bit(c: float) -> int:
    return max(0, min(255, int(round(c * 255.0))))


# --------------------------------------------------------------------------
# Inverse direction: a display colour → chromaticity (for inverse CCT).
# --------------------------------------------------------------------------


def _gamma_decode(c: float) -> float:
    """Gamma-companded sRGB channel → linear light (inverse of :func:`_gamma_encode`)."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    """Parse a ``#rgb`` or ``#rrggbb`` string into a ``(r, g, b)`` 0–255 triple."""
    s = value.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"not a hex colour: {value!r}")
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        raise ValueError(f"not a hex colour: {value!r}") from None


def srgb_to_xyz(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Gamma-encoded sRGB (channels in ``[0, 1]``) → CIE XYZ."""
    rl, gl, bl = _gamma_decode(r), _gamma_decode(g), _gamma_decode(b)
    return _matmul3(_RGB_TO_XYZ, rl, gl, bl)


def rgb_to_xy(rgb: Tuple[float, float, float]) -> Tuple[float, float]:
    """An sRGB ``(r, g, b)`` triple (0–255) → CIE 1931 chromaticity ``(x, y)``."""
    r, g, b = rgb
    return xyz_to_xy(*srgb_to_xyz(r / 255.0, g / 255.0, b / 255.0))


def xy_to_uv(x: float, y: float) -> Tuple[float, float]:
    """CIE 1931 ``(x, y)`` → CIE 1960 UCS ``(u, v)`` — the space CCT is defined in."""
    denom = -2.0 * x + 12.0 * y + 3.0
    if denom == 0:
        return 0.0, 0.0
    return 4.0 * x / denom, 6.0 * y / denom
