#!/usr/bin/env python3
"""Build the hand-authored 80x56 ZX rainbow unicorn source grid."""

from pathlib import Path

from PIL import Image, ImageDraw


W, H = 80, 56

# Numeric values are converted to zx-kit layer symbols at the end. Drawing at
# the final pixel resolution keeps every edge crisp and deterministic.
SYMBOLS = {
    0: "K",  # black background
    1: "W",  # bright white fur
    2: "S",  # normal white fur shadow
    3: "R",
    4: "Y",
    5: "G",
    6: "C",
    7: "B",
    8: "M",
}

LAYER_INFO = [
    ("K", "background", "C.BLACK"),
    ("W", "brightWhiteFur", "C.B_WHITE"),
    ("S", "whiteFurShadow", "C.WHITE"),
    ("R", "redHair", "C.B_RED"),
    ("Y", "yellowHairAndHorn", "C.B_YELLOW"),
    ("G", "greenHair", "C.B_GREEN"),
    ("C", "cyanHair", "C.B_CYAN"),
    ("B", "blueHairAndEye", "C.B_BLUE"),
    ("M", "magentaHair", "C.B_MAGENTA"),
]


def main() -> None:
    image = Image.new("P", (W, H), 0)
    draw = ImageDraw.Draw(image)

    # Rainbow tail, placed behind the body. Thick native-resolution strokes
    # make the colour bands readable when the sprite moves.
    tail_paths = [
        (3, [(57, 25), (66, 20), (74, 21), (77, 17)]),
        (4, [(58, 27), (67, 23), (75, 25), (78, 22)]),
        (5, [(58, 29), (68, 27), (76, 29), (78, 28)]),
        (6, [(58, 31), (67, 31), (75, 34), (78, 33)]),
        (7, [(57, 33), (66, 35), (73, 39), (77, 38)]),
        (8, [(56, 35), (64, 39), (70, 43), (74, 42)]),
    ]
    for colour, points in tail_paths:
        draw.line(points, fill=colour, width=4, joint="curve")

    # Hind legs and far foreleg.
    draw.polygon([(48, 34), (55, 34), (55, 45), (58, 49), (57, 52),
                  (51, 52), (50, 48)], fill=2)
    draw.polygon([(29, 34), (35, 35), (34, 45), (36, 50), (34, 52),
                  (28, 52), (29, 47)], fill=2)

    # Main torso with a high, elegant back and tucked belly.
    draw.ellipse((25, 21, 61, 39), fill=1)
    draw.polygon([(22, 23), (31, 19), (42, 19), (50, 21), (45, 37),
                  (31, 38), (24, 33)], fill=1)

    # Neck slopes into a left-facing head.
    draw.polygon([(24, 20), (34, 21), (32, 33), (27, 37), (21, 32),
                  (19, 25)], fill=1)
    draw.ellipse((11, 17, 29, 29), fill=1)
    draw.polygon([(8, 22), (18, 19), (20, 27), (15, 31), (8, 28),
                  (6, 25)], fill=1)

    # Ear, horn, and muzzle details.
    draw.polygon([(20, 18), (21, 11), (25, 18)], fill=1)
    draw.polygon([(15, 18), (11, 8), (18, 17)], fill=4)
    draw.line([(12, 10), (16, 16)], fill=1, width=1)
    draw.rectangle((7, 25, 10, 27), fill=2)

    # Front and near hind legs, with separated hooves for a clear stance.
    draw.polygon([(22, 33), (29, 34), (27, 45), (29, 49), (27, 52),
                  (20, 52), (22, 47)], fill=1)
    draw.polygon([(48, 34), (55, 34), (53, 45), (55, 49), (53, 52),
                  (46, 52), (48, 46)], fill=1)
    draw.rectangle((20, 50, 28, 52), fill=2)
    draw.rectangle((46, 50, 54, 52), fill=2)

    # Rainbow mane follows the rear edge of the neck in six distinct tufts.
    mane = [
        (3, [(27, 17), (33, 18), (31, 22), (27, 21)]),
        (4, [(29, 20), (35, 21), (32, 25), (28, 24)]),
        (5, [(30, 23), (36, 25), (32, 28), (28, 27)]),
        (6, [(30, 26), (35, 29), (31, 31), (27, 29)]),
        (7, [(29, 29), (34, 33), (29, 34), (25, 31)]),
        (8, [(27, 32), (31, 37), (26, 37), (22, 33)]),
    ]
    for colour, polygon in mane:
        draw.polygon(polygon, fill=colour)

    # Fur shading remains exact ZX normal white; highlights stay bright white.
    draw.line([(33, 35), (42, 37), (49, 36)], fill=2, width=2)
    draw.line([(34, 23), (45, 22), (54, 25)], fill=2, width=1)
    draw.line([(14, 29), (20, 30), (23, 27)], fill=2, width=1)
    draw.rectangle((41, 24, 43, 25), fill=1)

    # Facial features and a small smile. Black is legal and remains legible
    # because these pixels sit inside the white head.
    draw.rectangle((14, 20, 15, 21), fill=7)
    draw.point((15, 21), fill=0)
    draw.point((8, 25), fill=0)
    draw.line([(9, 28), (12, 29), (15, 28)], fill=0, width=1)

    # A few single-pixel fur highlights sharpen the silhouette.
    for point in [(18, 18), (23, 20), (31, 20), (56, 24), (59, 29),
                  (44, 38), (25, 43), (51, 43)]:
        draw.point(point, fill=1)

    rows = ["".join(SYMBOLS[image.getpixel((x, y))] for x in range(W))
            for y in range(H)]
    output = Path("outputs/rainbow_unicorn_rows.txt")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"WROTE {output} ({W}x{H})")

    row_source = "\n".join(f'  "{row}",' for row in rows)
    layer_source = "\n".join(
        "  { "
        f'name: "{name}", symbol: "{symbol}", color: {colour}, '
        f'bitmap: createBitmapFromRows(layerRows("{symbol}"))'
        " },"
        for symbol, name, colour in LAYER_INFO
    )
    ts_source = f'''import {{ C, createBitmapFromRows, drawBitmap }} from "zx-kit";

export const RAINBOW_UNICORN_WIDTH = {W};
export const RAINBOW_UNICORN_HEIGHT = {H};

export const rainbowUnicornRows = [
{row_source}
] as const;

function layerRows(symbol: string): string[] {{
  return rainbowUnicornRows.map((row) =>
    Array.from(row, (pixel) => pixel === symbol ? "x" : ".").join("")
  );
}}

export const rainbowUnicornLayers = [
{layer_source}
] as const;

export function drawRainbowUnicorn(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
): void {{
  for (const layer of rainbowUnicornLayers) {{
    drawBitmap(ctx, layer.bitmap, x, y, layer.color);
  }}
}}
'''
    ts_output = Path("outputs/rainbow_unicorn_zxkit.ts")
    ts_output.write_text(ts_source, encoding="utf-8")
    print(f"WROTE {ts_output}")


if __name__ == "__main__":
    main()
