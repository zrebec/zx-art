# ZX Spectrum Image Generation

## Purpose

Create, convert, edit, or optimize raster images that comply with the graphical constraints of the ZX Spectrum.

This skill MUST be used whenever the user asks to:

* create a ZX Spectrum image
* create ZX Spectrum pixel art
* create a ZX Spectrum sprite
* create a game asset for ZX Spectrum
* create a tile, icon, character, object, background, or UI element for ZX Spectrum
* convert an existing image to ZX Spectrum graphics
* apply ZX Spectrum dithering
* reduce an image to the ZX Spectrum palette
* optimize an image for ZX Spectrum attribute-cell limitations
* generate graphics specifically targeting ZX Spectrum hardware constraints

The skill accepts either:

1. A textual image description/prompt
2. An input/reference image supplied by the user

The final output MUST satisfy every hard technical constraint defined in this document.

---

## Hard Constraints

These constraints are NON-NEGOTIABLE.

### 1. Image Dimensions

The final image MUST satisfy:

```text
1 <= WIDTH  <= 256
1 <= HEIGHT <= 192
```

The image does NOT have to be exactly 256×192.

Smaller images are explicitly supported and SHOULD be used for game assets such as:

* sprites
* characters
* enemies
* objects
* icons
* tiles
* UI elements

Examples:

```text
256 × 192   full-screen image
16 × 16     tile / small sprite
16 × 24     sprite
24 × 32     character
32 × 32     object
```

The user's requested dimensions SHOULD be preserved whenever possible.

Do NOT upscale a small asset to 256×192 unless explicitly requested.

---

### 2. Allowed Color Palette

Every pixel MUST use a color from the ZX Spectrum palette defined in:

```text
references/palette.md
```

The complete allowed RGB palette is:

```text
#000000
#0000CD
#CD0000
#CD00CD
#00CD00
#00CDCD
#CDCD00
#CDCDCD
#0000FF
#FF0000
#FF00FF
#00FF00
#00FFFF
#FFFF00
#FFFFFF
```

There are 15 unique RGB colors.

`BLACK` and `B_BLACK` have the same RGB value and therefore count as one unique color.

The image MUST NOT contain any other RGB value.

Forbidden:

* anti-aliasing
* alpha blending
* transparency
* semi-transparent pixels
* interpolated colors
* gradients containing non-palette colors
* arbitrary RGB approximations
* colors introduced by image scaling
* colors introduced by post-processing
* subpixel rendering
* smooth shading using non-palette colors

Every pixel must have exactly one allowed RGB color.

---

### 3. Maximum Global Color Count

The image MUST contain no more than 15 unique RGB colors.

Formally:

```text
unique_colors(image) <= 15
```

Because the allowed palette contains exactly 15 unique RGB colors, this condition is automatically satisfied when the palette constraint is satisfied.

It MUST nevertheless be checked by the validator.

---

### 4. 8×8 Attribute Cell Constraint

The image is divided into 8×8 pixel attribute cells starting at coordinate `(0, 0)`.

For every cell:

```text
unique_colors(cell) <= 2
```

A cell MUST contain at most two distinct RGB colors.

This is the most important graphical constraint after the palette restriction.

For images whose width or height is not divisible by 8, partial cells at the right and/or bottom edges are valid.

The same two-color limit applies to partial cells.

Examples:

```text
Image: 16 × 16
Cells: 2 × 2

Image: 20 × 20
Cells:
- x=0..7
- x=8..15
- x=16..19

and equivalent Y ranges
```

Do NOT ignore partial cells.

---

# Input Handling

## Text Prompt

When the user provides only a textual description:

1. Understand the requested subject.
2. Determine the intended asset type.
3. Determine or infer suitable dimensions.
4. Construct the artwork with ZX Spectrum constraints in mind from the beginning.
5. Use only the allowed palette.
6. Keep every 8×8 cell within the two-color limit.
7. Validate the final image.
8. If validation fails, correct the image and validate again.

Do NOT first create a normal unrestricted RGB image and assume it can simply be converted afterwards.

The ZX Spectrum limitations MUST influence the visual design from the beginning.

---

## Reference Image

When the user supplies an input/reference image:

1. Analyze the source image.
2. Identify the important subject, silhouette, composition, and details.
3. Determine appropriate target dimensions.
4. Reduce or scale the image if necessary.
5. Map colors to the allowed ZX Spectrum palette.
6. Resolve all 8×8 attribute-cell conflicts.
7. Apply dithering where useful.
8. Validate the result.
9. Correct all validation failures.
10. Validate again.

Preserve recognizability and important visual information over exact reproduction of colors that cannot exist on the ZX Spectrum.

---

# Dithering

Dithering MAY be used to approximate visual tones that cannot be represented directly by the palette.

However:

**Dithering MUST NEVER introduce a third color into an 8×8 cell.**

For each cell:

1. Select zero, one, or two palette colors.
2. If two colors are selected, dithering may alternate only between those two colors.
3. Never introduce a third color.
4. Validate the cell after dithering.

Possible techniques include:

* ordered dithering
* Bayer dithering
* controlled pixel patterns
* structured pixel clusters
* adapted error diffusion

Dithering SHOULD be selective.

Do NOT add noise simply to make an image appear more "retro".

Prefer large coherent pixel clusters and readable shapes.

---

# Pixel-Art Design Principles

The result should look intentionally designed for ZX Spectrum rather than like a modern image degraded by aggressive color reduction.

Prefer:

* strong silhouettes
* readable shapes
* deliberate pixel clusters
* high contrast
* intentional palette selection
* clean edges
* controlled dithering
* meaningful details
* clear separation between foreground and background

Avoid:

* unnecessary single-pixel noise
* excessive dithering
* blurry edges
* anti-aliasing
* smooth modern gradients
* photographic shading
* accidental checkerboard patterns
* visually noisy textures

When detail and readability conflict, prioritize readability.

---

# Attribute Cell Strategy

Treat every 8×8 cell as an independent color-constrained region.

For each cell:

1. Identify the most important visual content.
2. Determine which colors are visually necessary.
3. Select no more than two palette colors.
4. Render the cell using only those colors.
5. Verify the cell.

Adjacent cells MAY use completely different color pairs.

Do NOT unnecessarily force neighboring cells to share the same color pair.

This allows the image to use the available palette more effectively while respecting the attribute-cell limitation.

---

# Scaling

When scaling an image:

* Never allow interpolation to create non-palette colors.
* Prefer nearest-neighbor scaling for pixel-art preservation.
* If the source exceeds 256×192, reduce it to fit.
* Re-check palette and attribute-cell constraints after scaling.

Any scaling operation MUST be followed by validation.

---

# Validation Is Mandatory

Validation is NOT optional.

A generated or converted image MUST NOT be considered complete until it has passed:

```text
scripts/validate.py
```

The validator is the authoritative source of truth for technical validity.

Do NOT rely on visual inspection alone.

When Python execution is available, the agent MUST run the validator.

Example:

```bash
python scripts/validate.py output.png
```

If the validator reports an error:

1. Identify the violation.
2. Correct the image.
3. Run the validator again.
4. Repeat until validation succeeds.

Do NOT return an image that has failed validation.

---

# Validation Requirements

The validator MUST verify:

## Dimensions

```text
1 <= WIDTH <= 256
1 <= HEIGHT <= 192
```

## Color Mode

The image MUST contain explicit RGB pixels.

Images with:

* alpha channels
* palette/transparency modes
* grayscale pixels
* CMYK pixels
* other non-RGB representations

MUST be rejected unless they are explicitly converted to valid RGB pixels before validation.

The resulting RGB pixels must still be validated against the allowed palette.

## Palette

Every pixel MUST be one of the 15 allowed RGB colors.

## Global Colors

```text
unique_colors(image) <= 15
```

## Attribute Cells

For every 8×8 cell:

```text
unique_colors(cell) <= 2
```

Partial cells MUST also be checked.

---

# Validator Failure Handling

The validator SHOULD produce actionable diagnostics.

Example:

```text
INVALID IMAGE

Cell: (17, 8)
Pixel bounds: x=136..143, y=64..71

Colors found: 3
Maximum allowed: 2

Colors:
  #000000
  #CD0000
  #00CD00
```

The agent should use these coordinates to identify and correct the offending region.

---

# Final Verification Checklist

Before considering the task complete:

* [ ] Width <= 256
* [ ] Height <= 192
* [ ] Width >= 1
* [ ] Height >= 1
* [ ] RGB image
* [ ] No alpha/transparency
* [ ] Every pixel uses an allowed palette color
* [ ] No more than 15 unique colors
* [ ] Every 8×8 cell contains at most 2 colors
* [ ] Partial cells are also valid
* [ ] Dithering does not introduce invalid colors
* [ ] Important shapes remain recognizable
* [ ] Dimensions are appropriate for the requested asset
* [ ] `scripts/validate.py` has been executed
* [ ] Validator returned success

Only after all checks pass may the image be considered valid ZX Spectrum output.

---

# Constraint Priority

When visual fidelity conflicts with a hard technical constraint:

```text
TECHNICAL VALIDITY
        >
RECOGNIZABILITY
        >
DETAIL
        >
VISUAL FIDELITY
```

Never violate a hard constraint merely to improve visual appearance.

If necessary:

1. Simplify secondary details.
2. Reduce colors.
3. Change dithering.
4. Simplify shapes.
5. Modify composition.
6. Preserve the technical constraints.

Never silently relax a constraint.
