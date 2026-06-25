"""Harvard spectral classification and the perceptual color names. Both are
threshold tables, so the tests walk the boundaries."""

import pytest

from starhue import classify as cl


# --------------------------------------------------------------------------
# spectral_class
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "t, letter",
    [
        (45000.0, "O"),
        (30000.0, "O"),   # lower edge of O (inclusive)
        (29999.0, "B"),   # just below ⇒ B
        (10000.0, "B"),
        (9999.0, "A"),
        (7500.0, "A"),
        (6000.0, "F"),
        (5772.0, "G"),
        (5200.0, "G"),
        (3700.0, "K"),
        (3699.0, "M"),
        (2500.0, "M"),
        (100.0, "M"),
    ],
)
def test_spectral_class_boundaries(t, letter):
    assert cl.spectral_class(t).letter == letter


def test_spectral_type_is_named_tuple():
    st = cl.spectral_class(5772.0)
    assert st.letter == "G"
    assert st.description == "Sun-like"
    assert tuple(st) == ("G", "Sun-like")


def test_every_class_has_a_description():
    for _, letter, desc in cl.MK_CLASSES:
        assert desc and isinstance(desc, str)


# --------------------------------------------------------------------------
# appearance_name
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "t, name",
    [
        (1000.0, "ember red"),
        (1299.0, "ember red"),
        (1300.0, "orange-red"),   # boundary is exclusive on the low side
        (2000.0, "deep orange"),
        (5772.0, "neutral white"),
        (7000.0, "cool white"),
        (12000.0, "icy blue"),
        (50000.0, "icy blue"),
    ],
)
def test_appearance_name_boundaries(t, name):
    assert cl.appearance_name(t) == name


def test_appearance_progression_is_a_real_name():
    # Spot-check that names are non-empty across the whole range.
    for t in range(1000, 40000, 2500):
        assert cl.appearance_name(float(t)).strip()
