"""Physical constants used throughout :mod:`starhue`.

All values are the exact CODATA / SI 2019 redefinition constants, so the
blackbody math is reproducible to full floating-point precision.
"""

from __future__ import annotations

#: Planck constant, J·s (exact since the 2019 SI redefinition).
H = 6.626_070_15e-34

#: Speed of light in vacuum, m·s⁻¹ (exact).
C = 299_792_458.0

#: Boltzmann constant, J·K⁻¹ (exact).
K_B = 1.380_649e-23

#: Stefan–Boltzmann constant, W·m⁻²·K⁻⁴ (derived, CODATA 2018).
SIGMA = 5.670_374_419e-8

#: Wien's displacement-law constant (wavelength form), m·K (CODATA 2018).
WIEN_B = 2.897_771_955e-3

#: First radiation constant for spectral radiance, 2·h·c², W·m²·sr⁻¹.
C1L = 2.0 * H * C * C

#: Second radiation constant, h·c / k_B, m·K.
C2 = H * C / K_B

__all__ = ["H", "C", "K_B", "SIGMA", "WIEN_B", "C1L", "C2"]
