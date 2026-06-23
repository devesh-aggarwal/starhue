"""Command-line interface for starhue.

    starhue 5772                      # one star card
    starhue 3000 5772 9940           # several cards
    starhue --from-color '#ffd1a3'   # inverse: a colour → its nearest blackbody
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from . import __version__
from .cct import cct_from_rgb
from .color import hex_to_rgb
from .render import star_card, supports_color
from .star import Star


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="starhue",
        description="Temperature → true star colour + Planck spectrum.",
        epilog="Give a temperature in kelvin (e.g. 5772 for the Sun) and see its real colour.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("temperatures", nargs="*", type=float, help="one or more temperatures in kelvin")
    p.add_argument(
        "--no-spectrum", dest="spectrum", action="store_false", help="hide the spectrum sparkline"
    )
    p.add_argument(
        "--from-color",
        metavar="COLOR",
        help="inverse mode: a colour (#rrggbb or r,g,b) → its nearest blackbody",
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

    # --- inverse mode: a colour → its nearest blackbody --------------------
    if args.from_color:
        rgb = _parse_color(args.from_color)
        result = cct_from_rgb(rgb)
        print(
            f"# {args.from_color.strip()} → nearest blackbody {result.temperature_k:.0f} K"
            f" (Duv {result.duv:+.4f})",
            file=sys.stderr,
        )
        temps: List[float] = [result.temperature_k]
    else:
        temps = args.temperatures or [5772.0]  # default: show the Sun
        _validate_temps(temps)

    for i, t in enumerate(temps):
        if i:
            print()
        print(star_card(Star(t), color=use_color, spectrum=args.spectrum))

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
