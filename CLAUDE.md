# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`starhue` converts a blackbody temperature (kelvin) into the true sRGB colour a
star of that temperature shows the eye, plus the physics behind it (Planck
spectrum, Wien peak, Stefan–Boltzmann exitance, Harvard spectral class). It also
runs in reverse — colour → correlated colour temperature (CCT) — and applies
relativistic Doppler shifts.

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
`argparse`, `json`, `os`, `sys`, `typing`). No `pyproject.toml`/`setup.py`, no
test suite, no linter config. Verify changes by running the CLI and the
doctests/examples in the README.

## Common commands

```bash
# Run the CLI (from the parent directory)
python -m starhue 5772                  # a card for the Sun
python -m starhue --range 1000 12000    # gradient strip across the locus
python -m starhue 5772 --svg sun.svg    # write a showcase SVG
python -m starhue --from-color '#ffd1a3'  # inverse: colour → temperature
python -m starhue 5772 --beta 0.3       # Doppler-shifted (receding at 0.3c)

# Smoke-test the public API (no test framework is installed)
python -c "import starhue; print(starhue.temperature_to_hex(5772))"  # -> #fff1ea

# Regenerate the gallery assets in assets/ after changing render/svg/color
python -m starhue 5772  --svg assets/sun.svg
python -m starhue 3500  --svg assets/betelgeuse.svg
python -m starhue 12100 --svg assets/rigel.svg
```

## Architecture & data flow

The forward pipeline (temperature → colour) is a one-way dependency chain;
respect its layering when editing:

```
constants  →  physics  →  color  →  cct       (cct inverts color/physics)
                  ↓          ↓
              classify    render / svg / cli   (presentation only)
                  ↘        ↙
                    star   (the high-level facade tying it all together)
```

- **`constants.py`** — exact 2019-SI / CODATA physical constants. Single source
  of truth; everything else derives from these (no magic numbers downstream).
- **`physics.py`** — Planck's law (`planck`/`planck_nm`), Wien peak
  (wavelength + frequency forms), Stefan–Boltzmann, spectrum sampling, and the
  relativistic Doppler temperature shift. A Doppler shift is modelled as *just
  another blackbody temperature*, which is why `Star.doppler_shifted` returns a
  plain `Star`.
- **`color.py`** — the colorimetry pipeline: sample Planck across the visible
  band → integrate against CIE 1931 colour-matching functions → XYZ → linear
  sRGB (D65) → gamut-clamp → luminance-normalise → gamma-encode. The CMFs use
  the **Wyman–Sloan–Shirley (2013)** analytic Gaussian fit, so there is **no
  embedded CIE data table** — keep it that way.
- **`cct.py`** — the inverse: colour → nearest point on the Planckian locus in
  CIE 1960 *uv*, returning a `CCTResult(temperature_k, duv)`. It round-trips
  with the forward model, so changes to `color.py` chromaticity output must keep
  `cct` consistent.
- **`classify.py`** — Harvard spectral class (O/B/A/F/G/K/M) and perceptual
  colour names from temperature.
- **`star.py`** — `Star`, the high-level facade. It owns no physics; every
  property delegates to the modules above. Inverse constructors
  (`from_hex`/`from_rgb`/`from_color`) go through `cct`; `to_dict()` is the
  JSON shape the CLI emits. New user-facing capabilities should usually surface
  here.
- **`render.py` / `svg.py` / `cli.py`** — presentation only (terminal cards +
  sparkline, dependency-free SVG export, argparse front-end). They consume
  `Star`; no science lives here. Colour output honours `NO_COLOR` /
  `FORCE_COLOR`.

The public API surface is defined explicitly by `__all__` in `__init__.py` — when
adding an exported function, register it there (and in the relevant module's
`__all__`) or it won't be part of the package API.
