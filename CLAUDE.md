# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`starhue` converts a blackbody temperature (kelvin) into the true sRGB color a
star of that temperature shows the eye, plus the physics behind it (Planck
spectrum, Wien peak, Stefan–Boltzmann exitance, Harvard spectral class). It also
runs in reverse — color → correlated color temperature (CCT) — and can plot the
Planck curve.

## Key structural fact

This is a **standard installable package**: the repo root holds packaging files
(`pyproject.toml`, `requirements.txt`) and the source lives in the `starhue/`
*subdirectory* (`physics.py`, `color.py`, etc.). Imports between modules are
relative (`from . import color`), so run the package by its import name from
anywhere:

```bash
python -m starhue 5772
```

Install it editable into a virtualenv for development (the `.venv/` directory is
the project's virtualenv):

```bash
python -m pip install -e .            # core only
python -m pip install -e '.[plot]'    # + matplotlib, for Star.spectrum() plots
python -m pip install -e '.[test]'    # + pytest (and matplotlib) to run the suite
```

The core has **no third-party runtime dependencies** — pure standard library
(`math`, `argparse`, `os`, `sys`, `typing`). `requirements.txt` is intentionally
empty of packages; `pyproject.toml` declares `dependencies = []`. The **one
optional exception** is `Star.spectrum()`, which renders a matplotlib figure; it
lives behind the `plot` extra and lazily imports matplotlib *inside* the method
(raising a friendly `ModuleNotFoundError` if it's missing), so everything else
stays zero-dependency. Keep it that way: do not add a top-level matplotlib import
or any new runtime dependency.

There is **no `[project.scripts]` entry point**, so the CLI is invoked as
`python -m starhue`, not a bare `starhue` command.

`starhue.egg-info/` is generated build metadata from the editable install — not
source; safe to delete (regenerated on the next install).

## Common commands

```bash
# Run the CLI
python -m starhue 5772                    # a card for the Sun
python -m starhue 3000 5772 9940          # several cards at once
python -m starhue --from-color '#ffd1a3'  # inverse: color → temperature
python -m starhue 5772 --no-spectrum      # card without the sparkline

# Smoke-test the public API
python -c "import starhue; print(starhue.temperature_to_color(5772))"  # -> #fff1ea

# Run the tests (needs the test extra installed)
python -m pytest                          # picks up testpaths=["tests"] from pyproject
python -m pytest -v tests/test_physics.py # a single module

# Build the docs (needs docs/requirements.txt installed)
sphinx-build -b html docs/source docs/build
```

## Architecture & data flow

The forward pipeline (temperature → color) is a one-way dependency chain;
respect its layering when editing:

```
constants  →  physics  →  color  →  cct       (cct inverts color/physics)
                  ↓          ↓
              classify    render / cli         (presentation only)
                  ↘        ↙
                    star   (the high-level facade tying it all together)
```

- **`constants.py`** — exact 2019-SI / CODATA physical constants. Single source
  of truth; everything else derives from these (no magic numbers downstream).
- **`physics.py`** — Planck's law (`planck`/`planck_nm`), Wien peak
  (wavelength + frequency forms), Stefan–Boltzmann, and `spectrum` (the band
  sampler returning `(wavelength_nm, radiance)` pairs).
- **`color.py`** — the colorimetry pipeline: sample Planck across the visible
  band → integrate against CIE 1931 color-matching functions → XYZ → linear
  sRGB (D65) → gamut-clamp → luminance-normalize → gamma-encode. The CMFs use
  the **Wyman–Sloan–Shirley (2013)** analytic Gaussian fit, so there is **no
  embedded CIE data table** — keep it that way.
- **`cct.py`** — the inverse: `color_to_temperature` finds the nearest point on
  the Planckian locus in CIE 1960 *uv* and returns that temperature (K). It
  round-trips with the forward model, so changes to `color.py` chromaticity
  output must keep `cct` consistent.
- **`classify.py`** — Harvard spectral class (O/B/A/F/G/K/M) and perceptual
  color names (`appearance_name`) from temperature.
- **`star.py`** — `Star`, the high-level facade. It owns no physics; every
  property delegates to the modules above. Inverse constructors
  (`from_hex`/`from_rgb`/`from_color`) go through `cct`. `Star.spectrum()` is the
  one presentation-flavoured method: it samples `physics.spectrum` and returns a
  matplotlib `Figure` stroked in the star's own sRGB color (the caller owns and
  closes the figure). New user-facing capabilities should usually surface here.
- **`render.py` / `cli.py`** — presentation only (terminal card + spectrum
  sparkline, argparse front-end). They consume `Star`; no science lives here.
  The sparkline samples `physics.spectrum` directly. Color output honours
  `NO_COLOR` / `FORCE_COLOR`.

The public API surface is defined explicitly by `__all__` in `__init__.py` — when
adding an exported function, register it there (and in the relevant module's
`__all__`) or it won't be part of the package API.

## Conventions

- **Google-style docstrings.** Every public module, class, and function gets a
  docstring with `Args:` / `Returns:` / `Raises:` sections in Google style.
  Sphinx's `napoleon` extension parses these for the docs, so keep the format
  consistent — match the existing docstrings when adding code.
- **Test every piece of functionality.** The `tests/` suite runs under pytest
  and mirrors the source: one `test_<module>.py` per source module
  (`test_physics.py`, `test_color.py`, `test_cct.py`, `test_classify.py`,
  `test_star.py`, `test_render.py`, `test_cli.py`, `test_constants.py`), each
  unit-testing that module against closed-form values and invariants. On top of
  that, `tests/test_e2e.py` spawns the real `python -m starhue` subprocess and
  asserts on its stdout/stderr/exit code — the package exactly as a user runs it.
  When you add or change functionality, add or update the matching unit tests
  (and the e2e tests if you touch the CLI surface), and run `python -m pytest`
  before considering the change done.
- **No linter config** — keep style consistent with surrounding code by hand.

## Docs & CI

- **Docs** live in `docs/` (Sphinx, `autodoc` + `napoleon`, RTD theme) and are
  built on Read the Docs per `.readthedocs.yaml`. The toolchain is pinned in
  `docs/requirements.txt`.
- **CI** is in `.github/workflows/`: `python-app.yml` runs the pytest suite
  across a Python matrix (3.8 → 3.14) on every push and PR; `publish.yml`
  builds and publishes to PyPI via Trusted Publishing (OIDC, no stored token)
  whenever a GitHub Release is published.
- **Versioning** is single-sourced from `__version__` in `starhue/__init__.py`
  (`pyproject.toml` reads it via `[tool.setuptools.dynamic]`). Bump it there.
