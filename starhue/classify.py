"""Harvard spectral classification and plain-language color names."""

from __future__ import annotations

from typing import List, NamedTuple, Tuple

__all__ = ["SpectralType", "spectral_class", "appearance_name", "MK_CLASSES"]


class SpectralType(NamedTuple):
    """A Harvard spectral classification result."""

    letter: str          #: O, B, A, F, G, K or M
    description: str      #: short prose description


# (min_temp_K, letter, description). Upper-open on the hot end.
MK_CLASSES: List[Tuple[float, str, str]] = [
    (30000.0, "O", "blue, blistering and short-lived"),
    (10000.0, "B", "blue-white, massive and luminous"),
    (7500.0, "A", "white with strong hydrogen lines"),
    (6000.0, "F", "yellow-white"),
    (5200.0, "G", "yellow, Sun-like"),
    (3700.0, "K", "orange, cooler than the Sun"),
    (0.0, "M", "red, cool and abundant"),
]


def spectral_class(temperature_k: float) -> SpectralType:
    """Return the Harvard spectral type for an effective temperature.

    Args:
        temperature_k (float): Effective temperature in kelvin.

    Returns:
        SpectralType: The matching spectral class and its description.
    """
    for min_t, letter, desc in MK_CLASSES:
        if temperature_k >= min_t:
            return SpectralType(letter, desc)
    # The last bucket starts at 0 K, so the loop always returns for a normal
    # temperature; this only guards a non-finite value slipping through.
    _, letter, desc = MK_CLASSES[-1]
    return SpectralType(letter, desc)


# (max_temp_K exclusive, name). The colors people actually perceive.
_APPEARANCE: List[Tuple[float, str]] = [
    (1200.0, "dim ember red"),
    (2200.0, "deep red"),
    (3200.0, "reddish orange"),
    (4200.0, "warm amber"),
    (5000.0, "pale gold"),
    (5600.0, "soft yellow-white"),
    (6600.0, "neutral white"),
    (8000.0, "cool white"),
    (12000.0, "blue-white"),
    (float("inf"), "icy blue"),
]


def appearance_name(temperature_k: float) -> str:
    """A friendly, perceptual color name for a blackbody temperature.

    This is the star's color as seen *in a vacuum* — the light leaving its
    surface, before any atmosphere reddens it. So the Sun (5772 K) comes out a
    neutral white here, not the yellow it looks from the ground (Earth's
    atmosphere scatters away the blue and tints the disc yellow).

    Args:
        temperature_k (float): Absolute temperature in kelvin.

    Returns:
        str: A perceptual color name, e.g. ``"neutral white"``.
    """
    for max_t, name in _APPEARANCE:
        if temperature_k < max_t:
            return name
    # The final bucket has max_t == inf, so the loop always returns above.
    return _APPEARANCE[-1][1]
