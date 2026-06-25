"""Inverse direction: a color → correlated color temperature. The defining
property is that it round-trips with the forward color model."""

import pytest

from starhue import cct
from starhue.color import temperature_to_color


def test_sun_hex_recovers_sun_temperature():
    assert cct.color_to_temperature("#fff1ea") == pytest.approx(5772, rel=0.01)


@pytest.mark.parametrize("t", [2000.0, 3000.0, 5772.0, 9940.0])
def test_forward_inverse_roundtrip(t):
    recovered = cct.color_to_temperature(temperature_to_color(t))
    assert recovered == pytest.approx(t, rel=0.01)


def test_hot_star_roundtrip_looser_tolerance():
    # The locus crowds together at the blue end, so tolerance loosens.
    recovered = cct.color_to_temperature(temperature_to_color(20000.0))
    assert recovered == pytest.approx(20000.0, rel=0.03)


def test_accepts_hex_string_and_rgb_tuple_alike():
    from_hex = cct.color_to_temperature("#fff1ea")
    from_rgb = cct.color_to_temperature((255, 241, 234))
    assert from_hex == from_rgb


def test_result_within_meaningful_range():
    t = cct.color_to_temperature("#fff1ea")
    assert cct.T_MIN <= t <= cct.T_MAX


def test_warmer_color_gives_lower_temperature():
    warm = cct.color_to_temperature(temperature_to_color(3000.0))
    cool = cct.color_to_temperature(temperature_to_color(9000.0))
    assert warm < cool
