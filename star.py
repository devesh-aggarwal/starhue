"""The :class:`Star` — a friendly object that ties the physics and colour
pipelines together for one temperature.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from . import color, physics
from .classify import SpectralType, appearance_name, spectral_class

__all__ = ["Star"]


class Star:
    """A blackbody at a given temperature, with its colour and spectrum on tap.

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

    # -- colour --------------------------------------------------------------
    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Display sRGB colour as a ``(r, g, b)`` triple of 0–255 ints."""
        return color.temperature_to_rgb(self.temperature, self._color_step_nm)

    @property
    def rgb01(self) -> Tuple[float, float, float]:
        """Display sRGB colour as three floats in ``[0, 1]``."""
        return color.temperature_to_rgb01(self.temperature, self._color_step_nm)

    @property
    def hex(self) -> str:
        """Display sRGB colour as a ``#rrggbb`` string."""
        return color.temperature_to_hex(self.temperature, self._color_step_nm)

    @property
    def xyz(self) -> Tuple[float, float, float]:
        """CIE 1931 XYZ tristimulus values."""
        return color.temperature_to_xyz(self.temperature, self._color_step_nm)

    @property
    def chromaticity(self) -> Tuple[float, float]:
        """CIE 1931 chromaticity ``(x, y)`` on the Planckian locus."""
        return color.temperature_to_xy(self.temperature, self._color_step_nm)

    # -- physics -------------------------------------------------------------
    @property
    def peak_wavelength_nm(self) -> float:
        """Wavelength of peak spectral radiance (Wien's law), nm."""
        return physics.wien_peak_wavelength_nm(self.temperature)

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
        """A friendly perceptual colour name, e.g. ``"neutral white"``."""
        return appearance_name(self.temperature)

    # -- misc ----------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """A JSON-serialisable summary of everything known about the star."""
        r, g, b = self.rgb
        x, y = self.chromaticity
        st = self.spectral_type
        return {
            "temperature_k": self.temperature,
            "hex": self.hex,
            "rgb": [r, g, b],
            "chromaticity_xy": [x, y],
            "peak_wavelength_nm": self.peak_wavelength_nm,
            "peak_frequency_hz": self.peak_frequency_hz,
            "radiant_exitance_w_m2": self.radiant_exitance,
            "spectral_class": st.letter,
            "spectral_description": st.description,
            "appearance": self.appearance,
        }

    def __repr__(self) -> str:
        return f"Star({self.temperature:g} K, {self.hex}, class {self.spectral_type.letter})"
