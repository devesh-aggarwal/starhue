"""Blackbody physics: Planck's law, Wien's two peaks, Stefan–Boltzmann, and the
band sampler. Assertions are anchored to closed-form values and invariants."""

import math

import pytest

from starhue import physics as p
from starhue.constants import SIGMA, WIEN_B

SUN = 5772.0


# --------------------------------------------------------------------------
# planck / planck_nm
# --------------------------------------------------------------------------
def test_planck_positive_radiance():
    assert p.planck(500e-9, SUN) > 0.0


def test_planck_nm_matches_planck_in_metres():
    # planck_nm is just planck(λ·1e-9)·1e-9.
    assert math.isclose(p.planck_nm(500.0, SUN), p.planck(500e-9, SUN) * 1e-9)


def test_planck_nm_known_value():
    assert math.isclose(p.planck_nm(500.0, SUN), 26238.54056859585, rel_tol=1e-9)


def test_planck_peaks_near_wien_wavelength():
    peak_nm = p.wien_peak_wavelength(SUN)
    here = p.planck_nm(peak_nm, SUN)
    assert here > p.planck_nm(peak_nm - 80, SUN)
    assert here > p.planck_nm(peak_nm + 80, SUN)


def test_planck_underflows_to_zero_in_the_far_uv_tail():
    # x = c₂/(λT) > 700 ⇒ guarded to 0.0 instead of an OverflowError.
    assert p.planck(1e-9, 100.0) == 0.0


@pytest.mark.parametrize("bad_t", [0.0, -1.0, float("inf"), float("nan")])
def test_planck_rejects_bad_temperature(bad_t):
    with pytest.raises(ValueError):
        p.planck(500e-9, bad_t)


@pytest.mark.parametrize("bad_w", [0.0, -1.0, float("nan")])
def test_planck_rejects_bad_wavelength(bad_w):
    with pytest.raises(ValueError):
        p.planck(bad_w, SUN)


# --------------------------------------------------------------------------
# Wien — wavelength form
# --------------------------------------------------------------------------
def test_wien_wavelength_sun_is_about_502nm():
    assert round(p.wien_peak_wavelength(SUN)) == 502


def test_wien_displacement_invariant():
    # λ_max · T = b  (the whole content of Wien's law).
    for t in (1000.0, 3000.0, SUN, 12000.0):
        assert math.isclose(p.wien_peak_wavelength(t, "m") * t, WIEN_B, rel_tol=1e-12)


def test_wien_wavelength_unit_metres():
    assert math.isclose(
        p.wien_peak_wavelength(SUN, "m") * 1e9, p.wien_peak_wavelength(SUN, "nm")
    )


def test_wien_wavelength_rejects_bad_unit():
    with pytest.raises(ValueError):
        p.wien_peak_wavelength(SUN, "angstrom")


def test_wien_wavelength_rejects_bad_temperature():
    with pytest.raises(ValueError):
        p.wien_peak_wavelength(-5.0)


# --------------------------------------------------------------------------
# Wien — frequency form
# --------------------------------------------------------------------------
def test_wien_frequency_scales_linearly_with_temperature():
    assert math.isclose(p.wien_peak_frequency(2 * SUN), 2 * p.wien_peak_frequency(SUN))


def test_wien_frequency_known_value():
    assert math.isclose(p.wien_peak_frequency(SUN), 339331594731374.75, rel_tol=1e-9)


def test_wien_frequency_peak_differs_from_wavelength_peak():
    # The "Wien peak paradox": c/ν_max ≠ λ_max.
    nm_from_freq = (299_792_458.0 / p.wien_peak_frequency(SUN)) * 1e9
    assert not math.isclose(nm_from_freq, p.wien_peak_wavelength(SUN), rel_tol=0.05)


def test_wien_frequency_rejects_bad_temperature():
    with pytest.raises(ValueError):
        p.wien_peak_frequency(0.0)


# --------------------------------------------------------------------------
# Stefan–Boltzmann
# --------------------------------------------------------------------------
def test_stefan_boltzmann_is_sigma_t4():
    assert math.isclose(p.stefan_boltzmann(SUN), SIGMA * SUN**4)


def test_stefan_boltzmann_unit_temperature_is_sigma():
    assert math.isclose(p.stefan_boltzmann(1.0), SIGMA)


def test_stefan_boltzmann_quartic_scaling():
    # Double the temperature ⇒ 16× the exitance.
    assert math.isclose(p.stefan_boltzmann(2 * SUN), 16 * p.stefan_boltzmann(SUN))


def test_stefan_boltzmann_rejects_bad_temperature():
    with pytest.raises(ValueError):
        p.stefan_boltzmann(-1.0)


# --------------------------------------------------------------------------
# spectrum
# --------------------------------------------------------------------------
def test_spectrum_shape_and_endpoints():
    pts = p.spectrum(SUN, 300.0, 1100.0, samples=200)
    assert len(pts) == 200
    assert pts[0][0] == 300.0
    assert math.isclose(pts[-1][0], 1100.0)
    assert all(r >= 0.0 for _, r in pts)


def test_spectrum_normalize_peak_is_one():
    pts = p.spectrum(SUN, 300.0, 1100.0, samples=200, normalize=True)
    assert math.isclose(max(r for _, r in pts), 1.0)


def test_spectrum_rejects_too_few_samples():
    with pytest.raises(ValueError):
        p.spectrum(SUN, samples=1)


def test_spectrum_rejects_inverted_band():
    with pytest.raises(ValueError):
        p.spectrum(SUN, lo_nm=900.0, hi_nm=400.0)


def test_spectrum_rejects_bad_temperature():
    with pytest.raises(ValueError):
        p.spectrum(0.0)
