#!/usr/bin/env python3
"""Convert the existing white-cat screen artwork into an animation-ready sprite."""

from collections import deque
from pathlib import Path

from PIL import Image


SOURCE = Path("output/zx-spectrum-screen/white-cat-256x192.png")
OUTPUT_ROWS = Path("outputs/white_cat_sitting_rows.txt")
OUTPUT_TS = Path("outputs/white_cat_sitting_zxkit.ts")
WIDTH = 96
HEIGHT = 128


def exterior_background(mask: list[list[bool]]) -> list[list[bool]]:
    """Return black pixels connected to the crop boundary."""
    height = len(mask)
    width = len(mask[0])
    outside = [[False] * width for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        for y in (0, height - 1):
            if not mask[y][x] and not outside[y][x]:
                outside[y][x] = True
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if not mask[y][x] and not outside[y][x]:
                outside[y][x] = True
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if (0 <= nx < width and 0 <= ny < height
                    and not mask[ny][nx] and not outside[ny][nx]):
                outside[ny][nx] = True
                queue.append((nx, ny))
    return outside


def main() -> None:
    source = Image.open(SOURCE).convert("RGB")
    white_pixels = [
        (x, y)
        for y in range(source.height)
        for x in range(source.width)
        if source.getpixel((x, y)) != (0, 0, 0)
    ]
    left = min(x for x, _ in white_pixels)
    top = min(y for _, y in white_pixels)
    right = max(x for x, _ in white_pixels) + 1
    bottom = max(y for _, y in white_pixels) + 1
    crop_width = right - left
    crop_height = bottom - top
    if (crop_width, crop_height) != (86, 122):
        raise ValueError(
            f"unexpected source silhouette {crop_width}x{crop_height}; expected 86x122"
        )

    white = [[False] * crop_width for _ in range(crop_height)]
    for y in range(crop_height):
        for x in range(crop_width):
            white[y][x] = source.getpixel((left + x, top + y)) != (0, 0, 0)

    outside = exterior_background(white)
    grid = [["."] * WIDTH for _ in range(HEIGHT)]
    offset_x = (WIDTH - crop_width) // 2
    offset_y = (HEIGHT - crop_height) // 2

    # A one-pixel four-connected outline keeps white fur readable over bright
    # game backgrounds. Enclosed black regions retain the original facial and
    # body line work.
    for y in range(crop_height):
        for x in range(crop_width):
            if white[y][x]:
                continue
            enclosed_detail = not outside[y][x]
            touches_fur = any(
                0 <= x + dx < crop_width
                and 0 <= y + dy < crop_height
                and white[y + dy][x + dx]
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if enclosed_detail or touches_fur:
                grid[offset_y + y][offset_x + x] = "K"

    # Extend the outline one pixel beyond the original crop where needed.
    for y in range(crop_height):
        for x in range(crop_width):
            if not white[y][x]:
                continue
            gx, gy = offset_x + x, offset_y + y
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and grid[ny][nx] == ".":
                    grid[ny][nx] = "K"

    for y in range(crop_height):
        for x in range(crop_width):
            if white[y][x]:
                grid[offset_y + y][offset_x + x] = "W"

    rows = ["".join(row) for row in grid]
    OUTPUT_ROWS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROWS.write_text("\n".join(rows) + "\n", encoding="utf-8")

    row_source = "\n".join(f'  "{row}",' for row in rows)
    ts_source = f'''import {{ C, createBitmapFromRows, drawBitmap }} from "zx-kit";

export const WHITE_CAT_WIDTH = {WIDTH};
export const WHITE_CAT_HEIGHT = {HEIGHT};
export const WHITE_CAT_ANCHOR_X = 48;
export const WHITE_CAT_ANCHOR_Y = 127;

export const whiteCatRows = [
{row_source}
] as const;

function layerRows(symbol: string): string[] {{
  return whiteCatRows.map((row) =>
    Array.from(row, (pixel) => pixel === symbol ? "x" : ".").join("")
  );
}}

export const whiteCatLayers = [
  {{ name: "outline", symbol: "K", color: C.BLACK,
    bitmap: createBitmapFromRows(layerRows("K")) }},
  {{ name: "fur", symbol: "W", color: C.B_WHITE,
    bitmap: createBitmapFromRows(layerRows("W")) }},
] as const;

export function drawWhiteCat(
  ctx: CanvasRenderingContext2D,
  anchorX: number,
  anchorY: number,
): void {{
  const x = anchorX - WHITE_CAT_ANCHOR_X;
  const y = anchorY - WHITE_CAT_ANCHOR_Y;
  for (const layer of whiteCatLayers) {{
    drawBitmap(ctx, layer.bitmap, x, y, layer.color);
  }}
}}
'''
    OUTPUT_TS.write_text(ts_source, encoding="utf-8")
    print(
        f"WROTE {OUTPUT_ROWS} and {OUTPUT_TS}; "
        f"source silhouette {crop_width}x{crop_height}; canvas {WIDTH}x{HEIGHT}"
    )


if __name__ == "__main__":
    main()
