#!/usr/bin/env python3
"""Validate and export hardware-valid ZX Spectrum 48K standard screens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


WIDTH = 256
HEIGHT = 192
CELL = 8
COLS = WIDTH // CELL
ROWS = HEIGHT // CELL
BITMAP_BYTES = 6144
ATTRIBUTE_BYTES = 768
SCREEN_BYTES = BITMAP_BYTES + ATTRIBUTE_BYTES

NORMAL = (
    (0x00, 0x00, 0x00),
    (0x00, 0x00, 0xCD),
    (0xCD, 0x00, 0x00),
    (0xCD, 0x00, 0xCD),
    (0x00, 0xCD, 0x00),
    (0x00, 0xCD, 0xCD),
    (0xCD, 0xCD, 0x00),
    (0xCD, 0xCD, 0xCD),
)
BRIGHT = (
    (0x00, 0x00, 0x00),
    (0x00, 0x00, 0xFF),
    (0xFF, 0x00, 0x00),
    (0xFF, 0x00, 0xFF),
    (0x00, 0xFF, 0x00),
    (0x00, 0xFF, 0xFF),
    (0xFF, 0xFF, 0x00),
    (0xFF, 0xFF, 0xFF),
)
VISIBLE_PALETTE = frozenset(NORMAL + BRIGHT)


class ScreenError(ValueError):
    """Raised when an image cannot be represented by the standard screen."""


def load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source.seek(0)
        image = source.convert("RGB")
    if image.size != (WIDTH, HEIGHT):
        raise ScreenError(
            f"expected {WIDTH}x{HEIGHT}, got {image.width}x{image.height}"
        )
    return image


def colour_candidates(rgb: tuple[int, int, int]) -> list[tuple[int, int]]:
    """Return possible (bright, colour-index) encodings for an RGB colour."""
    candidates: list[tuple[int, int]] = []
    for bright, palette in enumerate((NORMAL, BRIGHT)):
        for index, value in enumerate(palette):
            if value == rgb:
                candidates.append((bright, index))
    return candidates


def infer_cell(
    image: Image.Image, cell_x: int, cell_y: int
) -> tuple[int, int, int]:
    """Infer (bright, paper, ink), choosing the common colour as PAPER."""
    x0 = cell_x * CELL
    y0 = cell_y * CELL
    counts: dict[tuple[int, int, int], int] = {}
    for y in range(y0, y0 + CELL):
        for x in range(x0, x0 + CELL):
            rgb = image.getpixel((x, y))
            counts[rgb] = counts.get(rgb, 0) + 1

    if len(counts) > 2:
        colours = ", ".join(f"#{r:02X}{g:02X}{b:02X}" for r, g, b in counts)
        raise ScreenError(
            f"CELL ({cell_x},{cell_y}) contains {len(counts)} colours: {colours}"
        )

    for rgb in counts:
        if rgb not in VISIBLE_PALETTE:
            raise ScreenError(
                f"CELL ({cell_x},{cell_y}) contains illegal colour "
                f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
            )

    colours = sorted(counts, key=lambda rgb: (-counts[rgb], rgb))
    if len(colours) == 1:
        candidates = colour_candidates(colours[0])
        bright, index = min(candidates)
        return bright, index, index

    common_brightness = {
        bright
        for bright, _ in colour_candidates(colours[0])
        if any(b == bright for b, _ in colour_candidates(colours[1]))
    }
    if not common_brightness:
        raise ScreenError(
            f"CELL ({cell_x},{cell_y}) mixes normal and BRIGHT colours"
        )

    # Prefer normal for an all-black ambiguity; otherwise the visible colours
    # make the brightness choice unique.
    bright = min(common_brightness)
    paper = next(i for b, i in colour_candidates(colours[0]) if b == bright)
    ink = next(i for b, i in colour_candidates(colours[1]) if b == bright)
    return bright, paper, ink


def analyse(image: Image.Image) -> list[list[tuple[int, int, int]]]:
    pixels = set(image.getdata())
    illegal = pixels - VISIBLE_PALETTE
    if illegal:
        rgb = min(illegal)
        raise ScreenError(f"image contains illegal colour #{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
    if len(pixels) > 15:
        raise ScreenError(f"image contains {len(pixels)} visible colours; maximum is 15")

    return [
        [infer_cell(image, cell_x, cell_y) for cell_x in range(COLS)]
        for cell_y in range(ROWS)
    ]


def bitmap_offset(x_byte: int, y: int) -> int:
    """Return the native ZX bitmap offset for byte column x_byte and scan y."""
    return (
        ((y & 0b11000000) << 5)
        | ((y & 0b00000111) << 8)
        | ((y & 0b00111000) << 2)
        | x_byte
    )


def load_flash_map(path: Path | None) -> list[list[bool]]:
    if path is None:
        return [[False] * COLS for _ in range(ROWS)]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or len(data) != ROWS:
        raise ScreenError(f"FLASH map must contain {ROWS} rows")
    result: list[list[bool]] = []
    for row_index, row in enumerate(data):
        if not isinstance(row, list) or len(row) != COLS:
            raise ScreenError(f"FLASH map row {row_index} must contain {COLS} values")
        result.append([bool(value) for value in row])
    return result


def encode(image: Image.Image, flash_map: list[list[bool]]) -> bytes:
    cells = analyse(image)
    screen = bytearray(SCREEN_BYTES)

    for cell_y in range(ROWS):
        for cell_x in range(COLS):
            bright, paper, ink = cells[cell_y][cell_x]
            attribute = (
                (int(flash_map[cell_y][cell_x]) << 7)
                | (bright << 6)
                | (paper << 3)
                | ink
            )
            screen[BITMAP_BYTES + cell_y * COLS + cell_x] = attribute

            ink_rgb = (BRIGHT if bright else NORMAL)[ink]
            for pixel_y in range(CELL):
                value = 0
                y = cell_y * CELL + pixel_y
                for pixel_x in range(CELL):
                    x = cell_x * CELL + pixel_x
                    if image.getpixel((x, y)) == ink_rgb:
                        value |= 1 << (7 - pixel_x)
                screen[bitmap_offset(cell_x, y)] = value

    return bytes(screen)


def decode(screen: bytes, alternate_flash: bool = False) -> Image.Image:
    if len(screen) != SCREEN_BYTES:
        raise ScreenError(f"expected {SCREEN_BYTES} SCR bytes, got {len(screen)}")

    image = Image.new("RGB", (WIDTH, HEIGHT))
    for cell_y in range(ROWS):
        for cell_x in range(COLS):
            attribute = screen[BITMAP_BYTES + cell_y * COLS + cell_x]
            flash = bool(attribute & 0x80)
            bright = bool(attribute & 0x40)
            paper = (attribute >> 3) & 0x07
            ink = attribute & 0x07
            if alternate_flash and flash:
                paper, ink = ink, paper
            palette = BRIGHT if bright else NORMAL

            for pixel_y in range(CELL):
                y = cell_y * CELL + pixel_y
                value = screen[bitmap_offset(cell_x, y)]
                for pixel_x in range(CELL):
                    index = ink if value & (1 << (7 - pixel_x)) else paper
                    image.putpixel((cell_x * CELL + pixel_x, y), palette[index])
    return image


def nearest(image: Image.Image, scale: int) -> Image.Image:
    if scale < 1:
        raise ScreenError("scale must be a positive integer")
    return image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)


def save_gif(screen: bytes, output: Path, scale: int) -> None:
    phase_a = nearest(decode(screen, alternate_flash=False), scale)
    phase_b = nearest(decode(screen, alternate_flash=True), scale)
    phase_a.save(
        output,
        save_all=True,
        append_images=[phase_b],
        duration=[320, 320],
        loop=0,
        optimize=False,
        disposal=1,
    )


def command_validate(args: argparse.Namespace) -> None:
    image = load_rgb(args.input)
    cells = analyse(image)
    screen = encode(image, [[False] * COLS for _ in range(ROWS)])
    reconstructed = decode(screen)
    if reconstructed.tobytes() != image.tobytes():
        raise ScreenError("SCR round trip is not pixel-exact")
    visible = len(set(image.getdata()))
    print(
        f"PASS {WIDTH}x{HEIGHT}; {COLS}x{ROWS} CELLs; "
        f"{visible}/15 colours; {len(cells) * len(cells[0])} CELLs valid; "
        f"SCR round trip exact"
    )


def command_encode(args: argparse.Namespace) -> None:
    image = load_rgb(args.input)
    screen = encode(image, load_flash_map(args.flash_map))
    args.output.write_bytes(screen)
    if decode(screen).tobytes() != image.tobytes():
        raise ScreenError("encoded SCR does not reconstruct the input exactly")
    print(f"WROTE {args.output} ({len(screen)} bytes)")


def command_decode(args: argparse.Namespace) -> None:
    screen = args.input.read_bytes()
    image = decode(screen, alternate_flash=args.alternate_flash)
    image.save(args.output)
    print(f"WROTE {args.output} ({image.width}x{image.height})")


def command_upscale(args: argparse.Namespace) -> None:
    image = load_rgb(args.input)
    analyse(image)
    enlarged = nearest(image, args.scale)
    enlarged.save(args.output)
    print(f"WROTE {args.output} ({enlarged.width}x{enlarged.height}, {args.scale}x)")


def command_gif(args: argparse.Namespace) -> None:
    screen = args.input.read_bytes()
    if len(screen) != SCREEN_BYTES:
        raise ScreenError(f"expected {SCREEN_BYTES} SCR bytes, got {len(screen)}")
    save_gif(screen, args.output, args.scale)
    print(
        f"WROTE {args.output} ({WIDTH * args.scale}x{HEIGHT * args.scale}, "
        "two 320 ms FLASH phases)"
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subcommands = root.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="validate a native PNG")
    validate.add_argument("input", type=Path)
    validate.set_defaults(func=command_validate)

    encode_parser = subcommands.add_parser("encode", help="encode PNG to 6912-byte SCR")
    encode_parser.add_argument("input", type=Path)
    encode_parser.add_argument("output", type=Path)
    encode_parser.add_argument(
        "--flash-map",
        type=Path,
        help="JSON array containing 24 rows of 32 boolean FLASH values",
    )
    encode_parser.set_defaults(func=command_encode)

    decode_parser = subcommands.add_parser("decode", help="decode SCR to native PNG")
    decode_parser.add_argument("input", type=Path)
    decode_parser.add_argument("output", type=Path)
    decode_parser.add_argument("--alternate-flash", action="store_true")
    decode_parser.set_defaults(func=command_decode)

    upscale = subcommands.add_parser("upscale", help="nearest-neighbour upscale")
    upscale.add_argument("input", type=Path)
    upscale.add_argument("output", type=Path)
    upscale.add_argument("--scale", type=int, default=4)
    upscale.set_defaults(func=command_upscale)

    gif = subcommands.add_parser("gif", help="make two-phase FLASH GIF from SCR")
    gif.add_argument("input", type=Path)
    gif.add_argument("output", type=Path)
    gif.add_argument("--scale", type=int, default=4)
    gif.set_defaults(func=command_gif)

    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.func(args)
    except (OSError, ScreenError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
