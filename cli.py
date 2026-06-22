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


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    use_color = supports_color() if args.color is None else args.color

    # --- gradient strip across a range -------------------------------------
    if args.range is not None:
        t_min, t_max = args.range
        if t_min <= 0 or t_max <= 0:
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

    # --- one or more explicit temperatures ---------------------------------
    temps = args.temperatures or [5772.0]  # default: show the Sun
    _validate_temps(temps)
    stars = [Star(t) for t in temps]

    if args.json:
        payload = stars[0].to_dict() if len(stars) == 1 else [s.to_dict() for s in stars]
        print(json.dumps(payload, indent=2))
    else:
        for i, star in enumerate(stars):
            if i:
                print()
            print(star_card(star, color=use_color, spectrum=args.spectrum))

    if args.svg:
        if len(stars) == 1:
            _emit_svg(args.svg, star_card_svg(stars[0]))
        else:
            lo, hi = min(temps), max(temps)
            _emit_svg(args.svg, gradient_strip_svg(lo, hi, args.steps or 64))

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
