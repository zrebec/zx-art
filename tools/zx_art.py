#!/usr/bin/env python3
"""Verify, render and inventory the ``art/`` tree.

``art/`` holds one file per artwork and nothing else. A screen is its ``.scr``;
a sprite is its ``.json`` text grid; a tileset is one ``.json`` holding a family
of opaque text-grid tiles. Every PNG this project has ever shipped is a
*function* of one of those files, so PNGs are built into ``build/`` on demand
and never committed.

This driver is the thing that makes that claim checkable:

``verify``    every ``.scr`` is a fixed point of decode/encode, every sprite grid
              matches its legend, every tile is opaque and every ``8x8`` cell of
              it is one a screen could hold. Exits non-zero on any failure.
``build``     renders ``build/<project>/<mode>/`` from ``art/``.
``manifest``  writes ``MANIFEST.md`` from measurements, not from memory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterator, NamedTuple

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zx_screen  # noqa: E402
import zx_sprite  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
ART = REPO / "art"
BUILD = REPO / "build"
MANIFEST = REPO / "MANIFEST.md"

#: The 4x nearest-neighbour preview is the one every skill and note refers to.
PREVIEW_SCALE = 4


class Asset(NamedTuple):
    """One row of the inventory: a source file plus everything measured from it."""

    project: str
    mode: str  # "screen" | "sprite" | "tileset"
    name: str
    source: Path  # relative to the repo root
    size: str  # "256x192", "40x64", or a tileset's tile size "16x16"
    bytes_on_disk: int
    colours: int
    detail: str  # mode-specific: cell/flash counts, or the legend
    status: str  # "PASS" or "FAIL: ..."
    note: str = ""  # worth printing, but not a failure


def _iter_sources(root: Path) -> Iterator[tuple[str, str, Path]]:
    """Yields ``(project, mode, path)`` for every source file, in a stable order."""
    for project_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for mode, pattern in (
            ("screen", "screens/*.scr"),
            ("sprite", "sprites/*.json"),
            ("tileset", "tiles/*.json"),
        ):
            for path in sorted(project_dir.glob(pattern)):
                yield project_dir.name, mode, path


def _flash_map(screen: bytes) -> list[list[bool]]:
    """Reads FLASH back out of the attribute block.

    ``zx_screen.encode`` takes the FLASH map as a separate argument because it
    encodes from a PNG, which has no bit for it. Re-encoding a ``.scr`` with an
    all-false map would therefore *drop* FLASH and make a legitimate screen look
    like a round-trip failure. None of today's six screens use it; this is here so
    the invariant keeps holding on the day one does.
    """
    attrs = screen[zx_screen.BITMAP_BYTES :]
    return [
        [bool(attrs[row * zx_screen.COLS + col] & 0x80) for col in range(zx_screen.COLS)]
        for row in range(zx_screen.ROWS)
    ]


def check_screen(path: Path) -> tuple[Asset, object]:
    """Decodes a ``.scr`` and proves it is a fixed point of the codec.

    The interesting direction is ``scr -> image -> scr``, not the other way round.
    A PNG that survives encoding only shows the *converter* behaved; a ``.scr``
    that re-encodes byte-identically shows the file on disk is the whole truth and
    the PNG next to it would carry no information the ``.scr`` does not.
    """
    project = path.parent.parent.name
    raw = path.read_bytes()
    status = "PASS"
    image = None
    colours = 0
    flash = bright = 0

    if len(raw) != zx_screen.SCREEN_BYTES:
        status = f"FAIL: {len(raw)} bytes, expected {zx_screen.SCREEN_BYTES}"
    else:
        attrs = raw[zx_screen.BITMAP_BYTES :]
        flash = sum(1 for a in attrs if a & 0x80)
        bright = sum(1 for a in attrs if a & 0x40)
        try:
            image = zx_screen.decode(raw)
            colours = len(set(image.getdata()))
            zx_screen.analyse(image)
            if zx_screen.encode(image, _flash_map(raw)) != raw:
                status = "FAIL: re-encode is not byte-identical"
        except zx_screen.ScreenError as error:
            status = f"FAIL: {error}"

    return (
        Asset(
            project=project,
            mode="screen",
            name=path.stem,
            source=path.relative_to(REPO),
            size=f"{zx_screen.WIDTH}x{zx_screen.HEIGHT}",
            bytes_on_disk=len(raw),
            colours=colours,
            detail=f"{zx_screen.COLS * zx_screen.ROWS} cells, {bright} bright, {flash} flash",
            status=status,
        ),
        image,
    )


def check_sprite(path: Path) -> tuple[Asset, object]:
    """Validates a sprite grid against its own legend and renders it."""
    project = path.parent.parent.name
    raw = path.read_bytes()
    status = "PASS"
    note = ""
    image = None
    width = height = 0
    legend: dict[str, str] = {}

    try:
        data = json.loads(raw)
        width, height = int(data["w"]), int(data["h"])
        rows, legend = list(data["rows"]), dict(data["legend"])
        zx_sprite.validate(rows, width, height, legend)
        image = zx_sprite.render(rows, width, height, legend)
        # Not a failure: a pose family shares one legend, so an individual pose can
        # legitimately not reach for every colour in it. The road train's `R` (cab
        # flank) is exactly this — it only appears once the cab articulates, so the
        # straight pose never uses it. Worth printing, because a symbol no pose in
        # the family uses is a typo waiting to be copied into the next sprite.
        unused = sorted(set(legend) - {c for row in rows for c in row})
        if unused:
            note = f"legend symbols unused in this pose: {' '.join(unused)}"
    except (KeyError, ValueError, TypeError) as error:
        status = f"FAIL: {error}"

    return (
        Asset(
            project=project,
            mode="sprite",
            name=path.stem,
            source=path.relative_to(REPO),
            size=f"{width}x{height}",
            bytes_on_disk=len(raw),
            colours=len(set(legend.values())),
            detail=" ".join(f"{k}={v}" for k, v in sorted(legend.items())),
            status=status,
            note=note,
        ),
        image,
    )


#: Tiles per row on a tileset contact sheet, and the transparent gap between them.
SHEET_COLUMNS = 8
SHEET_GAP = 1


def _contact_sheet(tiles: list[Image.Image], size: int) -> Image.Image:
    """Lays tiles out left to right in authored order, a transparent pixel apart.

    The gap is transparent rather than a colour so the sheet can never be mistaken
    for a picture made of these tiles: nothing in it is a pixel the art put there.
    """
    columns = min(SHEET_COLUMNS, len(tiles))
    rows = -(-len(tiles) // columns)
    step = size + SHEET_GAP
    sheet = Image.new("RGBA", (columns * step - SHEET_GAP, rows * step - SHEET_GAP), zx_sprite.TRANSPARENT)
    for index, tile in enumerate(tiles):
        sheet.paste(tile.convert("RGBA"), ((index % columns) * step, (index // columns) * step))
    return sheet


def check_tile(rows: list[str], size: int, legend: dict[str, str]) -> Image.Image:
    """Validates one tile and returns its render, or raises ``ValueError``.

    Two sprite freedoms are withdrawn. A tile is background, so it has no
    transparency — the floor has to be *something*. And every ``8x8`` cell must
    pass the very test a ``.scr`` cell passes (``zx_screen.infer_cell``): at most
    one INK and one PAPER, from one brightness bank. Tiles whose size is a multiple
    of 8, laid on a grid of that size, put every cell of the result inside exactly
    one tile — so any room built from them is a picture the machine could display.
    """
    zx_sprite.validate(rows, size, size, legend)
    for y, row in enumerate(rows, start=1):
        x = row.find(".")
        if x >= 0:
            raise ValueError(f"row {y}, column {x + 1}: '.' is transparent, and a tile is opaque")
    image = zx_sprite.render(rows, size, size, legend).convert("RGB")
    cells = size // zx_screen.CELL
    for cell_y in range(cells):
        for cell_x in range(cells):
            zx_screen.infer_cell(image, cell_x, cell_y)
    return image


def check_tileset(path: Path) -> tuple[Asset, object]:
    """Validates a tileset — ``{tile, legend, tiles: {name: rows}}`` — and renders its sheet."""
    project = path.parent.parent.name
    raw = path.read_bytes()
    status = "PASS"
    note = ""
    image = None
    size = 0
    legend: dict[str, str] = {}
    tiles: dict[str, list[str]] = {}

    try:
        data = json.loads(raw)
        size = int(data["tile"])
        legend, tiles = dict(data["legend"]), dict(data["tiles"])
        if size < zx_screen.CELL or size % zx_screen.CELL:
            raise ValueError(f"tile size {size} must be a positive multiple of {zx_screen.CELL}")
        if not tiles:
            raise ValueError("a tileset needs at least one tile")
        renders = []
        for name, rows in tiles.items():
            if not zx_sprite.NAME_RE.fullmatch(name):
                raise ValueError(f"tile name {name!r} must be letters, digits, '.', '_' or '-'")
            try:
                renders.append(check_tile(list(rows), size, legend))
            except ValueError as error:
                raise ValueError(f"tile {name!r}: {error}") from error
        image = _contact_sheet(renders, size)
        # Same reasoning as for a sprite family: not a failure, but a symbol no tile
        # uses is a typo waiting to be copied into the next one.
        used = {c for rows in tiles.values() for row in rows for c in row}
        unused = sorted(set(legend) - used)
        if unused:
            note = f"legend symbols unused by any tile: {' '.join(unused)}"
    except (KeyError, ValueError, TypeError) as error:
        status = f"FAIL: {error}"

    return (
        Asset(
            project=project,
            mode="tileset",
            name=path.stem,
            source=path.relative_to(REPO),
            size=f"{size}x{size}",
            bytes_on_disk=len(raw),
            colours=len(set(legend.values())),
            detail=f"{len(tiles)} tiles: {' '.join(tiles)}",
            status=status,
            note=note,
        ),
        image,
    )


CHECKS = {"screen": check_screen, "sprite": check_sprite, "tileset": check_tileset}


def inventory() -> list[tuple[Asset, object]]:
    """Checks every source under ``art/`` and returns the rows plus the renders."""
    if not ART.is_dir():
        raise SystemExit(f"ERROR: {ART} does not exist")
    return [CHECKS[mode](path) for _project, mode, path in _iter_sources(ART)]


def command_verify(_args: argparse.Namespace) -> int:
    results = inventory()
    failures = 0
    for asset, _image in results:
        marker = "ok  " if asset.status == "PASS" else "FAIL"
        print(f"{marker} {asset.source} — {asset.size}, {asset.colours} colours")
        if asset.note:
            print(f"     note: {asset.note}")
        if asset.status != "PASS":
            print(f"     {asset.status}")
            failures += 1
    count = {mode: sum(1 for a, _ in results if a.mode == mode) for mode in CHECKS}
    print(
        f"\n{count['screen']} screens, {count['sprite']} sprites, "
        f"{count['tileset']} tilesets, {failures} failed"
    )
    return 1 if failures else 0


def command_build(args: argparse.Namespace) -> int:
    """Renders every source into ``build/``. Nothing here is committed."""
    results = inventory()
    written = 0
    for asset, image in results:
        if asset.status != "PASS" or image is None:
            print(f"skip {asset.source} — {asset.status}")
            continue
        out_dir = BUILD / asset.project / f"{asset.mode}s"
        out_dir.mkdir(parents=True, exist_ok=True)
        native = out_dir / f"{asset.name}.png"
        image.save(native)
        preview = out_dir / f"{asset.name}@{args.scale}x.png"
        zx_screen.nearest(image, args.scale).save(preview)
        written += 2
        if asset.mode == "screen" and args.gif:
            zx_screen.save_gif(asset.source.read_bytes(), out_dir / f"{asset.name}.gif", args.scale)
            written += 1
    print(f"wrote {written} files under {BUILD.relative_to(REPO)}/")
    return 0


def _manifest_text(results: list[tuple[Asset, object]]) -> str:
    lines = [
        "# Manifest",
        "",
        "Generated by `tools/zx_art.py manifest`. Do not edit by hand — every column",
        "below is measured from the file it names, so a stale row is a bug in the tool",
        "rather than a note someone forgot to update.",
        "",
        "`Check` means, for a screen, that decoding the `.scr` and encoding the result",
        "returns the identical 6912 bytes — so the file on disk is the whole picture and",
        "a PNG beside it would say nothing more. For a sprite it means the grid is",
        "rectangular and uses only `.` and its own legend symbols. For a tileset it means",
        "every tile is a square grid of its declared size with no `.` (tiles are opaque),",
        "and every `8x8` cell of every tile holds at most one INK and one PAPER from one",
        "brightness bank — the same test a screen cell passes, so a room laid out from",
        "these tiles on their own grid is a displayable screen. A note about unused",
        "legend symbols is not a failure: a pose family shares one legend, and a pose may",
        "not reach for every colour in it.",
        "",
    ]
    projects: dict[str, list[Asset]] = {}
    for asset, _image in results:
        projects.setdefault(asset.project, []).append(asset)

    for project in sorted(projects):
        assets = projects[project]
        lines += [f"## {project}", ""]
        for mode, heading in (("screen", "Screens"), ("sprite", "Sprites"), ("tileset", "Tilesets")):
            rows = [a for a in assets if a.mode == mode]
            if not rows:
                continue
            lines += [
                f"### {heading}",
                "",
                "| Asset | Size | Bytes | Colours | Detail | Check |",
                "|---|---|---:|---:|---|---|",
            ]
            for a in rows:
                lines.append(
                    f"| `{a.source}` | {a.size} | {a.bytes_on_disk} | {a.colours} "
                    f"| {a.detail} | {a.status}{' · ' + a.note if a.note else ''} |"
                )
            lines.append("")
    total = len(results)
    failed = sum(1 for a, _ in results if a.status != "PASS")
    lines += [f"---", "", f"{total} assets, {total - failed} passing, {failed} failing.", ""]
    return "\n".join(lines)


def command_manifest(_args: argparse.Namespace) -> int:
    results = inventory()
    MANIFEST.write_text(_manifest_text(results), encoding="utf-8")
    print(f"wrote {MANIFEST.relative_to(REPO)} — {len(results)} assets")
    return 1 if any(a.status != "PASS" for a, _ in results) else 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = root.add_subparsers(dest="command", required=True)

    sub.add_parser("verify", help="check every source under art/").set_defaults(run=command_verify)

    build = sub.add_parser("build", help="render art/ into build/")
    build.add_argument("--scale", type=int, default=PREVIEW_SCALE, help="preview scale (default 4)")
    build.add_argument("--gif", action="store_true", help="also write FLASH gifs for screens")
    build.set_defaults(run=command_build)

    sub.add_parser("manifest", help="write MANIFEST.md").set_defaults(run=command_manifest)
    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.run(args))


if __name__ == "__main__":
    raise SystemExit(main())
