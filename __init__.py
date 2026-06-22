"""starhue — temperature → true star colour + Planck spectrum.

Give it a temperature in kelvin; get back the actual sRGB colour a blackbody of
that temperature would show your eye, the spectral curve behind it, and a pile
of derived physics (Wien peak, Stefan–Boltzmann exitance, spectral class).

    >>> import starhue
    >>> starhue.temperature_to_hex(5772)   # the Sun
    '#fff1ea'
    >>> star = starhue.Star(3500)
    >>> star.spectral_type.letter
    'M'

See :class:`Star` for the high-level object and the ``color``/``physics``
submodules for the underlying functions.
"""

from __future__ import annotations

from .classify import SpectralType, spectral_class
from .color import (
    temperature_to_hex,
    temperature_to_rgb,
    temperature_to_rgb01,
    temperature_to_xy,
    temperature_to_xyz,
    wavelength_to_rgb,
)
from .physics import (
    planck,
    planck_nm,
    spectrum,
    stefan_boltzmann,
    wien_peak_frequency,
    wien_peak_wavelength,
    wien_peak_wavelength_nm,
)
from .star import Star

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Star",
    "SpectralType",
    "spectral_class",
    # colour
    "temperature_to_hex",
    "temperature_to_rgb",
    "temperature_to_rgb01",
    "temperature_to_xy",
    "temperature_to_xyz",
    "wavelength_to_rgb",
    # physics
    "planck",
    "planck_nm",
    "spectrum",
    "stefan_boltzmann",
    "wien_peak_wavelength",
    "wien_peak_wavelength_nm",
    "wien_peak_frequency",
]
