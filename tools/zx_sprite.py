#!/usr/bin/env python3
"""Validate and render transparent ZX-palette sprite text grids."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image


PALETTE = {
    "C.BLACK": (0x00, 0x00, 0x00, 0xFF),
    "C.BLUE": (0x00, 0x00, 0xCD, 0xFF),
    "C.RED": (0xCD, 0x00, 0x00, 0xFF),
    "C.MAGENTA": (0xCD, 0x00, 0xCD, 0xFF),
    "C.GREEN": (0x00, 0xCD, 0x00, 0xFF),
    "C.CYAN": (0x00, 0xCD, 0xCD, 0xFF),
    "C.YELLOW": (0xCD, 0xCD, 0x00, 0xFF),
    "C.WHITE": (0xCD, 0xCD, 0xCD, 0xFF),
    "C.B_BLACK": (0x00, 0x00, 0x00, 0xFF),
    "C.B_BLUE": (0x00, 0x00, 0xFF, 0xFF),
    "C.B_RED": (0xFF, 0x00, 0x00, 0xFF),
    "C.B_MAGENTA": (0xFF, 0x00, 0xFF, 0xFF),
    "C.B_GREEN": (0x00, 0xFF, 0x00, 0xFF),
    "C.B_CYAN": (0x00, 0xFF, 0xFF, 0xFF),
    "C.B_YELLOW": (0xFF, 0xFF, 0x00, 0xFF),
    "C.B_WHITE": (0xFF, 0xFF, 0xFF, 0xFF),
}
TRANSPARENT = (0x00, 0x00, 0x00, 0x00)
SYMBOL_RE = re.compile(r"[A-Za-z]")
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class SpriteError(ValueError):
    """Raised when a sprite grid or legend is invalid."""


def load_rows(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise SpriteError(f"{path} must be UTF-8 text") from error


def parse_legend(values: list[str]) -> dict[str, str]:
    legend: dict[str, str] = {}
    tokens = [
        token
        for value in values
        for token in re.split(r"[\s,]+", value.strip())
        if token
    ]
    if not tokens:
        raise SpriteError("legend must contain at least one SYMBOL=C.CONSTANT mapping")

    for token in tokens:
        if token.count("=") != 1:
            raise SpriteError(f"invalid legend mapping {token!r}; expected X=C.NAME")
        symbol, constant = token.split("=", 1)
        if not SYMBOL_RE.fullmatch(symbol):
            raise SpriteError(f"legend symbol {symbol!r} must be one ASCII letter")
        if symbol in legend:
            raise SpriteError(f"duplicate legend symbol {symbol!r}")
        if constant not in PALETTE:
            allowed = ", ".join(PALETTE)
            raise SpriteError(f"illegal palette constant {constant!r}; choose from {allowed}")
        legend[symbol] = constant
    return legend


def validate(rows: list[str], width: int, height: int, legend: dict[str, str]) -> None:
    if width < 1 or height < 1:
        raise SpriteError("width and height must be positive integers")
    if len(rows) != height:
        raise SpriteError(f"expected {height} rows, got {len(rows)}")

    for row_index, row in enumerate(rows, start=1):
        if len(row) != width:
            raise SpriteError(
                f"row {row_index} must contain exactly {width} characters; got {len(row)}"
            )
        for column_index, symbol in enumerate(row, start=1):
            if symbol == ".":
                continue
            if not SYMBOL_RE.fullmatch(symbol):
                raise SpriteError(
                    f"row {row_index}, column {column_index}: {symbol!r} is not '.' "
                    "or an ASCII letter"
                )
            if symbol not in legend:
                raise SpriteError(
                    f"row {row_index}, column {column_index}: symbol {symbol!r} "
                    "is missing from the legend"
                )


def render(rows: list[str], width: int, height: int, legend: dict[str, str]) -> Image.Image:
    image = Image.new("RGBA", (width, height), TRANSPARENT)
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, symbol in enumerate(row):
            if symbol != ".":
                pixels[x, y] = PALETTE[legend[symbol]]
    return image


def write_outputs(
    rows: list[str],
    width: int,
    height: int,
    legend: dict[str, str],
    name: str,
    out_dir: Path | None = None,
    json_only: bool = False,
) -> tuple[Path, Path | None, Path | None]:
    if not NAME_RE.fullmatch(name):
        raise SpriteError(
            "name must start with an ASCII letter or digit and contain only "
            "letters, digits, '.', '_', or '-'"
        )

    output_dir = out_dir if out_dir is not None else Path.cwd() / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{name}.json"

    payload = {"w": width, "h": height, "rows": rows, "legend": legend}
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # The JSON is the whole sprite: `{w, h, rows, legend}` regenerates both PNGs
    # exactly. `--json-only` is for a repository that keeps sources and renders
    # apart and builds the renders on demand.
    if json_only:
        return json_path, None, None

    native_path = output_dir / f"{name}.png"
    preview_path = output_dir / f"{name}_4x.png"
    native = render(rows, width, height, legend)
    native.save(native_path)
    native.resize((width * 4, height * 4), Image.Resampling.NEAREST).save(preview_path)
    return json_path, native_path, preview_path


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("rows", type=Path, help="UTF-8 text file containing the sprite grid")
    root.add_argument("--width", type=int, required=True, help="grid width in pixels")
    root.add_argument("--height", type=int, required=True, help="grid height in pixels")
    root.add_argument(
        "--legend",
        nargs="+",
        required=True,
        metavar="X=C.NAME",
        help="one mapping per used letter; comma or whitespace separation is accepted",
    )
    root.add_argument(
        "--name",
        help="output basename (default: input filename stem)",
    )
    root.add_argument(
        "--out",
        type=Path,
        help="directory to write into (default: ./outputs)",
    )
    root.add_argument(
        "--json-only",
        action="store_true",
        help="write only the JSON grid; both PNGs are derivable from it",
    )
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        rows = load_rows(args.rows)
        legend = parse_legend(args.legend)
        validate(rows, args.width, args.height, legend)
        name = args.name if args.name is not None else args.rows.stem
        json_path, native_path, preview_path = write_outputs(
            rows, args.width, args.height, legend, name, args.out, args.json_only
        )
    except (OSError, SpriteError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    written = ", ".join(str(p) for p in (json_path, native_path, preview_path) if p)
    print(f"PASS {args.width}x{args.height}; {len(legend)} colours; WROTE {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
