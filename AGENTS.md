# AGENTS.md

# zx-imagegen

Repository instructions for Codex and other coding agents working on the
`zx-imagegen` project.

## 1. Purpose and authenticity requirement

This project creates images that are technically representable by an original
ZX Spectrum 48K standard screen, especially intro and loading-screen artwork.

Hardware validity is mandatory. A generic "retro", "8-bit", "pixel-art",
"old-school 1980s", or "early 1990s" appearance is not sufficient. An image
that looks similar but violates the ZX Spectrum bitmap or attribute structure
must not be accepted as a final asset.

Default artwork requirements:

- no text unless the user explicitly requests it;
- no cassette loading stripes unless explicitly requested;
- no antialiasing, alpha blending, gradients, interpolated colours, modern
  glow, blur, or other effects that cannot be encoded in the standard screen;
- no colours outside the project palette in section 4;
- preserve genuine attribute-cell restrictions, including visible attribute
  clash where it is unavoidable.

If a request conflicts with the original ZX Spectrum 48K standard display,
prefer hardware-authentic behaviour and explain the limitation.

---

## 2. Communication and maintenance

### 2.1 Language

- This file must always be maintained in English.
- All future edits to this file must also be written in English.
- Console and chat communication with the user must be in Slovak unless the
  user explicitly requests another language.

### 2.2 Maintenance

When the user asks to refine, expand, or correct project rules, update this
file and keep all sections mutually consistent.

---

## 3. Canonical ZX Spectrum 48K screen model

### 3.1 Native dimensions

The only canonical source resolution is exactly:

- width: `256` pixels;
- height: `192` pixels;
- total: `49,152` one-bit pixel positions.

The active image contains exactly `32` CELL columns and `24` CELL rows. Each
CELL is exactly `8x8` pixels, for a total of `768` cells.

Do not confuse rows and columns:

- `32 * 8 = 256` pixels horizontally;
- `24 * 8 = 192` pixels vertically.

### 3.2 Bitmap and attribute memory

A standard screen is representable as a `6912`-byte `.scr` payload:

- `6144` bytes of one-bit pixel bitmap data;
- `768` bytes of attributes, one byte per `8x8` CELL.

For each bitmap pixel, bit value `1` selects INK and bit value `0` selects
PAPER. The unusual native bitmap scan-line address order must be used when
writing or reading `.scr`; the attribute bytes follow in ordinary row-major
CELL order.

### 3.3 Attribute byte and two-colour rule

Every CELL has exactly one attribute byte:

```text
bit 7       FLASH
bit 6       BRIGHT
bits 5..3   PAPER colour index (0..7)
bits 2..0   INK colour index (0..7)
```

Therefore:

- one `8x8` CELL may reference at most two displayed colours: one INK and one
  PAPER;
- all 64 pixels in that CELL share the same INK, PAPER, BRIGHT, and FLASH;
- BRIGHT applies to both INK and PAPER; it is not selectable per colour or per
  pixel;
- normal and bright chromatic colours must never be mixed inside one CELL;
- BLACK and B_BLACK are visually identical, so the complete display has 15
  distinct visible colours rather than 16;
- assigning INK and PAPER the same colour is valid, although the bitmap then
  has no visible effect;
- hardware-authentic attribute clash is preferable to silently introducing a
  third colour or a second brightness level in a CELL.

### 3.4 FLASH and PAL animation

FLASH applies to the entire CELL. In the alternate phase, that CELL displays
the same bitmap with INK and PAPER exchanged. Non-FLASH cells remain unchanged.
FLASH does not intrinsically alternate between "visible" and solid black; that
description is not the standard hardware behaviour.

For an animated preview, use a looping two-state GIF:

- phase A duration: approximately `320 ms` (16 frames at 50 Hz PAL timing);
- phase B duration: approximately `320 ms`;
- full cycle: approximately `640 ms`;
- only cells whose FLASH bit is set may change between the phases;
- do not simulate FLASH with fades, intermediate colours, moving pixels, or
  independent pixel animation.

GIF is a preview/export format, not the canonical screen representation. The
native `256x192` indexed/static phases and, when applicable, the attribute data
remain authoritative.

### 3.5 Tiles are fragments of a screen

A tile (`art/<project>/tiles/*.json`, see `README.md` §1) is not a full screen,
but every rule in §3.3 applies to each of its `8x8` CELLs: one INK, one PAPER,
one brightness state. A tile's size must be a multiple of `8` and a tile is
fully opaque — `.` (transparent) is not allowed. The validator checks each CELL
with the same function the screen encoder uses, so any room laid out from valid
tiles on their own grid is a displayable standard screen.

Author tiles as text grids, like sprites. Do not derive them by downscaling.

---

## 4. Project colour palette

Use only these exact project sRGB constants. Do not derive, interpolate,
colour-correct, or add colours. These constants are the project's deterministic
digital representation; an analogue PAL/RF capture may look different and is
not the source palette.

```ts
export const C = {
  BLACK:     '#000000',
  BLUE:      '#0000CD',
  RED:       '#CD0000',
  MAGENTA:   '#CD00CD',
  GREEN:     '#00CD00',
  CYAN:      '#00CDCD',
  YELLOW:    '#CDCD00',
  WHITE:     '#CDCDCD',
  B_BLACK:   '#000000',
  B_BLUE:    '#0000FF',
  B_RED:     '#FF0000',
  B_MAGENTA: '#FF00FF',
  B_GREEN:   '#00FF00',
  B_CYAN:    '#00FFFF',
  B_YELLOW:  '#FFFF00',
  B_WHITE:   '#FFFFFF',
} as const
```

Palette-index values are:

```text
0 BLACK, 1 BLUE, 2 RED, 3 MAGENTA,
4 GREEN, 5 CYAN, 6 YELLOW, 7 WHITE
```

BRIGHT selects the `B_` form for both CELL colours. `B_BLACK` remains
`#000000`.

---

## 5. Required image-production workflow

### 5.1 Design stage

Always design and reason about the image at native `256x192` resolution.
Generated or hand-drawn concept art may be used only as a reference. It is not
a valid final image until it has been converted to the canonical bitmap plus
CELL attributes and has passed validation.

For every CELL, explicitly or algorithmically choose:

1. one brightness state (`BRIGHT=0` or `BRIGHT=1`);
2. one PAPER index;
3. one INK index;
4. one 64-bit `8x8` bitmap mask;
5. optionally one FLASH flag.

When a CELL is supplied as JSON, use this canonical representation:

```json
{
  "cell": {
    "bright": true,
    "flash": false,
    "ink": "C.BLUE",
    "paper": "C.YELLOW",
    "pixels": "..xx.... xxxx..xx .......x xxxxxxxx ........ x.x.x.x. .x.x.x.x ........"
  }
}
```

The `pixels` value must contain exactly eight whitespace-separated rows and
every row must contain exactly eight characters. Lowercase `x` selects INK and
`.` selects PAPER. No other character is valid. In the example, `bright: true`
makes `x` display as `B_BLUE` and `.` display as `B_YELLOW`. It does not create
two papers or two inks: the CELL still has one INK and one PAPER.

`bright` and `flash` are two boolean flags, not the CELL's two colours. Each
pixel remains a one-bit selector between the CELL-wide INK and PAPER. A pixel
cannot independently choose any of the eight base colours.

Quantisation or fitting must minimise error subject to these hard constraints;
it must never relax them. Dithering is permitted only when every resulting
pixel still selects one of that CELL's two legal colours. No micro-cell,
sub-cell, 8x1, multicolour, ULAplus, Timex, Pentagon, or ZX Spectrum Next mode
may be substituted for the standard `8x8` attribute mode.

### 5.2 Deterministic validation

Before delivery, validate the native master programmatically:

- dimensions are exactly `256x192`;
- every pixel is an exact palette constant;
- the image contains no more than 15 distinct visible colours globally;
- each aligned `8x8` CELL contains no more than two colours;
- both CELL colours belong to the same normal/bright bank, with black allowed
  in either bank because its RGB value is identical;
- a stored attribute byte and bitmap mask can reconstruct every CELL exactly;
- if FLASH is used, the second frame differs only by INK/PAPER exchange in
  FLASH cells;
- encode to `.scr`, decode it again, and require a pixel-exact round trip.

Visual inspection alone is never sufficient. If no suitable validator exists,
create one as part of the task.

The repository validator and exporter is `tools/zx_screen.py`. Its relevant
commands are `validate`, `encode`, `decode`, `upscale`, and `gif`. Use it for
final verification rather than replacing it with an informal image inspection.

### 5.3 Background requests and attribute clash

A requested background colour means PAPER uses that colour wherever possible.
For example, "blue background" means normal `BLUE` (`#0000CD`) unless the user
explicitly requests bright blue.

Because BRIGHT is CELL-wide, a CELL cannot contain normal BLUE paper and a
bright non-black INK. Choose one hardware-valid result:

- keep normal BLUE and use a normal INK colour;
- make both colours bright, which changes the paper to `B_BLUE` in that CELL;
- redesign the silhouette or CELL boundary to avoid the conflict.

Never hide this restriction by adding an illegal colour. A black background is
special: BLACK and B_BLACK look identical, so bright subject colours can share
a CELL with visually unchanged black paper.

### 5.4 Upscaling and final exports

The canonical master is always `256x192`. Upscaled files are derived previews
only and must use integer nearest-neighbour resampling with no filtering,
antialiasing, smoothing, sharpening, or colour conversion.

The default final preview is an exact `4x` linear upscale:

```text
256 * 4 = 1024
192 * 4 = 768
```

Therefore the correct `4x` dimensions are `1024x768`, not `1024x176`. The
native and enlarged images both retain the `4:3` aspect ratio.

For the default enlarged deliverable, upscale each native pixel into an exact
`4x4` block. Downscaling that file by exactly `1/4` with nearest-neighbour
sampling must reproduce the native `256x192` image pixel-for-pixel. For an
animated GIF, upscale every phase independently with the same method and retain
the phase timing and infinite loop.

Never repeatedly resample an already enlarged preview. Always regenerate every
export directly from the canonical native master.

---

## 6. Default subject and composition rules

When the user requests a cat without additional composition details:

- create a small, readable, continuous cat scene;
- use the requested background colour, defaulting to BLACK (`#000000`);
- favour a strong silhouette and deliberate CELL-aware colour placement;
- do not add text, loading stripes, borders, unrelated objects, or modern
  effects;
- let the genuine `8x8` attribute geometry influence colour boundaries without
  turning the image into arbitrary large square mosaic art.

The result must look intentionally drawn for the ZX Spectrum display, not like
unconstrained pixel art passed through a palette filter.

---

## 7. Delivery checklist

Unless the user requests fewer files, retain or provide:

- canonical native PNG or equivalent lossless indexed image at `256x192`;
- standard `6912`-byte `.scr` representation when the workflow supports it;
- native animated GIF when FLASH cells are used;
- nearest-neighbour preview/export at `1024x768` (`4x` linear scale);
- a validation result stating dimensions, palette, CELL validity, brightness
  validity, FLASH validity, and `.scr` round-trip status.

Do not claim ZX Spectrum 48K authenticity unless every mandatory validation has
passed.
