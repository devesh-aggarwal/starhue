"""The colorimetry pipeline: Planck → CIE XYZ → sRGB, plus the inverse
chromaticity helpers and hex parsing."""

import math
import re

import pytest

from starhue import color as c

HEX_RE = re.compile(r"^#[0-9a-f]{6}$")
SUN = 5772.0


# --------------------------------------------------------------------------
# temperature_to_color
# --------------------------------------------------------------------------
def test_sun_color_anchor_hex():
    assert c.temperature_to_color(SUN) == "#fff1ea"


def test_sun_color_anchor_rgb():
    assert c.temperature_to_color(SUN, "rgb") == (255, 241, 234)


def test_color_hex_format_is_well_formed():
    for t in (2000.0, 3500.0, SUN, 12000.0, 30000.0):
        assert HEX_RE.match(c.temperature_to_color(t))


def test_hotter_stars_are_bluer_cooler_stars_redder():
    cool = c.temperature_to_color(3000.0, "rgb")
    hot = c.temperature_to_color(9940.0, "rgb")
    assert cool[0] >= cool[2]      # a 3000 K star leans red
    assert hot[2] >= hot[0]        # a 9940 K star leans blue
    assert hot[2] > cool[2]        # and is bluer than the cool one


def test_normalized_to_full_brightness():
    # Luminance-normalized: the brightest channel is pinned at 255.
    assert max(c.temperature_to_color(SUN, "rgb")) == 255


def test_color_rejects_bad_format():
    with pytest.raises(ValueError):
        c.temperature_to_color(SUN, "cmyk")


def test_color_step_nm_affects_accuracy_only_slightly():
    fine = c.temperature_to_color(SUN, "rgb", 1.0)
    coarse = c.temperature_to_color(SUN, "rgb", 5.0)
    assert all(abs(a - b) <= 4 for a, b in zip(fine, coarse))


# --------------------------------------------------------------------------
# wavelength_to_color
# --------------------------------------------------------------------------
def test_wavelength_color_hex_format():
    assert HEX_RE.match(c.wavelength_to_color(530.0))


def test_wavelength_color_green_midband():
    r, g, b = c.wavelength_to_color(530.0, "rgb")
    assert g > r and g > b           # 530 nm reads green


def test_wavelength_color_fades_to_black_outside_eye():
    assert c.wavelength_to_color(250.0) == "#000000"     # deep UV
    assert c.wavelength_to_color(1100.0) == "#000000"    # far IR


def test_wavelength_color_rejects_bad_format():
    with pytest.raises(ValueError):
        c.wavelength_to_color(530.0, "hsl")


# --------------------------------------------------------------------------
# hex_to_rgb
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value, expected",
    [
        ("#ffd1a3", (255, 209, 163)),
        ("ffd1a3", (255, 209, 163)),
        ("#fff", (255, 255, 255)),
        ("000", (0, 0, 0)),
        ("  #FFD1A3  ", (255, 209, 163)),  # stripped + case-insensitive
    ],
)
def test_hex_to_rgb_valid(value, expected):
    assert c.hex_to_rgb(value) == expected


@pytest.mark.parametrize("bad", ["", "#12", "#12345", "gggggg", "#xyzxyz", "12345678"])
def test_hex_to_rgb_invalid(bad):
    with pytest.raises(ValueError):
        c.hex_to_rgb(bad)


# --------------------------------------------------------------------------
# CIE building blocks
# --------------------------------------------------------------------------
def test_cie_1931_xyz_returns_triple():
    xyz = c.cie_1931_xyz(550.0)
    assert len(xyz) == 3
    assert all(v >= 0.0 for v in xyz)


def test_spectrum_to_xyz_positive():
    x, y, z = c.spectrum_to_xyz(SUN)
    assert x > 0 and y > 0 and z > 0


def test_spectrum_to_xyz_rejects_nonpositive_step():
    with pytest.raises(ValueError):
        c.spectrum_to_xyz(SUN, step_nm=0.0)


def test_xyz_to_xy_normalizes():
    x, y = c.xyz_to_xy(0.4, 0.4, 0.2)
    assert math.isclose(x, 0.4) and math.isclose(y, 0.4)


def test_xyz_to_xy_degenerate_is_origin():
    assert c.xyz_to_xy(0.0, 0.0, 0.0) == (0.0, 0.0)


def test_xy_to_uv_degenerate_is_origin():
    # denominator -2x + 12y + 3 == 0
    assert c.xy_to_uv(1.5, 0.0) == (0.0, 0.0)


def test_rgb_to_xy_in_unit_simplex():
    x, y = c.rgb_to_xy((255, 241, 234))
    assert 0.0 < x < 1.0 and 0.0 < y < 1.0


def test_srgb_xyz_roundtrip_white():
    # Pure white in, near-D65 white XYZ, and back to ~white. The forward/inverse
    # matrices are independently-rounded published constants, not exact inverses,
    # so the round-trip closes to ~1e-3 rather than machine epsilon.
    x, y, z = c.srgb_to_xyz(1.0, 1.0, 1.0)
    r, g, b = c.xyz_to_srgb(x, y, z)
    assert math.isclose(r, 1.0, abs_tol=1e-3)
    assert math.isclose(g, 1.0, abs_tol=1e-3)
    assert math.isclose(b, 1.0, abs_tol=1e-3)
