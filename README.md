<!-- markdownlint-disable MD013 -->

# zx-art

The graphics pipeline for the retro ecosystem. It is not a library and not a game: it is the
place where artwork becomes something a ZX Spectrum could actually have held in memory, and the
place that can prove it.

It is the visual twin of [`zxplayer`](../zxplayer). That project feeds the *sound* half of
[`zx-kit`](../zx-kit) with AY register dumps; this one feeds the *picture* half with `.scr`
screens and sprite grids. Both directions of the same idea — the asset carries the hardware's
constraints, so the game does not have to enforce them at runtime.

---

## 1. The one distinction everything follows from

A **screen** and a **sprite** are different objects, and almost every mistake this project has
made came from applying one's rules to the other. A **tileset** sits between them: authored like
a sprite, obeying a screen's cell rule.

|  | Screen mode | Sprite mode | Tileset mode |
|---|---|---|---|
| What it is | A whole 48K display, exactly as the machine stored it | A small object composited over a scene in software | Square background pieces a game lays on a grid to build a room |
| Size | Always `256×192` | Whatever you choose — `16×24`, `32×32`, `40×64` | One size per set, a multiple of 8 — `8×8`, `16×16` |
| File | `.scr`, exactly `6912` bytes | `.json`, a text grid plus a legend | `.json`, one shared legend plus named grids |
| Two colours per `8×8` cell | **Enforced.** It is a property of the format | **Not applicable.** A sprite has no attribute block | **Enforced**, cell by cell, by the screen's own test |
| Global colour cap | 15 | None | None per set; 15 is the palette anyway |
| Transparency | Impossible | Required (`.` in the grid) | **Forbidden** — background is opaque |
| Attribute clash | Preserved deliberately — it is the look | Does not exist | Cannot occur *inside* a tile; sprites drawn over tiles are the game's business |
| Authoring | Convert a concept image, then hand-repair cells | Write the grid by hand | Write the grid by hand |

The last row is the practical one. A concept image downscaled to `256×192` and quantised is a
usable *starting point* for a screen, because a screen has 49 152 pixels and a mistake in one cell
is a cell. The same procedure at `16×24` produces 384 pixels of noise. **Small sprites are
authored as text, not converted.** Image generation may provide a reference for the pose; it never
provides the final grid.

Why a tileset enforces the cell rule a sprite is free of: a tile whose size is a multiple of 8,
laid on a grid of that size, puts every `8×8` cell of the room inside exactly one tile. If every
cell of every tile is legal, **every room built from the set is a picture the machine could
display** — checked once, per tile, instead of per room.

---

## 2. The hardware, precisely

Everything below is what the encoder and validator actually implement, not a summary of folklore.

### 2.1 The display

The standard screen is `256×192` pixels covered by a `32×24` grid of `8×8` **attribute cells** —
768 of them. A pixel is one bit. That bit does not choose a colour; it chooses whether the pixel
takes its cell's **INK** or its cell's **PAPER**. Colour therefore has one-eighth the horizontal
resolution and one-eighth the vertical resolution of shape.

That is the entire origin of **attribute clash**: two objects of different colours that overlap
inside one cell cannot both keep their colour, so one of them changes. The rule in this repository
is that clash is **preserved, never concealed** — introducing a third colour into a cell to hide it
is not a fix, it is a picture the machine could not display.

### 2.2 The attribute byte

One byte per cell, 768 of them, laid out most-significant bit first:

```text
bit  7     6      5  4  3     2  1  0
     FLASH BRIGHT  PAPER (0-7)  INK (0-7)
```

Three bits for INK and three for PAPER is the fact the whole project rests on. **Three bits are
eight values.** There is no bit pattern that names a ninth colour, no way to store two INKs in one
cell, and no way to give one cell two brightness levels. A `.scr` cannot smuggle in a 32-colour
image or a soft gradient the way a PNG can — not because a check rejects it, but because the
format has nowhere to put it.

`FLASH` swaps INK and PAPER roughly twice a second. `BRIGHT` selects a brightness bank, and the
bank is per *cell*, not per pixel: a cell's INK and PAPER are both normal or both bright.

### 2.3 The palette

Eight hues in two banks. Normal uses `0xCD` where bright uses `0xFF`:

| Index | Normal | Bright |
|---:|---|---|
| 0 | `#000000` BLACK | `#000000` BLACK |
| 1 | `#0000CD` BLUE | `#0000FF` B_BLUE |
| 2 | `#CD0000` RED | `#FF0000` B_RED |
| 3 | `#CD00CD` MAGENTA | `#FF00FF` B_MAGENTA |
| 4 | `#00CD00` GREEN | `#00FF00` B_GREEN |
| 5 | `#00CDCD` CYAN | `#00FFFF` B_CYAN |
| 6 | `#CDCD00` YELLOW | `#FFFF00` B_YELLOW |
| 7 | `#CDCDCD` WHITE | `#FFFFFF` B_WHITE |

Sixteen codes, **fifteen visible colours** — black is identical in both banks. That is why the
validator's cap is 15 and not 16, and why a screen reported as "9/15 colours" is not missing
anything.

### 2.4 Screen memory is not in reading order

The 6144 bitmap bytes come first, then the 768 attribute bytes. Within the bitmap, the vertical
coordinate is interleaved. Writing `y` as three fields — `TT` the third of the screen, `SSS` the
character row within that third, `RRR` the pixel row within the character:

```text
y      = 0bTT_SSS_RRR
offset = TT  * 2048        # (y & 0b11000000) << 5
       + RRR * 256         # (y & 0b00000111) << 8
       + SSS * 32          # (y & 0b00111000) << 2
       + x_byte
```

Consecutive addresses therefore walk down the *same* character row of all 32 columns, then jump to
the next pixel row. This is the reason a half-loaded Spectrum screen filled in those characteristic
bands rather than top to bottom, and `tools/zx_screen.py` undoes it on decode so the rest of the
pipeline sees ordinary rows.

---

## 3. What is committed, and the measurement behind it

**One file per artwork is the truth. Everything else is a build product.**

- A screen *is* its `.scr`.
- A sprite *is* its `.json` — `{w, h, rows, legend}`.
- A tileset *is* its `.json` — `{tile, legend, tiles: {name: rows}}`.

All three are complete. The proof is not an argument, it is a check that runs:

```console
$ python3 tools/zx_art.py verify
ok   art/icehaul/screens/icehaul-loading.scr — 256x192, 9 colours
...
6 screens, 15 sprites, 1 tilesets, 0 failed
```

For a screen, `verify` decodes the `.scr` to an image and encodes that image again, and requires
the result to be **byte-identical to the file it started from**. The `.scr` is a fixed point of the
codec. A PNG stored beside it could therefore carry no information the `.scr` does not, which is
the entire reason none is stored.

This was measured before anything was deleted. The 34 PNGs that used to be committed were rebuilt
from the `.scr` and `.json` sources alone and compared pixel by pixel against the originals:
**34 of 34 identical, 0 differing.** The `1024×768` previews are likewise exactly a `4×`
nearest-neighbour resize of the native image, so they are two derivations away from the source and
still exact.

### The three kinds of file

| Kind | Committed | Why |
|---|---|---|
| `art/*/screens/*.scr`, `art/*/sprites/*.json`, `art/*/tiles/*.json` | **yes** | The artwork. Nothing else can reproduce them |
| `art/*/concept/*.png` | **yes** | The generated image a screen was composed from. It is an *input*, not a render — re-running a generator produces a different picture, so this is the only irreproducible provenance we have |
| `build/**` | **no** | Every pixel is a function of the two rows above. `.gitignore`d |

Committed renders are exactly what produced two rival output directories in the first place — see
§8.

---

## 4. Layout

```text
zx-art/
├── art/                        the only committed output tree
│   ├── icehaul/
│   │   ├── screens/            *.scr        — 6912 bytes each
│   │   ├── sprites/            *.json       — {w, h, rows, legend}
│   │   ├── tiles/              *.json       — {tile, legend, tiles}   (chaosbunny today)
│   │   └── concept/            *.png        — generated composition reference
│   ├── minefield/
│   ├── chaosbunny/
│   └── sandbox/                not owned by a game: tests, studies, one-offs
├── build/                      gitignored; written by `zx_art.py build`
├── tools/
│   ├── zx_screen.py            screen: validate · encode · decode · upscale · gif
│   ├── zx_cell_quantize.py     concept image → hardware-valid 256×192
│   ├── zx_sprite.py            sprite: validate a text grid → JSON + previews
│   ├── zx_art.py               the driver: verify · build · manifest
│   └── design_*.py, make_*.py  one-off generators kept as worked examples
├── skills/                     agent-facing instructions (see §7)
├── AGENTS.md                   the screen-mode hardware rules, in full
├── SPRITES.md                  the sprite-mode specification
└── MANIFEST.md                 generated inventory — never hand-edited
```

`sandbox/` is deliberate. A white cat, a rainbow unicorn and a fashion editorial are not assets of
any game; they are the pictures that proved the pipeline works on a photograph, on flat colour, and
on a two-colour subject. Keeping them out of the game directories means a project folder lists
exactly what that project ships.

---

## 5. The tools

All four need Python 3 and [Pillow](https://python-pillow.org). Nothing else.

### 5.1 `zx_screen.py` — the screen codec

```console
python3 tools/zx_screen.py validate native.png            # is this displayable at all?
python3 tools/zx_screen.py encode  native.png screen.scr  # → 6912 bytes
python3 tools/zx_screen.py decode  screen.scr decoded.png
python3 tools/zx_screen.py upscale native.png preview.png # 4× nearest neighbour
python3 tools/zx_screen.py gif     screen.scr preview.gif # two 320 ms FLASH phases
```

`validate` is the interesting one. It refuses an image that is not `256×192`, that contains a
colour outside the 15, that uses more than 15, that puts more than one INK and one PAPER in a cell,
or that mixes brightness banks within a cell. It then encodes and decodes and requires a
pixel-exact round trip. `encode` takes FLASH separately via `--flash-map` (24 rows × 32 booleans),
because a PNG has no bit for it.

### 5.2 `zx_cell_quantize.py` — concept image to native

```console
python3 tools/zx_cell_quantize.py concept.png native.png \
    --brightness auto --resize cover
```

This is a **cell-aware** quantiser, and the distinction matters. Ordinary whole-image palette
reduction picks the best 15 colours globally and will happily leave four of them inside one `8×8`
cell — the result looks like a Spectrum and cannot be encoded as one. This tool solves each cell
independently for the (BRIGHT, INK, PAPER) triple and the 64 bits that best reproduce it.

`--brightness` chooses the bank: `auto` per cell, `normal` for deliberately dark scenes, `bright`
when the whole converted palette should be bright. `--resize` is `cover` (crop to 4:3), `contain`
(letterbox) or `stretch`.

Treat the output as a **starting point**. The conversion is where silhouettes die: check that the
subject still reads, then hand-repair the cells that lost it, then validate.

### 5.3 `zx_sprite.py` — the sprite validator

```console
python3 tools/zx_sprite.py rows.txt \
    --width 40 --height 64 \
    --legend K=C.BLACK R=C.RED U=C.B_BLUE W=C.B_WHITE \
    --name player-road-train-straight \
    --out art/icehaul/sprites --json-only
```

`rows.txt` is exactly `height` lines of exactly `width` characters, where `.` is transparent and
every other character is an ASCII letter present in the legend. The legend maps each letter to one
`zx-kit` palette constant — the same names the game imports, so the grid and the code cannot drift
apart.

It validates everything *before* writing anything. `--out` chooses the directory (default
`./outputs`); `--json-only` skips both PNGs, because they are derivable and this repository builds
them on demand.

### 5.4 `zx_art.py` — the driver

```console
python3 tools/zx_art.py verify      # check every source under art/; non-zero on failure
python3 tools/zx_art.py build       # render art/ → build/  (add --gif for FLASH screens)
python3 tools/zx_art.py manifest    # write MANIFEST.md
```

`verify` is the gate. It walks `art/`, applies §3's fixed-point check to every screen, the grid
rules to every sprite, and to every tile the grid rules plus two more — no `.`, and each `8×8`
cell passes `zx_screen.infer_cell`, the exact function the screen encoder uses. It reports notes
that are not failures — for example a pose that does not use every symbol in its family's shared
legend. A failing tile is named with its cell: `tile 'floor': CELL (0,0) mixes normal and BRIGHT
colours`.

`manifest` writes `MANIFEST.md` from those measurements, so the inventory cannot be stale in a way
the tool cannot see. Every column — size, byte count, colour count, bright and flash cell counts,
the legend, the check result — is read off the file it names. This is the fix for validation
results that previously lived in a text file next to some assets and in the author's memory for the
rest.

---

## 6. The three workflows

### Screen

```text
concept.png            generated or drawn, any size, any colours
   │  zx_cell_quantize.py --resize cover
   ▼
native.png             256×192, every cell legal
   │  hand repair — the step that decides whether it is good
   │  zx_screen.py validate
   ▼
name.scr               6912 bytes  →  art/<project>/screens/
   │  zx_art.py verify           the fixed-point proof
   │  zx_art.py build            previews, when a human needs to look
   ▼
game                   see §9
```

Keep `concept.png` in `art/<project>/concept/`. Everything after `native.png` is reproducible;
the concept is not.

### Sprite

```text
reference (optional)   a generated image, used only to decide the pose
   │  write the grid by hand
   ▼
rows.txt               H lines × W chars, '.' plus legend letters
   │  zx_sprite.py --json-only --out art/<project>/sprites
   ▼
name.json              {w, h, rows, legend}  →  the sprite, complete
   │  zx_art.py verify / build
   ▼
game                   as a bitmap, or as generated TypeScript
```

`rows.txt` is not committed: it is `json["rows"]`, and keeping two copies of a grid is how they
come to disagree.

### Tileset

```text
the room's needs       which surfaces must a player tell apart at a glance?
   │  write each tile by hand, two colours per 8×8 cell, one bank per cell
   ▼
name.json              {tile, legend, tiles}  →  art/<project>/tiles/
   │  zx_art.py verify           grid + opacity + the screen's cell test
   │  zx_art.py build            a contact sheet, tiles one transparent pixel apart
   ▼
game                   lays the tiles on its own grid
```

A tileset has no `zx_sprite.py` step: one file holds the whole family, so there is no per-tile
`rows.txt` to convert. Keep a set's legend small — one bank per cell is easy to break by accident
when a set grows, and `verify` names the tile and the cell when it happens.

---

## 7. The agent skill, and how it stays in sync

Most artwork here is produced by an agent following a skill. Three scripts are shared between this
repository and the installed skill, and **the repository is canonical**:

```console
cp tools/zx_screen.py tools/zx_cell_quantize.py tools/zx_sprite.py \
   ~/.codex/skills/zx-spectrum-screen/scripts/
cp AGENTS.md ~/.codex/skills/zx-spectrum-screen/references/hardware-rules.md
```

Drift here is not hypothetical. Before this was written down, the repository held two of the three
scripts and the skill held all three — so `zx_sprite.py` existed and worked for two months while a
cross-project task list recorded it as unwritten. If you change a script, copy it; if you change
`AGENTS.md`, copy it.

`skills/` in this repository holds the agent-facing instructions themselves: the hardware rules
(`AGENTS.md`, mirrored as the skill's `references/hardware-rules.md`) and the sprite-mode
specification (`SPRITES.md`).

---

## 8. Why there used to be two output directories

Worth recording, because the cause was structural rather than careless.

`zx_sprite.py` wrote to `./outputs` — hardcoded, and documented as "run it from the directory where
you want the `outputs` directory". The screen half of the pipeline wrote to
`output/zx-spectrum-screen/`, named after the skill that produced it. Two tools, two hardcoded
conventions, two spellings of the same English word, and no one ever decided anything. On top of
that the sprite tool used `snake_case` filenames and the screen tool `kebab-case`.

What the merge cost: **176 KB of derived PNGs** (regenerated exactly, §3) and **~200 KB of stale
generated TypeScript** — delivery copies of `playerTruck.ts` and `truck.ts` that Ice Haul had since
edited, so the copies here were quietly *older* than the game and would have been wrong to copy
back. Generated code now leaves through a patch and lives in the game; this repository keeps the
art.

What it gained beyond tidiness: four of the five road-train poses had a `rows.txt` and a PNG but no
legend, so their colours existed only inside a PNG. They now have JSON like every other sprite,
sharing the pose family's legend.

---

## 9. Consumers

**Ice Haul** ships `art/icehaul/screens/icehaul-loading.scr` inside its bundle. The route is:

```console
node scripts/screen-import.mjs src/assets/icehaul-loading.scr --write
```

which emits a TypeScript module holding the 6912 bytes as base64, decoded once at import with
`parseSCR()` from `zx-kit` (0.46+) and drawn with `drawBitmapAttrs`.

Inlining rather than fetching is deliberate and was a bug fix. The previous version loaded a PNG
and gated the scene on `image.complete && image.naturalWidth > 0`; a missing file left the player
on a black screen that never accepted a keypress — not a crash, not an error, a silently frozen
game. A module cannot half-arrive.

**Sprites** reach a game either as a bitmap built from the grid at runtime, or as generated
TypeScript checked into the game repository. Once generated code lands in a game, the game owns it.

---

## 10. House rules

1. **A PNG is never a shipped asset.** It is an input to the pipeline or a picture for a human to
   look at. What ships is `.scr` and `.json`.
2. **Never conceal clash.** A third colour in a cell is not a repair.
3. **Do not derive a small sprite by downscaling.** Write the grid.
4. **`verify` must pass before anything is committed**, and `manifest` regenerated with it.
5. **Sample even rows when validating a screenshot of a running game.** Games here draw scanlines
   over odd device rows; a validator that ignores this measures the overlay and reports faults that
   do not exist.
6. **The repository is canonical for the skill scripts** (§7).
