"""The physical constants are the single source of truth — pin the exact SI
2019 / CODATA values and the two derived radiation constants."""

import math

from starhue import constants as k


def test_exact_si_constants():
    # Exact since the 2019 SI redefinition — these must not drift.
    assert k.H == 6.626_070_15e-34
    assert k.C == 299_792_458.0
    assert k.K_B == 1.380_649e-23


def test_codata_derived_constants():
    assert k.SIGMA == 5.670_374_419e-8
    assert k.WIEN_B == 2.897_771_955e-3


def test_first_radiation_constant_is_2hc2():
    assert k.C1L == 2.0 * k.H * k.C * k.C


def test_second_radiation_constant_is_hc_over_kb():
    assert k.C2 == k.H * k.C / k.K_B
    # Sanity: c₂ ≈ 0.0143877 m·K.
    assert math.isclose(k.C2, 0.014_387_77, rel_tol=1e-5)
