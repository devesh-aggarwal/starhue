"""Command-line interface for starhue.

    starhue 5772                      # one star card
    starhue 3000 5772 9940           # several cards
    starhue --range 1000 12000       # a gradient strip across the locus
    starhue 5772 --svg sun.svg       # write a showcase SVG
    starhue 5772 --json              # machine-readable summary
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Sequence

from . import __version__
from .cct import cct_from_rgb
from .color import hex_to_rgb
from .constants import C
from .physics import beta_from_redshift, redshift_from_beta, relativistic_doppler_temperature
from .render import gradient_strip, star_card, supports_color
from .star import Star
from .svg import gradient_strip_svg, star_card_svg


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="starhue",
        description="Temperature → true star colour + Planck spectrum.",
        epilog="Give a temperature in kelvin (e.g. 5772 for the Sun) and see its real colour.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("temperatures", nargs="*", type=float, help="one or more temperatures in kelvin")
    p.add_argument(
        "--range",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        help="render a gradient strip across this temperature range",
    )
    p.add_argument("--steps", type=int, default=None, help="number of steps in the gradient strip")
    p.add_argument("--svg", metavar="PATH", help="write an SVG (card for one temp, strip for many)")
    p.add_argument("--json", action="store_true", help="emit a JSON summary instead of a card")
    p.add_argument(
        "--no-spectrum", dest="spectrum", action="store_false", help="hide the spectrum sparkline"
    )
    p.add_argument(
        "--from-color",
        metavar="COLOR",
        help="inverse mode: a colour (#rrggbb or r,g,b) → its nearest blackbody",
    )
    doppler = p.add_mutually_exclusive_group()
    doppler.add_argument("--beta", type=float, help="Doppler shift: radial velocity as v/c (+ = receding)")
    doppler.add_argument("--velocity-kms", type=float, help="Doppler shift: radial velocity in km/s")
    doppler.add_argument("--redshift", type=float, help="Doppler shift: redshift z (+ = receding)")
    color = p.add_mutually_exclusive_group()
    color.add_argument("--color", dest="color", action="store_true", default=None, help="force ANSI colour")
    color.add_argument("--no-color", dest="color", action="store_false", help="disable ANSI colour")
    p.add_argument("--version", action="version", version=f"starhue {__version__}")
    return p


def _validate_temps(temps: Sequence[float]) -> None:
    for t in temps:
        if t <= 0:
            raise SystemExit(f"starhue: temperature must be positive, got {t:g}")


def _emit_svg(path: str, markup: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(markup)
    print(f"wrote {path}", file=sys.stderr)


def _resolve_beta(args: argparse.Namespace) -> Optional[float]:
    """Turn whichever Doppler flag was given into a single ``beta = v/c`` (or None)."""
    if args.beta is not None:
        beta = args.beta
    elif args.velocity_kms is not None:
        beta = args.velocity_kms * 1000.0 / C
    elif args.redshift is not None:
        if args.redshift <= -1.0:
            raise SystemExit("starhue: redshift z must be greater than -1")
        beta = beta_from_redshift(args.redshift)
    else:
        return None
    if not -1.0 < beta < 1.0:
        raise SystemExit(f"starhue: speed must be sub-luminal (|v/c| < 1), got beta={beta:+.4f}")
    return beta


def _parse_color(value: str) -> tuple:
    """Parse a CLI colour: ``#rrggbb``/``#rgb`` or ``r,g,b``."""
    s = value.strip()
    if "," in s:
        parts = s.split(",")
        if len(parts) != 3:
            raise SystemExit(f"starhue: expected 'r,g,b', got {value!r}")
        try:
            return tuple(max(0, min(255, int(p))) for p in parts)
        except ValueError:
            raise SystemExit(f"starhue: invalid r,g,b colour {value!r}") from None
    try:
        return hex_to_rgb(s)
    except ValueError as exc:
        raise SystemExit(f"starhue: {exc}") from None


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    use_color = supports_color() if args.color is None else args.color
    beta = _resolve_beta(args)

    def shift(t: float) -> float:
        return relativistic_doppler_temperature(t, beta) if beta is not None else t

    if beta is not None:
        z = redshift_from_beta(beta)
        verb = "receding" if beta > 0 else "approaching"
        print(f"# Doppler: β={beta:+.4f}  z={z:+.4f}  ({verb})", file=sys.stderr)

    if args.from_color and args.range is not None:
        raise SystemExit("starhue: --from-color cannot be combined with --range")

    # --- gradient strip across a range -------------------------------------
    if args.range is not None:
        t_min, t_max = shift(args.range[0]), shift(args.range[1])
        if args.range[0] <= 0 or args.range[1] <= 0:
            raise SystemExit("starhue: --range temperatures must be positive")
        if t_max <= t_min:
            raise SystemExit("starhue: --range MAX must be greater than MIN")
        steps = args.steps or 32
        if args.json:
            stars = [
                Star(t_min + (t_max - t_min) * i / (steps - 1)).to_dict() for i in range(steps)
            ]
            print(json.dumps({"range": [t_min, t_max], "steps": steps, "stars": stars}, indent=2))
        else:
            print(gradient_strip(t_min, t_max, steps, color=use_color))
        if args.svg:
            _emit_svg(args.svg, gradient_strip_svg(t_min, t_max, args.steps or 64))
        return 0

    # --- inverse mode: a colour → its nearest blackbody --------------------
    query_duv: Optional[float] = None
    query_color: Optional[str] = None
    if args.from_color:
        rgb = _parse_color(args.from_color)
        result = cct_from_rgb(rgb)
        query_color, query_duv = args.from_color.strip(), result.duv
        print(
            f"# {query_color} → nearest blackbody {result.temperature_k:.0f} K"
            f" (Duv {result.duv:+.4f})",
            file=sys.stderr,
        )
        rest_temps: List[float] = [result.temperature_k]
    else:
        rest_temps = args.temperatures or [5772.0]  # default: show the Sun
        _validate_temps(rest_temps)

    # (rest temperature, the star as observed after any Doppler shift)
    records = [(t, Star(shift(t))) for t in rest_temps]

    if args.json:
        items = []
        for rest_t, star in records:
            d = star.to_dict()
            if beta is not None:
                d.update(rest_temperature_k=rest_t, beta=beta, redshift=redshift_from_beta(beta))
            if query_color is not None:
                d.update(query_color=query_color, duv=query_duv)
            items.append(d)
        print(json.dumps(items[0] if len(items) == 1 else items, indent=2))
    else:
        for i, (_rest_t, star) in enumerate(records):
            if i:
                print()
            print(star_card(star, color=use_color, spectrum=args.spectrum))

    if args.svg:
        observed = [star.temperature for _t, star in records]
        if len(records) == 1:
            _emit_svg(args.svg, star_card_svg(records[0][1]))
        else:
            _emit_svg(args.svg, gradient_strip_svg(min(observed), max(observed), args.steps or 64))

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
