"""Harvard spectral classification and plain-language colour names."""

from __future__ import annotations

from typing import List, NamedTuple, Tuple

__all__ = ["SpectralType", "spectral_class", "appearance_name", "MK_CLASSES"]


class SpectralType(NamedTuple):
    """A Harvard spectral classification result."""

    letter: str          #: O, B, A, F, G, K or M
    description: str      #: short prose description
    example: str         #: a familiar star of roughly this class


# (min_temp_K, letter, description, example star). Upper-open on the hot end.
MK_CLASSES: List[Tuple[float, str, str, str]] = [
    (30000.0, "O", "blue, blistering and short-lived", "Mintaka"),
    (10000.0, "B", "blue-white, massive and luminous", "Rigel"),
    (7500.0, "A", "white with strong hydrogen lines", "Sirius"),
    (6000.0, "F", "yellow-white", "Procyon"),
    (5200.0, "G", "yellow, Sun-like", "the Sun"),
    (3700.0, "K", "orange, cooler than the Sun", "Arcturus"),
    (0.0, "M", "red, cool and abundant", "Betelgeuse"),
]


def spectral_class(temperature_k: float) -> SpectralType:
    """Return the Harvard spectral type for an effective temperature."""
    for min_t, letter, desc, example in MK_CLASSES:
        if temperature_k >= min_t:
            return SpectralType(letter, desc, example)
    # The last bucket starts at 0 K, so the loop always returns for a normal
    # temperature; this only guards a non-finite value slipping through.
    _, letter, desc, example = MK_CLASSES[-1]
    return SpectralType(letter, desc, example)


# (max_temp_K exclusive, name). The colours people actually perceive.
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
    """A friendly, perceptual colour name for a blackbody temperature."""
    for max_t, name in _APPEARANCE:
        if temperature_k < max_t:
            return name
    # The final bucket has max_t == inf, so the loop always returns above.
    return _APPEARANCE[-1][1]
