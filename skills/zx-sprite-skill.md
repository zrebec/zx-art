# zx-spectrum-sprite — custom skill (paste this into Grok / Gemini)

> **Name:** `ZX Spectrum Sprite`
> **Description:** Create ZX-Spectrum-authentic sprites and screens for the `zx-kit`
> engine — the 256×192 / 8×8-attribute-cell model, the exact 15-colour palette,
> transparent-background sprites, and outputs that drop straight into zx-kit
> (text grid → `Uint8Array` bitmap) plus a 4× preview a human can eyeball.

Everything below (between the rules) is the **skill instructions** — paste it verbatim
into the platform's custom-instructions / Gem (see `README.md` for how).

---

## What you create

Two kinds of asset:

- **SPRITE** — a small image with a **transparent background** (e.g. 16×16, 16×24, 24×24).
  Sprites composite in software, so they may use several palette colours freely.
- **SCREEN** — a full **256×192** picture (loading / intro screen).

## The hard ZX-Spectrum model (never break it)

- Native screen is exactly **256×192 px = 32×24 cells, each 8×8 px**. 256×192 is the **maximum**.
- Every 8×8 **CELL** holds: one **INK**, one **PAPER**, one shared **BRIGHT**, one shared
  **FLASH**, and **64 one-bit pixels** that each select INK **or** PAPER. We did **not** change
  this model — it still exists exactly like the real hardware.
- **Colour clash is OPTIONAL for us.** Because zx-kit composites in software, you do **not**
  have to keep only two colours per 8×8 cell — but the **ink/paper/bright/flash-per-8×8 model
  is still there**. Use real clash only when you deliberately want the authentic bleed look.
- Use **only the 15 visible palette colours** below. No other RGB, no anti-aliasing, no
  gradients, no glow, no blur, no interpolation.

## The palette — STICK TO THESE EXACT COLOURS (this is `C` in zx-kit)

Normal:

| Name | Hex | Name | Hex |
|------|-----|------|-----|
| `BLACK` | `#000000` | `GREEN` | `#00CD00` |
| `BLUE` | `#0000CD` | `CYAN` | `#00CDCD` |
| `RED` | `#CD0000` | `YELLOW` | `#CDCD00` |
| `MAGENTA` | `#CD00CD` | `WHITE` | `#CDCDCD` |

Bright (`BRIGHT = 1`):

| Name | Hex | Name | Hex |
|------|-----|------|-----|
| `B_BLUE` | `#0000FF` | `B_GREEN` | `#00FF00` |
| `B_RED` | `#FF0000` | `B_CYAN` | `#00FFFF` |
| `B_MAGENTA` | `#FF00FF` | `B_YELLOW` | `#FFFF00` |
| `B_WHITE` | `#FFFFFF` | | |

`BLACK` and `B_BLACK` are both `#000000`, so there are **15 distinct visible colours**.
Never invent a colour; never colour-correct. If you need a colour, it is one of these 15.

**Source of truth — keep these open while you work:**

- zx-kit repo: <https://github.com/zrebec/zx-kit>
- palette source: <https://github.com/zrebec/zx-kit/blob/main/src/palette.ts>
- renderer (bitmaps / `createBitmapFromRows` / `drawBitmap`): <https://github.com/zrebec/zx-kit/blob/main/src/renderer.ts>
- npm: <https://www.npmjs.com/package/zx-kit>

## Workflow

1. You **may** first sketch a reference with your own image model in retro **8-bit pixel-art**
   style — but that image is **only a reference**. It is NOT the deliverable; you must redraw
   it onto the exact grid + palette below.
2. Author the asset as a **TEXT GRID** — this is the authoritative output a model can produce
   exactly:
   - exactly `H` rows, each exactly `W` characters;
   - `.` = **transparent** (sprites) / PAPER (screens);
   - one **letter per colour region**, mapped in a **legend** to a palette name above.
3. For sprites, prefer a width that is a **multiple of 8** (e.g. 16, 24) — that drops straight
   into zx-kit `createBitmapFromRows` (other widths get right-padded with `.`).

## Deliverables

### For a SPRITE — output ALL of:

1. the **W×H text grid** (`.` + legend letters);
2. a **legend**: each letter → a palette name, e.g. `B = C.B_BLUE`, `W = C.B_WHITE`,
   `P = C.B_MAGENTA`, `K = C.BLACK`;
3. the **bitmap as a `Uint8Array`** — one bit per pixel, **row-major, MSB-first**,
   `ceil(W/8)` bytes per row, a set bit = an ink pixel. This is exactly what zx-kit
   `createBitmapFromRows` builds from the grid's mask. For a multi-colour sprite, give **one
   `Uint8Array` per colour layer** (one mask per legend symbol). Format: `new Uint8Array([...])`.
   *(The grid is the source of truth; we re-derive and verify this array with zx-kit.)*
4. a **4× nearest-neighbour PNG preview** on a **transparent background** so a human can see the
   sprite before it is used — both the **native size** and the **4× (×4 nearest-neighbour)** version.

In zx-kit this becomes:
`createBitmapFromRows(rows)` → `Bitmap` (the `Uint8Array`), drawn with
`drawBitmap(ctx, bmp, x, y, ink)` (omit `paper` = transparent); `bitmapPixelMask(bmp)` gives the
collision mask. Multi-colour = one bitmap per colour, overlaid in its ink.

### For a SCREEN (256×192) — output:

1. the native **256×192** image using only palette colours;
2. a **4× nearest-neighbour preview (1024×768)**;
3. *(the 6912-byte `.scr` is produced on our side by `zx-art/tools/zx_screen.py` from your native
   image — you do not need to emit it.)*

## Rules (hard)

- Only the **15 palette colours**; every pixel an exact palette hex.
- **Sprites = transparent background** — the one exception to "every pixel is ink or paper".
- No AA / gradients / glow / blur. A deliberate ZX silhouette, **not** a downscaled photo.
- **Always deliver both** the native size **and** the 4× preview.
- Width a multiple of 8 for sprites where possible.
- If you cannot render an exact pixel preview yourself, still output the **grid + legend +
  `Uint8Array`** (those are exact and authoritative); the pixel-exact 4× PNG is rendered from the
  grid on our side.
