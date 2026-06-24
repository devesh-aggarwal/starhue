"""Command-line interface for starhue.

    starhue 5772                      # one star card
    starhue 3000 5772 9940           # several cards
    starhue --from-color '#ffd1a3'   # inverse: a color → its nearest blackbody
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from . import __version__
from .cct import color_to_temperature
from .color import hex_to_rgb
from .render import star_card, supports_color
from .star import Star


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for the CLI.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    p = argparse.ArgumentParser(
        prog="starhue",
        description="Temperature → true star color + Planck spectrum.",
        epilog="Give a temperature in kelvin (e.g. 5772 for the Sun) and see its real color.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("temperatures", nargs="*", type=float, help="one or more temperatures in kelvin")
    p.add_argument(
        "--no-spectrum", dest="spectrum", action="store_false", help="hide the spectrum sparkline"
    )
    p.add_argument(
        "--from-color",
        metavar="COLOR",
        help="inverse mode: a color (#rrggbb or r,g,b) → its nearest blackbody",
    )
    color = p.add_mutually_exclusive_group()
    color.add_argument("--color", dest="color", action="store_true", default=None, help="force ANSI color")
    color.add_argument("--no-color", dest="color", action="store_false", help="disable ANSI color")
    p.add_argument("--version", action="version", version=f"starhue {__version__}")
    return p


def _validate_temps(temps: Sequence[float]) -> None:
    """Reject any non-positive temperature.

    Args:
        temps (Sequence[float]): Temperatures in kelvin to validate.

    Raises:
        SystemExit: If any temperature is not positive.
    """
    for t in temps:
        if t <= 0:
            raise SystemExit(f"starhue: temperature must be positive, got {t:g}")


def _parse_color(value: str) -> tuple:
    """Parse a CLI color: ``#rrggbb``/``#rgb`` or ``r,g,b``.

    Args:
        value (str): The color string from the command line.

    Returns:
        tuple: The ``(r, g, b)`` channels as 0–255 ints.

    Raises:
        SystemExit: If the color cannot be parsed.
    """
    s = value.strip()
    if "," in s:
        parts = s.split(",")
        if len(parts) != 3:
            raise SystemExit(f"starhue: expected 'r,g,b', got {value!r}")
        try:
            return tuple(max(0, min(255, int(p))) for p in parts)
        except ValueError:
            raise SystemExit(f"starhue: invalid r,g,b color {value!r}") from None
    try:
        return hex_to_rgb(s)
    except ValueError as exc:
        raise SystemExit(f"starhue: {exc}") from None


def main(argv: Optional[List[str]] = None) -> int:
    """Run the starhue command-line interface.

    Args:
        argv (list[str] | None): Argument vector; defaults to ``sys.argv`` when
            None.

    Returns:
        int: Process exit code (0 on success).
    """
    args = _build_parser().parse_args(argv)
    use_color = supports_color() if args.color is None else args.color

    # --- inverse mode: a color → its nearest blackbody --------------------
    if args.from_color:
        rgb = _parse_color(args.from_color)
        temperature = color_to_temperature(rgb)
        print(
            f"# {args.from_color.strip()} → nearest blackbody {temperature:.0f} K",
            file=sys.stderr,
        )
        temps: List[float] = [temperature]
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
