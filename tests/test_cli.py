"""CLI internals driven in-process: argument validation, color parsing and the
main() dispatch over stdout/stderr and exit codes."""

import pytest

from starhue import cli

ESC = "\x1b"


# --------------------------------------------------------------------------
# _validate_temps
# --------------------------------------------------------------------------
def test_validate_temps_accepts_positive():
    cli._validate_temps([1.0, 5772.0, 30000.0])  # no raise


@pytest.mark.parametrize("bad", [[0.0], [-1.0], [5772.0, -3.0]])
def test_validate_temps_rejects_nonpositive(bad):
    with pytest.raises(SystemExit):
        cli._validate_temps(bad)


# --------------------------------------------------------------------------
# _parse_color
# --------------------------------------------------------------------------
def test_parse_color_hex():
    assert cli._parse_color("#ffd1a3") == (255, 209, 163)
    assert cli._parse_color("#fff") == (255, 255, 255)


def test_parse_color_rgb_triple():
    assert cli._parse_color("255,209,163") == (255, 209, 163)


def test_parse_color_rgb_clamps_out_of_range():
    assert cli._parse_color("300,-5,0") == (255, 0, 0)


@pytest.mark.parametrize("bad", ["1,2", "1,2,3,4", "x,y,z", "not-a-color", "#12"])
def test_parse_color_invalid_exits(bad):
    with pytest.raises(SystemExit):
        cli._parse_color(bad)


# --------------------------------------------------------------------------
# main — forward mode
# --------------------------------------------------------------------------
def test_main_single_temperature(capsys):
    assert cli.main(["5772"]) == 0
    out = capsys.readouterr().out
    assert "5772 K" in out and "class G" in out


def test_main_defaults_to_the_sun(capsys):
    assert cli.main([]) == 0
    assert "5772 K" in capsys.readouterr().out


def test_main_multiple_temperatures_renders_each(capsys):
    assert cli.main(["3000", "5772", "9940"]) == 0
    out = capsys.readouterr().out
    assert out.count("╭") == 3   # three boxed cards
    assert "3000 K" in out and "9940 K" in out


def test_main_no_spectrum_hides_axis(capsys):
    cli.main(["--no-spectrum", "5772"])
    assert "1100nm" not in capsys.readouterr().out


def test_main_no_color_has_no_ansi(capsys):
    cli.main(["--no-color", "5772"])
    assert ESC not in capsys.readouterr().out


def test_main_force_color_emits_ansi(capsys):
    cli.main(["--color", "5772"])
    assert ESC in capsys.readouterr().out


def test_main_rejects_nonpositive_temperature():
    with pytest.raises(SystemExit):
        cli.main(["0"])


# --------------------------------------------------------------------------
# main — inverse mode
# --------------------------------------------------------------------------
def test_main_from_color_reports_on_stderr(capsys):
    assert cli.main(["--from-color", "#ffd1a3"]) == 0
    captured = capsys.readouterr()
    assert "nearest blackbody" in captured.err
    assert "╭" in captured.out  # still renders a card on stdout


def test_main_from_color_invalid_exits(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--from-color", "totally-not-a-color"])


# --------------------------------------------------------------------------
# --version
# --------------------------------------------------------------------------
def test_version_flag_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "starhue" in capsys.readouterr().out
