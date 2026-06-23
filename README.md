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
python -m starhue --from-color '#ffd1a3'   # inverse: a colour → its nearest blackbody
python -m starhue 5772 --no-spectrum       # card without the sparkline
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

## Full API reference

These are the functions and objects you call. They're re-exported onto the
top-level `starhue` namespace, so `import starhue` is enough to reach all of
them; the table notes which submodule each lives in if you'd rather import from
there.

### Forward — temperature → colour

| Name | Signature → returns | Description |
|---|---|---|
| `temperature_to_hex` | `(temperature_k, step_nm=1.0) → str` | Temperature → `#rrggbb` sRGB hex string. |
| `temperature_to_rgb` | `(temperature_k, step_nm=1.0) → (int, int, int)` | Temperature → display sRGB `(r, g, b)`, 0–255. |
| `temperature_to_rgb01` | `(temperature_k, step_nm=1.0) → (float, float, float)` | Temperature → display sRGB, three floats in `[0, 1]`. |
| `temperature_to_xy` | `(temperature_k, step_nm=1.0) → (float, float)` | Temperature → CIE 1931 chromaticity `(x, y)`. |
| `temperature_to_xyz` | `(temperature_k, step_nm=1.0) → (float, float, float)` | Temperature → CIE 1931 XYZ tristimulus values. |
| `wavelength_to_rgb` | `(wavelength_nm) → (int, int, int)` | Display colour of a single monochromatic wavelength (for spectrum plots). |

### Inverse — colour → temperature

| Name | Signature → returns | Description |
|---|---|---|
| `cct_from_hex` | `(value) → CCTResult` | Nearest blackbody (+ Duv) for a `#rrggbb` colour. |
| `cct_from_rgb` | `(rgb) → CCTResult` | Nearest blackbody (+ Duv) for an sRGB `(r, g, b)` 0–255 colour. |
| `cct_from_xy` | `(x, y) → CCTResult` | Nearest blackbody (+ Duv) for a CIE 1931 `(x, y)` colour. |
| `cct_from_uv` | `(u, v) → CCTResult` | Nearest blackbody (+ Duv) for a CIE 1960 `(u, v)` colour. |
| `hex_to_rgb` | `(value) → (int, int, int)` | Parse `#rgb`/`#rrggbb` → `(r, g, b)`, 0–255. |
| `rgb_to_xy` | `(rgb) → (float, float)` | sRGB `(r, g, b)` 0–255 → CIE 1931 chromaticity `(x, y)`. |
| `CCTResult` | `NamedTuple(temperature_k, duv)` | What the `cct_from_*` functions return; `duv` is the signed distance from the locus. |

### Physics

| Name | Signature → returns | Description |
|---|---|---|
| `planck` | `(wavelength_m, temperature_k) → float` | Planck spectral radiance, W·sr⁻¹·m⁻³ (wavelength in **metres**). |
| `planck_nm` | `(wavelength_nm, temperature_k) → float` | Planck spectral radiance per nm (wavelength in **nanometres**). |
| `spectrum` | `(temperature_k, lo_nm=300, hi_nm=1100, samples=200, *, normalize=False) → list[(float, float)]` | Sample the Planck curve → `(wavelength_nm, radiance)` pairs. |
| `wien_peak_wavelength` | `(temperature_k) → float` | Wavelength of peak radiance (Wien), **metres**. |
| `wien_peak_wavelength_nm` | `(temperature_k) → float` | Wavelength of peak radiance (Wien), **nm**. |
| `wien_peak_frequency` | `(temperature_k) → float` | Frequency of peak radiance (frequency-form Wien), Hz. |
| `stefan_boltzmann` | `(temperature_k) → float` | Total radiant exitance σT⁴, W·m⁻². |

### Classification

| Name | Signature → returns | Description |
|---|---|---|
| `spectral_class` | `(temperature_k) → SpectralType` | Harvard spectral type (O/B/A/F/G/K/M) for an effective temperature. |
| `appearance_name` | `(temperature_k) → str` | Friendly perceptual colour name, e.g. `"warm amber"` *(in `starhue.classify`)*. |
| `SpectralType` | `NamedTuple(letter, description)` | What `spectral_class` returns. |

### Terminal rendering (`starhue.render`)

| Name | Signature → returns | Description |
|---|---|---|
| `star_card` | `(star, *, color=True, spectrum=True, width=46) → str` | Multi-line "trading card": swatch, stats and spectrum. |
| `spectrum_sparkline` | `(star, width=48, lo_nm=300, hi_nm=1100, *, color=True) → str` | One-line Unicode Planck-curve sparkline, tinted by wavelength. |
| `swatch` | `(rgb, width=6, *, color=True) → str` | A solid colour bar of `width` cells. |
| `supports_color` | `(stream=None) → bool` | Best-effort 24-bit colour detection (honours `NO_COLOR` / `FORCE_COLOR`). |

### The `Star` object (`starhue.Star`)

`Star(temperature_k, *, color_step_nm=1.0)` — the high-level facade. The keyword
`color_step_nm` is the wavelength step (nm) of the colour integration; smaller is
more accurate but slower.

**Inverse constructors** (colour → nearest blackbody):

| Constructor | Signature → returns | Description |
|---|---|---|
| `Star.from_rgb` | `(rgb) → Star` | From an sRGB `(r, g, b)` triple (0–255). |
| `Star.from_hex` | `(value) → Star` | From a `#rrggbb` string. |
| `Star.from_color` | `(color_value) → Star` | From either a hex string or an `(r, g, b)` triple. |

**Attributes, properties & methods:**

| Member | Kind | Type / returns | Description |
|---|---|---|---|
| `temperature` | attribute | `float` | The star's temperature, K. |
| `rgb` | property | `(int, int, int)` | Display sRGB colour, 0–255. |
| `rgb01` | property | `(float, float, float)` | Display sRGB colour, floats in `[0, 1]`. |
| `hex` | property | `str` | Display sRGB colour as `#rrggbb`. |
| `xyz` | property | `(float, float, float)` | CIE 1931 XYZ tristimulus values. |
| `chromaticity` | property | `(float, float)` | CIE 1931 chromaticity `(x, y)`. |
| `peak_wavelength_nm` | property | `float` | Wien peak wavelength, nm. |
| `peak_frequency_hz` | property | `float` | Wien peak frequency (frequency form), Hz. |
| `radiant_exitance` | property | `float` | Stefan–Boltzmann exitance, W·m⁻². |
| `spectral_type` | property | `SpectralType` | Harvard spectral classification. |
| `appearance` | property | `str` | Friendly perceptual colour name, e.g. `"neutral white"`. |
| `planck(wavelength_nm)` | method | `float` | Spectral radiance at a wavelength in nm. |
| `spectrum(lo_nm=300, hi_nm=1100, samples=200, *, normalize=False)` | method | `list[(float, float)]` | Sample the Planck curve → `(wavelength_nm, radiance)` pairs. |

Anything not listed here (the colorimetry conversion steps in `starhue.color`,
the physical constants in `starhue.constants`) is internal plumbing the functions
above build on — usable, but not the intended surface.

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

## CLI reference

```
starhue [TEMPERATURES ...] [options]

positional:
  TEMPERATURES        one or more temperatures in kelvin (default: 5772, the Sun)

options:
  --no-spectrum       hide the spectrum sparkline in cards
  --from-color COLOR  inverse mode: a colour (#rrggbb or r,g,b) → its nearest blackbody
  --color / --no-color   force or disable ANSI colour (auto-detected by default)
  --version
```

```bash
starhue --from-color '#ffd1a3'   # what temperature is this colour?
```

Colour output honours the `NO_COLOR` and `FORCE_COLOR` conventions.

## Module map

| module | role |
|---|---|
| `constants` | exact SI / CODATA physical constants |
| `physics` | Planck's law, Wien's law, Stefan–Boltzmann, spectrum sampling |
| `color` | CIE 1931 CMF → XYZ → sRGB; chromaticity; wavelength → display colour |
| `cct` | inverse direction: colour → correlated colour temperature + Duv |
| `classify` | Harvard spectral class + perceptual colour names |
| `star` | the high-level `Star` object |
| `render` | terminal card + spectrum sparkline |
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
