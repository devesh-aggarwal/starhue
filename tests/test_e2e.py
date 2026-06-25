"""End-to-end: spawn the real ``python -m starhue`` process and assert on its
stdout, stderr and exit code — the package exactly as a user runs it."""

import subprocess
import sys

import pytest

ESC = "\x1b"


def run(*args, env=None):
    """Invoke ``python -m starhue`` with ``args`` and capture the result."""
    return subprocess.run(
        [sys.executable, "-m", "starhue", *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_single_temperature_card():
    r = run("5772")
    assert r.returncode == 0
    assert "5772 K" in r.stdout
    assert "#fff1ea" in r.stdout
    assert "class G" in r.stdout


def test_no_args_shows_the_sun():
    r = run()
    assert r.returncode == 0
    assert "5772 K" in r.stdout


def test_several_cards_at_once():
    r = run("3000", "5772", "9940")
    assert r.returncode == 0
    assert r.stdout.count("╭") == 3


def test_no_spectrum_flag():
    r = run("5772", "--no-spectrum")
    assert r.returncode == 0
    assert "1100nm" not in r.stdout       # axis label only present with the sparkline


def test_inverse_from_color():
    r = run("--from-color", "#ffd1a3")
    assert r.returncode == 0
    assert "nearest blackbody" in r.stderr
    assert "╭" in r.stdout


def test_invalid_temperature_exits_nonzero():
    r = run("0")
    assert r.returncode != 0
    assert "must be positive" in r.stderr


def test_invalid_color_exits_nonzero():
    r = run("--from-color", "not-a-color")
    assert r.returncode != 0
    assert "starhue:" in r.stderr


def test_no_color_env_strips_ansi():
    import os

    env = dict(os.environ, NO_COLOR="1", FORCE_COLOR="")
    r = run("5772", env=env)
    assert r.returncode == 0
    assert ESC not in r.stdout


def test_force_color_env_emits_ansi():
    import os

    env = dict(os.environ, FORCE_COLOR="1")
    env.pop("NO_COLOR", None)
    r = run("5772", env=env)
    assert r.returncode == 0
    assert ESC in r.stdout


def test_version_flag():
    r = run("--version")
    assert r.returncode == 0
    assert r.stdout.startswith("starhue ")


def test_help_flag():
    r = run("--help")
    assert r.returncode == 0
    assert "temperature" in r.stdout.lower()


@pytest.mark.parametrize("temp, klass", [("3000", "M"), ("9940", "A"), ("30000", "O")])
def test_spectral_class_in_output(temp, klass):
    r = run(temp)
    assert f"class {klass}" in r.stdout
