"""Physics of the blackbody follows Planck's law, Wien's law, Stefan–Boltzmann.
"""

from __future__ import annotations

import math
from typing import List, Tuple

from .constants import C1L, C2, H, K_B, SIGMA, WIEN_B

__all__ = [
    "planck",
    "planck_nm",
    "wien_peak_wavelength",
    "wien_peak_frequency",
    "stefan_boltzmann",
    "spectrum",
]

#: Root of ``(x - 3)·eˣ + 3 = 0`` — the dimensionless peak of the Planck curve
#: in frequency space. Used for the frequency form of Wien's law.
_WIEN_FREQUENCY_ROOT = 2.821_439_372_122_078_9


def _check_temperature(temperature_k: float) -> None:
    if not math.isfinite(temperature_k) or temperature_k <= 0:
        raise ValueError(
            f"temperature must be a positive, finite number of kelvin, got {temperature_k!r}"
        )


def planck(wavelength_m: float, temperature_k: float) -> float:
    """Planck spectral radiance, in W·sr⁻¹·m⁻³ (power / area / solid angle / wavelength).

    Computes ``B_λ(T) = (2hc² / λ⁵) / (exp(hc / λ·k_B·T) − 1)``.

    Args:
        wavelength_m (float): Wavelength in metres.
        temperature_k (float): Absolute temperature in kelvin.

    Returns:
        float: Spectral radiance in W·sr⁻¹·m⁻³.

    Raises:
        ValueError: If the temperature or wavelength is not a positive, finite
            number.
    """
    _check_temperature(temperature_k)
    if not math.isfinite(wavelength_m) or wavelength_m <= 0:
        raise ValueError(f"wavelength must be a positive number of metres, got {wavelength_m!r}")
    x = C2 / (wavelength_m * temperature_k)
    # for large x the radiance is effectively zero, and
    # math.expm1 would otherwise raise OverflowError around x ~ 709.
    if x > 700.0:
        return 0.0
    return C1L / (wavelength_m**5 * math.expm1(x))


def planck_nm(wavelength_nm: float, temperature_k: float) -> float:
    """Planck spectral radiance for a wavelength given in nanometres.

    Args:
        wavelength_nm (float): Wavelength in nanometres.
        temperature_k (float): Absolute temperature in kelvin.

    Returns:
        float: Spectral radiance per nanometre (W·sr⁻¹·m⁻²·nm⁻¹), useful for
            plotting against a wavelength axis in nm.
    """
    return planck(wavelength_nm * 1e-9, temperature_k) * 1e-9


def wien_peak_wavelength(temperature_k: float, unit: str = "nm") -> float:
    """Wavelength of peak spectral radiance (Wien's displacement law).

    Args:
        temperature_k (float): Absolute temperature in kelvin.
        unit (str): Output unit, ``"nm"`` (default) or ``"m"``.

    Returns:
        float: Peak wavelength in the requested unit.

    Raises:
        ValueError: If the temperature is not positive/finite, or ``unit`` is
            neither ``"nm"`` nor ``"m"``.
    """
    _check_temperature(temperature_k)
    metres = WIEN_B / temperature_k
    if unit == "nm":
        return metres * 1e9
    if unit == "m":
        return metres
    raise ValueError(f"unit must be 'nm' or 'm', got {unit!r}")


def wien_peak_frequency(temperature_k: float) -> float:
    """Frequency of peak spectral radiance (frequency form of Wien's law), in Hz.

    Note this peak does **not** correspond to the wavelength peak: the two forms
    of Planck's law have differently-shaped curves, so ``c / ν_max`` differs from
    ``wien_peak_wavelength``. This is the classic "Wien peak paradox".

    Args:
        temperature_k (float): Absolute temperature in kelvin.

    Returns:
        float: Frequency of peak spectral radiance in Hz.

    Raises:
        ValueError: If the temperature is not a positive, finite number.
    """
    _check_temperature(temperature_k)
    return _WIEN_FREQUENCY_ROOT * K_B * temperature_k / H


def stefan_boltzmann(temperature_k: float) -> float:
    """Total radiant exitance of a blackbody, in W·m⁻² (Stefan–Boltzmann law: σT⁴).

    Args:
        temperature_k (float): Absolute temperature in kelvin.

    Returns:
        float: Total radiant exitance in W·m⁻².

    Raises:
        ValueError: If the temperature is not a positive, finite number.
    """
    _check_temperature(temperature_k)
    return SIGMA * temperature_k**4


def spectrum(
    temperature_k: float,
    lo_nm: float = 300.0,
    hi_nm: float = 1100.0,
    samples: int = 200,
    *,
    normalize: bool = False,
) -> List[Tuple[float, float]]:
    """Sample the Planck curve across a wavelength band.

    Args:
        temperature_k (float): Absolute temperature in kelvin.
        lo_nm (float): Lower bound of the band, in nanometres.
        hi_nm (float): Upper bound of the band, in nanometres.
        samples (int): Number of evenly spaced samples (must be >= 2).
        normalize (bool): If True, scale the radiance so its peak within the
            band is 1.0 — handy for plotting curves of wildly different
            temperatures on the same axis.

    Returns:
        list[tuple[float, float]]: ``(wavelength_nm, radiance)`` pairs.

    Raises:
        ValueError: If the temperature is non-positive, ``samples < 2``, or
            ``hi_nm <= lo_nm``.
    """
    _check_temperature(temperature_k)
    if samples < 2:
        raise ValueError("samples must be >= 2")
    if hi_nm <= lo_nm:
        raise ValueError("hi_nm must be greater than lo_nm")
    step = (hi_nm - lo_nm) / (samples - 1)
    wavelengths = [lo_nm + i * step for i in range(samples)]
    pts = [(w, planck_nm(w, temperature_k)) for w in wavelengths]
    if normalize:
        peak = max((r for _, r in pts), default=0.0)
        if peak > 0:
            pts = [(w, r / peak) for w, r in pts]
    return pts
