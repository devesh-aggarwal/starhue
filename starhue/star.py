"""The ``Star`` — a friendly object that ties the physics and color pipelines
together for one temperature.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

from . import cct, color, physics
from .classify import SpectralType, appearance_name, spectral_class

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__ = ["Star"]


class Star:
    """A blackbody at a given temperature, with its color and spectrum on tap.

    Example:
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
        """Create a star at a given temperature.

        Args:
            temperature_k (float): Absolute temperature in kelvin (positive).
            color_step_nm (float): Wavelength step for the color integration, in
                nanometres (smaller is more accurate but slower).

        Raises:
            ValueError: If the temperature is not a positive, finite number.
        """
        physics._check_temperature(temperature_k)
        self.temperature = float(temperature_k)
        self._color_step_nm = color_step_nm

    # -- inverse constructor (color → temperature) --------------------------
    @classmethod
    def from_color(cls, color_value: Union[str, Tuple[float, float, float]]) -> "Star":
        """Build the nearest blackbody to a color.

        Args:
            color_value (str | tuple[float, float, float]): A ``#rrggbb`` hex
                string or an sRGB ``(r, g, b)`` triple (0–255).

        Returns:
            Star: The star whose temperature best matches the color.
        """
        return cls(cct.color_to_temperature(color_value))

    # -- color --------------------------------------------------------------
    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Display sRGB color as a ``(r, g, b)`` triple of 0–255 ints."""
        return color.temperature_to_color(self.temperature, "rgb", self._color_step_nm)

    @property
    def hex(self) -> str:
        """Display sRGB color as a ``#rrggbb`` string."""
        return color.temperature_to_color(self.temperature, "hex", self._color_step_nm)

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
        """Spectral radiance at a wavelength in nm (W·sr⁻¹·m⁻²·nm⁻¹).

        Args:
            wavelength_nm (float): Wavelength in nanometres.

        Returns:
            float: Spectral radiance per nanometre.
        """
        return physics.planck_nm(wavelength_nm, self.temperature)

    def spectrum(
        self,
        lo_nm: Optional[float] = None,
        hi_nm: Optional[float] = None,
        samples: int = 200,
    ) -> "Figure":
        """Plot the Planck curve across a wavelength band, tinted the star's color.

        Samples spectral radiance against wavelength (from the package physics,
        not loose constants) and draws it as a matplotlib figure. The curve is
        stroked in the star's own integrated sRGB color, on a dark background so
        even near-white stars stay legible.

        By default the band auto-fits around the star's Wien peak — ``0.4×`` to
        ``3×`` the peak wavelength — so the curve always rises from near zero,
        crests at its visible maximum, and decays down the tail, whatever the
        temperature. (A fixed band would push the peak off-screen for hot stars,
        whose peak lies in the UV.) Pass ``lo_nm``/``hi_nm`` to override.

        Args:
            lo_nm (float | None): Lower bound of the band, in nanometres. If
                None, ``0.4 ×`` the Wien peak wavelength.
            hi_nm (float | None): Upper bound of the band, in nanometres. If
                None, ``3 ×`` the Wien peak wavelength.
            samples (int): Number of evenly spaced samples (must be >= 2).

        Returns:
            matplotlib.figure.Figure: The figure, ready to ``.show()`` or
                ``.savefig(...)``. The caller owns it (and is responsible for
                closing it, e.g. ``matplotlib.pyplot.close(fig)``).

        Raises:
            ModuleNotFoundError: If matplotlib is not installed. Plotting is an
                optional extra — install it with ``pip install starhue[plot]``.
        """
        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError as exc:  # pragma: no cover - import guard
            raise ModuleNotFoundError(
                "Star.spectrum() needs matplotlib; install the plotting extra "
                "with `pip install starhue[plot]` (or `pip install matplotlib`)."
            ) from exc

        peak_nm = self.peak_wavelength_nm
        if lo_nm is None:
            lo_nm = 0.4 * peak_nm
        if hi_nm is None:
            hi_nm = 3.0 * peak_nm

        pts = physics.spectrum(self.temperature, lo_nm, hi_nm, samples)
        wavelengths = [w for w, _ in pts]
        radiance = [r for _, r in pts]
        line_color = tuple(channel / 255 for channel in self.rgb)

        bg = "#11131a"
        fig, ax = plt.subplots(figsize=(8, 6), facecolor=bg)
        ax.set_facecolor(bg)
        ax.plot(wavelengths, radiance, color=line_color, linewidth=2)
        ax.set_xlabel("Wavelength (nm)", color="0.85")
        ax.set_ylabel("Spectral radiance (W·sr⁻¹·m⁻²·nm⁻¹)", color="0.85")
        ax.set_title(
            f"Blackbody spectrum — {self.temperature:g} K (class {self.spectral_type.letter})",
            color="0.95",
        )
        ax.set_xlim(lo_nm, hi_nm)
        ax.set_ylim(bottom=0)
        ax.tick_params(colors="0.7")
        for spine in ax.spines.values():
            spine.set_color("0.4")
        fig.tight_layout()
        return fig

    # -- classification ------------------------------------------------------
    @property
    def spectral_type(self) -> SpectralType:
        """Harvard spectral classification (O/B/A/F/G/K/M)."""
        return spectral_class(self.temperature)

    @property
    def appearance(self) -> str:
        """A friendly perceptual color name, e.g. ``"neutral white"``.

        The color as seen in a vacuum (the Sun reads white here, not the yellow
        an atmosphere lends it); see ``starhue.classify.appearance_name``.
        """
        return appearance_name(self.temperature)

    def __repr__(self) -> str:
        return f"Star({self.temperature:g} K, {self.hex}, class {self.spectral_type.letter})"
