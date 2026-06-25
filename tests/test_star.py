"""The Star facade. It owns no physics — every property must agree with the
module it delegates to, so the tests check the wiring."""

import pytest

from starhue import cct, classify, color, physics
from starhue.star import Star

SUN = 5772.0


def test_init_stores_temperature_as_float():
    s = Star(5772)
    assert s.temperature == 5772.0
    assert isinstance(s.temperature, float)


@pytest.mark.parametrize("bad", [0.0, -10.0, float("inf"), float("nan")])
def test_init_rejects_bad_temperature(bad):
    with pytest.raises(ValueError):
        Star(bad)


def test_uses_slots_no_instance_dict():
    s = Star(SUN)
    assert not hasattr(s, "__dict__")
    with pytest.raises(AttributeError):
        s.surprise = 1  # type: ignore[attr-defined]


# --------------------------------------------------------------------------
# color properties delegate to color.temperature_to_color
# --------------------------------------------------------------------------
def test_hex_property():
    assert Star(SUN).hex == "#fff1ea"


def test_rgb_property():
    assert Star(SUN).rgb == (255, 241, 234)


def test_rgb_matches_color_module():
    s = Star(SUN)
    assert s.rgb == color.temperature_to_color(SUN, "rgb")


# --------------------------------------------------------------------------
# physics properties delegate
# --------------------------------------------------------------------------
def test_peak_wavelength_delegates():
    assert Star(SUN).peak_wavelength_nm == physics.wien_peak_wavelength(SUN)


def test_peak_frequency_delegates():
    assert Star(SUN).peak_frequency_hz == physics.wien_peak_frequency(SUN)


def test_radiant_exitance_delegates():
    assert Star(SUN).radiant_exitance == physics.stefan_boltzmann(SUN)


def test_planck_method_delegates():
    assert Star(SUN).planck(500.0) == physics.planck_nm(500.0, SUN)


def test_spectrum_method_delegates():
    s = Star(SUN)
    assert s.spectrum(400.0, 700.0, 50) == physics.spectrum(SUN, 400.0, 700.0, 50)


# --------------------------------------------------------------------------
# classification properties delegate
# --------------------------------------------------------------------------
def test_spectral_type_delegates():
    assert Star(SUN).spectral_type == classify.spectral_class(SUN)
    assert Star(SUN).spectral_type.letter == "G"


def test_appearance_delegates():
    assert Star(SUN).appearance == classify.appearance_name(SUN)
    assert Star(SUN).appearance == "neutral white"


# --------------------------------------------------------------------------
# inverse constructor
# --------------------------------------------------------------------------
def test_from_color_hex_matches_cct():
    s = Star.from_color("#fff1ea")
    assert s.temperature == pytest.approx(cct.color_to_temperature("#fff1ea"))
    assert s.temperature == pytest.approx(SUN, rel=0.01)


def test_from_color_rgb_tuple():
    s = Star.from_color((255, 241, 234))
    assert s.temperature == pytest.approx(SUN, rel=0.01)


# --------------------------------------------------------------------------
# repr
# --------------------------------------------------------------------------
def test_repr_is_informative():
    assert repr(Star(SUN)) == "Star(5772 K, #fff1ea, class G)"
