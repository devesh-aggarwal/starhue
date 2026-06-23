"""The :class:`Star` — a friendly object that ties the physics and color
pipelines together for one temperature.
"""

from __future__ import annotations

from typing import List, Tuple, Union

from . import cct, color, physics
from .classify import SpectralType, appearance_name, spectral_class

__all__ = ["Star"]


class Star:
    """A blackbody at a given temperature, with its color and spectrum on tap.

    Example
    -------
    >>> from starhue import Star
    >>> sun = Star(5772)
    >>> sun.hex
    '#fff1ea'
    >>> round(sun.peak_wavelength_nm)
    502
    >>> sun.spectral_type.letter
    'G'
    """

    __slots__ = ("temperature", "_color_step_nm")

    def __init__(self, temperature_k: float, *, color_step_nm: float = 1.0) -> None:
        physics._check_temperature(temperature_k)
        self.temperature = float(temperature_k)
        self._color_step_nm = color_step_nm

    # -- inverse constructor (color → temperature) --------------------------
    @classmethod
    def from_color(cls, color_value: Union[str, Tuple[float, float, float]]) -> "Star":
        """Build the nearest blackbody to a color given as ``#rrggbb`` hex or an
        sRGB ``(r, g, b)`` triple (0–255)."""
        if isinstance(color_value, str):
            return cls(cct.cct_from_hex(color_value).temperature_k)
        return cls(cct.cct_from_rgb(color_value).temperature_k)

    # -- color --------------------------------------------------------------
    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Display sRGB color as a ``(r, g, b)`` triple of 0–255 ints."""
        return color.temperature_to_rgb(self.temperature, self._color_step_nm)

    @property
    def hex(self) -> str:
        """Display sRGB color as a ``#rrggbb`` string."""
        return color.temperature_to_hex(self.temperature, self._color_step_nm)

    # -- physics -------------------------------------------------------------
    @property
    def peak_wavelength_nm(self) -> float:
        """Wavelength of peak spectral radiance (Wien's law), nm."""
        return physics.wien_peak_wavelength(self.temperature)

    @property
    def peak_frequency_hz(self) -> float:
        """Frequency of peak spectral radiance (frequency-form Wien's law), Hz."""
        return physics.wien_peak_frequency(self.temperature)

    @property
    def radiant_exitance(self) -> float:
        """Total power radiated per unit area (Stefan–Boltzmann), W·m⁻²."""
        return physics.stefan_boltzmann(self.temperature)

    def planck(self, wavelength_nm: float) -> float:
        """Spectral radiance at a wavelength in nm (W·sr⁻¹·m⁻²·nm⁻¹)."""
        return physics.planck_nm(wavelength_nm, self.temperature)

    def spectrum(
        self,
        lo_nm: float = 300.0,
        hi_nm: float = 1100.0,
        samples: int = 200,
        *,
        normalize: bool = False,
    ) -> List[Tuple[float, float]]:
        """Sample the Planck curve; see :func:`starhue.physics.spectrum`."""
        return physics.spectrum(self.temperature, lo_nm, hi_nm, samples, normalize=normalize)

    # -- classification ------------------------------------------------------
    @property
    def spectral_type(self) -> SpectralType:
        """Harvard spectral classification (O/B/A/F/G/K/M)."""
        return spectral_class(self.temperature)

    @property
    def appearance(self) -> str:
        """A friendly perceptual color name, e.g. ``"neutral white"``.

        The color as seen in a vacuum (the Sun reads white here, not the yellow
        an atmosphere lends it); see :func:`starhue.classify.appearance_name`.
        """
        return appearance_name(self.temperature)

    def __repr__(self) -> str:
        return f"Star({self.temperature:g} K, {self.hex}, class {self.spectral_type.letter})"
