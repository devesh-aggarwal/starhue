"""Harvard spectral classification and plain-language color names."""

from __future__ import annotations

from typing import List, NamedTuple, Tuple

__all__ = ["SpectralType", "spectral_class", "appearance_name", "MK_CLASSES"]


class SpectralType(NamedTuple):
    """A Harvard spectral classification result."""

    letter: str          #: O, B, A, F, G, K or M
    description: str      #: short prose description


# (min_temp_K, letter, description). Upper-open on the hot end. The
# descriptions deliberately carry no color word — the card's single color
# comes from ``appearance_name`` (the computed intrinsic hue), so a textbook
# label like "yellow" for class G would only contradict it.
MK_CLASSES: List[Tuple[float, str, str]] = [
    (30000.0, "O", "blistering and short-lived"),
    (10000.0, "B", "massive and luminous"),
    (7500.0, "A", "strong hydrogen lines"),
    (6000.0, "F", "hotter than the Sun"),
    (5200.0, "G", "Sun-like"),
    (3700.0, "K", "cooler than the Sun"),
    (0.0, "M", "cool and abundant"),
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


# (max_temp_K exclusive, name). Each name tracks the hue the integrated
# Planck spectrum actually renders to in sRGB (see color.temperature_to_color),
# so the boundaries follow the computed red→orange→white→blue progression.
_APPEARANCE: List[Tuple[float, str]] = [
    (1300.0, "ember red"),
    (1900.0, "orange-red"),
    (2600.0, "deep orange"),
    (3400.0, "amber orange"),
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
