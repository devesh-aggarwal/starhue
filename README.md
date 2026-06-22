# starhue

**Temperature → the colour of a star, plus its Planck spectrum.**

`starhue` takes a temperature value in kelvin, and returns the actual sRGB colour that a
blackbody of that temperature would show to your eye. 

<p align="center">
  <img src="assets/sun.png" alt="starhue card for the Sun (5772 K)" width="640">
</p>

---

## Quick start

The project folder *is* the `starhue` package, so you can run it straight from
source — from the directory that **contains** `starhue/`:

```bash
python -m starhue 5772            # the Sun
python -m starhue 3500 5772 12100 # several stars at once
python -m starhue --range 1000 12000   # a gradient strip across the locus
python -m starhue 5772 --svg sun.svg   # write a showcase SVG
python -m starhue 3500 --json          # machine-readable summary
```

```text
╭────────────────────────────────────────────────╮
│ ★  5772 K                              class G  │
│ ████████  #fff1ea  rgb(255, 241, 234)          │
│ yellow, Sun-like · neutral white               │
│                                                │
│ peak λ    502.0 nm  ·  3.393e+14 Hz            │
│ exitance  62.94 MW/m²                          │
│ CIE xy    (0.3263, 0.3361)                     │
│                                                │
│ ▄▄▅▆▆▇▇▇██████████▇▇▇▇▇▆▆▆▆▆▅▅▅▅▅▄▄▄▄▄▄▃▃▃▃▃▃▃ │
│            ▲                                    │
│ 300nm                                   1100nm │
╰────────────────────────────────────────────────╯
```

*(In a real terminal the swatch and spectrum sparkline are full 24-bit colour.)*

## Python API

```python
import starhue

# One-liners
starhue.temperature_to_hex(5772)     # '#fff1ea'
starhue.temperature_to_rgb(3500)     # (255, 200, 140)
starhue.temperature_to_xy(6500)      # (0.3134, 0.3239)  ≈ D65

# The high-level object
star = starhue.Star(5772)
star.hex                  # '#fff1ea'
star.rgb                  # (255, 241, 234)
star.chromaticity         # (0.3263, 0.3361)  CIE 1931 (x, y)
star.peak_wavelength_nm   # 502.0     — Wien's displacement law
star.peak_frequency_hz    # 3.39e14   — frequency-form Wien's law
star.radiant_exitance     # 6.29e7 W/m²  — Stefan–Boltzmann
star.spectral_type.letter # 'G'
star.appearance           # 'neutral white'
star.to_dict()            # everything, JSON-ready

# The raw spectrum: list of (wavelength_nm, radiance)
star.spectrum(380, 750, samples=100, normalize=True)
```

### Inverse: colour → temperature (CCT)

Go the other way too. The correlated colour temperature is the nearest point on
the Planckian locus in CIE 1960 *uv* space, so it round-trips with the forward
model. You also get **Duv** — the signed distance from the locus (≈0 means the
colour really is blackbody-like; + is the green side, − the pink side).

```python
starhue.cct_from_hex('#ffd1a3')   # CCTResult(temperature_k=3911.0, duv=-0.0012)
starhue.cct_from_rgb((205, 217, 255)).temperature_k   # ~10000

starhue.Star.from_hex('#fff1ea')  # Star(5773 K, #fff1ea, class G)
starhue.Star.from_color((255, 200, 140))
```

### Doppler shift

A relativistically Doppler-shifted blackbody is *still* a blackbody at a shifted
temperature, so motion just gives you another `Star`. Positive velocity =
receding (redshift, cooler & redder); negative = approaching (bluer).

```python
sun = starhue.Star(5772)
sun.doppler_shifted(beta=0.3)         # Star(4235 K, …)  — receding at 0.3c
sun.doppler_shifted(velocity_kms=-500)
sun.doppler_shifted(redshift=1.0).temperature   # 2886.0  (= T / (1+z))

starhue.relativistic_doppler_temperature(5772, 0.3)   # 4235.5
```

Lower-level physics and colour functions live in `starhue.physics` and
`starhue.color`:

```python
from starhue.physics import planck, wien_peak_wavelength, stefan_boltzmann
from starhue.color import temperature_to_rgb, wavelength_to_rgb, cie_1931_xyz
from starhue.cct import cct_from_xy, cct_from_uv
```

## The science

Everything is computed from first principles with the exact 2019-SI constants.

**Planck's law** — spectral radiance of a blackbody:

$$B_\lambda(T) = \frac{2hc^2}{\lambda^5}\,\frac{1}{\exp\!\left(\dfrac{hc}{\lambda k_B T}\right) - 1}$$

**Wien's displacement law** — where that curve peaks: $\lambda_\text{max} = b / T$.

**Stefan–Boltzmann law** — total power radiated per unit area: $j^\star = \sigma T^4$.

**Temperature → colour** follows the standard colorimetry pipeline:

1. Sample the Planck curve across the visible band (360–830 nm).
2. Integrate against the **CIE 1931 2° colour-matching functions** → CIE *XYZ*.
3. Map *XYZ* → linear sRGB with the D65 matrix.
4. Clamp out-of-gamut negatives, normalise to constant luminance, gamma-encode.

The colour-matching functions use the analytic multi-lobe Gaussian fit of
**Wyman, Sloan & Shirley (2013)**, which reproduces the tabulated CIE curves to
within ~1% with no embedded data table.

### Is it accurate?

Yes — it lands on the textbook reference points:

| Temperature | `starhue` | meaning |
|------------:|:----------|:--------|
| 6500 K | xy ≈ (0.313, 0.324) | essentially the **D65** white point |
| 5772 K | `#fff1ea` | the Sun — a warm white, *not* yellow |
| 3500 K | `#ffc88c` | amber (an M-type red giant) |
| 12000 K | bluish white | hot B-type star |

The full Planckian locus matches Mitchell Charity's well-known blackbody-colour
table closely.

## Gallery

A cool red giant — note the spectral peak sliding into the infrared:

<p align="center">
  <img src="assets/betelgeuse.png" alt="3500 K M-type star" width="560">
</p>

A hot blue star, peak pushed into the ultraviolet:

<p align="center">
  <img src="assets/rigel.png" alt="12100 K B-type star" width="560">
</p>

The blackbody locus from ember-red to icy blue:

<p align="center">
  <img src="assets/gradient.png" alt="blackbody colour gradient 1000–15000 K" width="800">
</p>

## CLI reference

```
starhue [TEMPERATURES ...] [options]

positional:
  TEMPERATURES        one or more temperatures in kelvin (default: 5772, the Sun)

options:
  --range MIN MAX     render a gradient strip across this temperature range
  --steps N           number of steps in the gradient strip
  --svg PATH          write an SVG (a card for one temp, a strip for many)
  --json              emit a JSON summary instead of a card
  --no-spectrum       hide the spectrum sparkline in cards
  --from-color COLOR  inverse mode: a colour (#rrggbb or r,g,b) → its nearest blackbody
  --beta B            Doppler shift by radial velocity v/c (+ = receding)
  --velocity-kms V    Doppler shift by radial velocity in km/s
  --redshift Z        Doppler shift by redshift z
  --color / --no-color   force or disable ANSI colour (auto-detected by default)
  --version
```

```bash
starhue --from-color '#ffd1a3'   # what temperature is this colour?
starhue 5772 --beta 0.3          # the Sun receding at 0.3c
starhue --range 1000 12000 --redshift 0.5   # a redshifted gradient
```

Colour output honours the `NO_COLOR` and `FORCE_COLOR` conventions.

## Module map

| module | role |
|---|---|
| `constants` | exact SI / CODATA physical constants |
| `physics` | Planck's law, Wien's law, Stefan–Boltzmann, Doppler shift, spectrum sampling |
| `color` | CIE 1931 CMF → XYZ → sRGB; chromaticity; wavelength → display colour |
| `cct` | inverse direction: colour → correlated colour temperature + Duv |
| `classify` | Harvard spectral class + perceptual colour names |
| `star` | the high-level `Star` object |
| `render` | terminal cards, spectrum sparkline, gradient strip |
| `svg` | dependency-free showcase SVG export |
| `cli` | the command-line interface |

## References

- M. Planck, *On the Law of Distribution of Energy in the Normal Spectrum* (1901).
- CIE 1931 2° standard colorimetric observer.
- C. Wyman, P. Sloan & P. Shirley, *Simple Analytic Approximations to the CIE
  XYZ Color Matching Functions*, **JCGT** 2(2), 2013.
- IEC 61966-2-1:1999 (sRGB).
- M. Charity, *What color is a blackbody?* — reference colour table.

## License

_To be decided by the project owner._
