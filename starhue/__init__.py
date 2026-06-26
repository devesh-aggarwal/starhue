"""starhue — temperature → true star color + Planck spectrum.

Give it a temperature in kelvin; get back the actual sRGB color a blackbody of
that temperature would show your eye, the spectral curve behind it, and a pile
of derived physics (Wien peak, Stefan–Boltzmann exitance, spectral class).

    >>> import starhue
    >>> starhue.temperature_to_color(5772)   # the Sun
    '#fff1ea'
    >>> star = starhue.Star(3500)
    >>> star.spectral_type.letter
    'M'

See :class:`Star` for the high-level object and the ``color``/``physics``
submodules for the underlying functions.
"""

from __future__ import annotations

from .cct import color_to_temperature
from .classify import SpectralType, spectral_class
from .color import (
    hex_to_rgb,
    temperature_to_color,
    wavelength_to_color,
)
from .physics import (
    planck,
    planck_nm,
    spectrum,
    stefan_boltzmann,
    wien_peak_frequency,
    wien_peak_wavelength,
)
from .star import Star

__version__ = "1.1.1"

__all__ = [
    "__version__",
    "Star",
    "SpectralType",
    "spectral_class",
    # color
    "temperature_to_color",
    "wavelength_to_color",
    "hex_to_rgb",
    # inverse CCT (color → temperature)
    "color_to_temperature",
    # physics
    "planck",
    "planck_nm",
    "spectrum",
    "stefan_boltzmann",
    "wien_peak_wavelength",
    "wien_peak_frequency",
]
