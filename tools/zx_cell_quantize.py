#!/usr/bin/env python3
"""Quantize concept art into ZX Spectrum 48K 8x8 attribute CELLs."""

from __future__ import annotations

import argparse
from itertools import combinations_with_replacement
from pathlib import Path

from PIL import Image, ImageOps


WIDTH = 256
HEIGHT = 192
CELL = 8
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


def distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    """Weighted squared RGB distance, favouring luminance and green detail."""
    red = left[0] - right[0]
    green = left[1] - right[1]
    blue = left[2] - right[2]
    return 3 * red * red + 6 * green * green + 2 * blue * blue


def palette_banks(mode: str) -> tuple[tuple[tuple[int, int, int], ...], ...]:
    if mode == "normal":
        return (NORMAL,)
    if mode == "bright":
        return (BRIGHT,)
    return (NORMAL, BRIGHT)


def quantize_cell(
    pixels: list[tuple[int, int, int]], mode: str
) -> tuple[list[tuple[int, int, int]], int]:
    best_pair: tuple[tuple[int, int, int], tuple[int, int, int]] | None = None
    best_cost: int | None = None
    best_bright = 0

    for palette in palette_banks(mode):
        bright = int(palette is BRIGHT)
        for first_index, second_index in combinations_with_replacement(range(8), 2):
            first = palette[first_index]
            second = palette[second_index]
            cost = sum(
                min(distance(pixel, first), distance(pixel, second))
                for pixel in pixels
            )
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_pair = (first, second)
                best_bright = bright

    assert best_pair is not None
    first, second = best_pair
    return (
        [
            first if distance(pixel, first) <= distance(pixel, second) else second
            for pixel in pixels
        ],
        best_bright,
    )


def resize_concept(image: Image.Image, mode: str) -> Image.Image:
    image = image.convert("RGB")
    if mode == "stretch":
        return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    if mode == "contain":
        resized = ImageOps.contain(image, (WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        result = Image.new("RGB", (WIDTH, HEIGHT), NORMAL[0])
        result.paste(resized, ((WIDTH - resized.width) // 2, (HEIGHT - resized.height) // 2))
        return result
    return ImageOps.fit(
        image,
        (WIDTH, HEIGHT),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def convert(source: Path, output: Path, brightness: str, resize: str) -> None:
    with Image.open(source) as opened:
        concept = resize_concept(opened, resize)

    result = Image.new("RGB", (WIDTH, HEIGHT), NORMAL[0])
    bright_cells = 0
    for cell_y in range(HEIGHT // CELL):
        for cell_x in range(WIDTH // CELL):
            x0 = cell_x * CELL
            y0 = cell_y * CELL
            pixels = [
                concept.getpixel((x0 + x, y0 + y))
                for y in range(CELL)
                for x in range(CELL)
            ]
            converted, bright = quantize_cell(pixels, brightness)
            bright_cells += bright
            for index, pixel in enumerate(converted):
                result.putpixel((x0 + index % CELL, y0 + index // CELL), pixel)

    result.save(output)
    print(
        f"WROTE {output} ({WIDTH}x{HEIGHT}; "
        f"brightness={brightness}; BRIGHT CELLs={bright_cells}/768; "
        f"colours={len(set(result.getdata()))})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--brightness",
        choices=("auto", "normal", "bright"),
        default="auto",
        help="allowed CELL brightness banks (default: auto)",
    )
    parser.add_argument(
        "--resize",
        choices=("cover", "contain", "stretch"),
        default="cover",
        help="how to fit the concept into 256x192 (default: cover)",
    )
    args = parser.parse_args()
    convert(args.source, args.output, args.brightness, args.resize)


if __name__ == "__main__":
    main()
