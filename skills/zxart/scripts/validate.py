#!/usr/bin/env python3

"""
ZX Spectrum image validator.

Validates:

* dimensions <= 256x192
* RGB image
* no alpha/transparency
* only the allowed ZX Spectrum palette
* maximum 15 unique colors
* maximum 2 colors per 8x8 attribute cell

Usage:

```
python validate.py image.png
```

Exit codes:
0 = valid
1 = validation failed
2 = invalid command-line usage / input error
"""

from **future** import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

MAX_WIDTH = 256
MAX_HEIGHT = 192
CELL_SIZE = 8
MAX_COLORS_PER_CELL = 2
MAX_GLOBAL_COLORS = 15

PALETTE = {
(0x00, 0x00, 0x00),  # BLACK / B_BLACK
(0x00, 0x00, 0xCD),  # BLUE
(0xCD, 0x00, 0x00),  # RED
(0xCD, 0x00, 0xCD),  # MAGENTA
(0x00, 0xCD, 0x00),  # GREEN
(0x00, 0xCD, 0xCD),  # CYAN
(0xCD, 0xCD, 0x00),  # YELLOW
(0xCD, 0xCD, 0xCD),  # WHITE
(0x00, 0x00, 0xFF),  # B_BLUE
(0xFF, 0x00, 0x00),  # B_RED
(0xFF, 0x00, 0xFF),  # B_MAGENTA
(0x00, 0xFF, 0x00),  # B_GREEN
(0x00, 0xFF, 0xFF),  # B_CYAN
(0xFF, 0xFF, 0x00),  # B_YELLOW
(0xFF, 0xFF, 0xFF),  # B_WHITE
}

def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
return "#{:02X}{:02X}{:02X}".format(*rgb)

def validate_image(path: Path) -> bool:
errors: list[str] = []

```
try:
    with Image.open(path) as image:
        width, height = image.size
        original_mode = image.mode

        print(f"Image: {path}")
        print(f"Dimensions: {width}x{height}")
        print(f"Mode: {original_mode}")

        # ------------------------------------------------------------
        # Dimensions
        # ------------------------------------------------------------

        if width < 1 or height < 1:
            errors.append(
                f"Invalid dimensions: {width}x{height}. "
                "Both dimensions must be at least 1."
            )

        if width > MAX_WIDTH or height > MAX_HEIGHT:
            errors.append(
                f"Image exceeds maximum dimensions: "
                f"{width}x{height}. "
                f"Maximum is {MAX_WIDTH}x{MAX_HEIGHT}."
            )

        # ------------------------------------------------------------
        # Color mode
        # ------------------------------------------------------------

        if original_mode != "RGB":
            errors.append(
                f"Invalid image mode: {original_mode}. "
                "Image must be RGB with no alpha/transparency."
            )

        # Do not silently convert here.
        # The validator validates the actual image supplied by the agent.
        if original_mode != "RGB":
            print("\nINVALID IMAGE\n")
            for error in errors:
                print(f"- {error}")
            return False

        pixels = list(image.getdata())
        unique_colors = set(pixels)

        # ------------------------------------------------------------
        # Global palette validation
        # ------------------------------------------------------------

        invalid_colors = unique_colors - PALETTE

        if invalid_colors:
            errors.append(
                f"Found {len(invalid_colors)} color(s) outside "
                "the ZX Spectrum palette."
            )

        if len(unique_colors) > MAX_GLOBAL_COLORS:
            errors.append(
                f"Image contains {len(unique_colors)} unique colors. "
                f"Maximum allowed is {MAX_GLOBAL_COLORS}."
            )

        # ------------------------------------------------------------
        # Attribute-cell validation
        # ------------------------------------------------------------

        invalid_cells: list[dict] = []

        for cell_y in range(0, height, CELL_SIZE):
            for cell_x in range(0, width, CELL_SIZE):
                cell_colors: set[tuple[int, int, int]] = set()

                cell_width = min(CELL_SIZE, width - cell_x)
                cell_height = min(CELL_SIZE, height - cell_y)

                for y in range(cell_y, cell_y + cell_height):
                    for x in range(cell_x, cell_x + cell_width):
                        cell_colors.add(image.getpixel((x, y)))

                if len(cell_colors) > MAX_COLORS_PER_CELL:
                    invalid_cells.append(
                        {
                            "x": cell_x // CELL_SIZE,
                            "y": cell_y // CELL_SIZE,
                            "pixel_x_start": cell_x,
                            "pixel_x_end": cell_x + cell_width - 1,
                            "pixel_y_start": cell_y,
                            "pixel_y_end": cell_y + cell_height - 1,
                            "colors": sorted(cell_colors),
                        }
                    )

        if invalid_cells:
            errors.append(
                f"{len(invalid_cells)} attribute cell(s) contain "
                f"more than {MAX_COLORS_PER_CELL} colors."
            )

        # ------------------------------------------------------------
        # Result
        # ------------------------------------------------------------

        if errors:
            print("\nINVALID IMAGE\n")

            for error in errors:
                print(f"- {error}")

            if invalid_colors:
                print("\nInvalid colors:")

                for color in sorted(invalid_colors):
                    print(f"  {rgb_to_hex(color)}")

            if invalid_cells:
                print("\nInvalid attribute cells:")

                for cell in invalid_cells:
                    print(
                        f"\nCell: ({cell['x']}, {cell['y']})"
                    )
                    print(
                        "Pixel bounds: "
                        f"x={cell['pixel_x_start']}.."
                        f"{cell['pixel_x_end']}, "
                        f"y={cell['pixel_y_start']}.."
                        f"{cell['pixel_y_end']}"
                    )
                    print(
                        f"Colors found: {len(cell['colors'])}"
                    )
                    print("Colors:")

                    for color in cell["colors"]:
                        print(f"  {rgb_to_hex(color)}")

            return False

        print("\nVALID ZX SPECTRUM IMAGE")
        print(f"Unique colors: {len(unique_colors)}")

        cells_x = (width + CELL_SIZE - 1) // CELL_SIZE
        cells_y = (height + CELL_SIZE - 1) // CELL_SIZE

        print(
            f"Attribute cells checked: "
            f"{cells_x} x {cells_y} = {cells_x * cells_y}"
        )

        print("Palette: OK")
        print("Attribute cells: OK")
        print("Dimensions: OK")

        return True

except FileNotFoundError:
    print(f"ERROR: File not found: {path}", file=sys.stderr)
    return False

except OSError as exc:
    print(
        f"ERROR: Could not read image '{path}': {exc}",
        file=sys.stderr,
    )
    return False
```

def main() -> int:
parser = argparse.ArgumentParser(
description="Validate an image against ZX Spectrum graphical constraints."
)

```
parser.add_argument(
    "image",
    type=Path,
    help="Path to the image to validate.",
)

args = parser.parse_args()

if validate_image(args.image):
    return 0

return 1
```

if **name** == "**main**":
sys.exit(main())
