> **Status: implemented.** This began as a request to extend the `zx-spectrum-screen`
> skill and is now shipped — sprite mode is in the skill and `tools/zx_sprite.py`
> exists. It is kept as the specification the implementation answers to. See
> `README.md` §1 and §5.3 for how it works today.

ADD TO THE zx-spectrum-screen SKILL — a new "Sprite mode" (keep the 256×192 SCR
"screen mode" exactly as-is).

A SPRITE is not a screen. For sprites do NOT emit a .scr, do NOT enforce 256×192,
the 15-colour global cap, or the 2-colours-per-8×8 attribute-clash rule. Sprites
composite over the scene in software, so transparency is allowed and a sprite may
use several of the 15 ZX colours freely (clash does not apply to sprites).

Sprite deliverable:
1. size in px (small; e.g. 16×16 or 16×24).
2. a TEXT GRID: exactly H rows, each exactly W chars; characters are
   `.` = transparent, plus one letter per colour region.
3. a LEGEND: every non-dot symbol → a zx-kit palette constant (BLACK, BLUE, RED,
   MAGENTA, GREEN, CYAN, YELLOW, WHITE and the B_ bright variants). Only these.
4. optional: a transparent-background preview PNG at native size + a 4×
   nearest-neighbour preview. NO .scr for sprites.

Rules: only the 15 ZX palette colours; no AA/gradients; every row exactly W chars,
exactly H rows, only `.` and legend symbols. Design a deliberate, readable ZX
sprite silhouette — not a downscaled photo.

Add scripts/zx_sprite.py that: validates a rows.txt (W×H, only `.`+legend symbols),
renders the transparent-bg preview + 4× preview, and emits {w,h,rows,legend} as JSON.

Format example (8×8, format only — NOT the bunny):
..XXXX..
.XWWWWX.
.XWBBWX.
.XWBBWX.
.XWWWWX.
..XXXX..
...XX...
........
legend: X=C.BLACK  W=C.B_WHITE  B=C.B_BLUE

Note: For 16×16, `imagegen` → `quantize` is unreliable (too few pixels) — the most accurate approach is to have the model generate the grid manually (it can use `imagegen` to create a reference, but will overwrite the final result with the grid).

The results always save in `outputs` sub-directory in this dir.