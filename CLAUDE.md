# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`starhue` converts a blackbody temperature (kelvin) into the true sRGB color a
star of that temperature shows the eye, plus the physics behind it (Planck
spectrum, Wien peak, Stefan–Boltzmann exitance, Harvard spectral class). It also
runs in reverse — color → correlated color temperature (CCT).

## Key structural fact

**This repository directory *is* the `starhue` package** — the parent folder is
named `starhue`, and the modules (`physics.py`, `color.py`, etc.) sit at the
repo root, not in a subpackage. Imports between them are relative (`from . import
color`), so the package is always run/imported by its parent-directory name:

```bash
cd ..                      # to the directory that *contains* this repo
python -m starhue 5772
```

The `starhue/` *subdirectory* is a gitignored Python virtualenv (note the
`/starhue` line in `.gitignore`) — **not** source code. Ignore it.

There are **no third-party dependencies** — pure standard library (`math`,
`argparse`, `os`, `sys`, `typing`). No `pyproject.toml`/`setup.py`, no
test suite, no linter config. Verify changes by running the CLI and the
doctests/examples in the README.

This is a deliberately **basic** package: the surface is forward color
(temperature → sRGB), inverse CCT (color → temperature), and the terminal star
card. SVG export, gradient strips, JSON output, and Doppler shifting were
removed to keep it simple — they may be re-added later.

## Common commands

```bash
# Run the CLI (from the parent directory)
python -m starhue 5772                    # a card for the Sun
python -m starhue 3000 5772 9940          # several cards at once
python -m starhue --from-color '#ffd1a3'  # inverse: color → temperature
python -m starhue 5772 --no-spectrum      # card without the sparkline

# Smoke-test the public API (no test framework is installed)
python -c "import starhue; print(starhue.temperature_to_color(5772))"  # -> #fff1ea
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
  (wavelength + frequency forms), Stefan–Boltzmann, and spectrum sampling.
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
  color names from temperature.
- **`star.py`** — `Star`, the high-level facade. It owns no physics; every
  property delegates to the modules above. Inverse constructors
  (`from_hex`/`from_rgb`/`from_color`) go through `cct`. New user-facing
  capabilities should usually surface here.
- **`render.py` / `cli.py`** — presentation only (terminal card + spectrum
  sparkline, argparse front-end). They consume `Star`; no science lives here.
  Color output honours `NO_COLOR` / `FORCE_COLOR`.

The public API surface is defined explicitly by `__all__` in `__init__.py` — when
adding an exported function, register it there (and in the relevant module's
`__all__`) or it won't be part of the package API.
