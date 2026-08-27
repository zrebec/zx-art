#!/usr/bin/env python3
"""Temporary Ice Haul road-train sprite workbench.

The Ice Haul deliverable is TypeScript Uint8Array data.  This helper stays in
zxart and only produces human previews plus packed byte declarations used while
authoring that data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw


OUT = Path("outputs")
FRAME_W = 40
FRAME_H = 64
CAB_W = 24
CAB_H = 24
TRAILER_W = 40
TRAILER_H = 60
CAB_X = 8
CAB_Y = 0
TRAILER_X = 0
TRAILER_Y = 4

CAB_X_BY_ANGLE = {-2: 4, -1: 6, 0: 8, 1: 10, 2: 12}

COLORS = {
    ".": (0, 0, 0, 0),
    "K": (0, 0, 0, 255),
    "R": (205, 0, 0, 255),
    "B": (0, 0, 205, 255),
    "U": (0, 0, 255, 255),
    "C": (0, 255, 255, 255),
    "W": (255, 255, 255, 255),
    "Y": (255, 255, 0, 255),
    "L": (205, 0, 0, 255),
}

LAYER_SYMBOL = {
    "base": "K",
    "red": "R",
    "blue": "B",
    "brightBlue": "U",
    "detail": "K",
    "cyan": "C",
    "white": "W",
    "yellow": "Y",
    "lamps": "L",
}


def mask(width: int, height: int) -> Image.Image:
    return Image.new("1", (width, height), 0)


def polygon(target: Image.Image, points: Iterable[tuple[int, int]]) -> None:
    ImageDraw.Draw(target).polygon(list(points), fill=1)


def rect(target: Image.Image, box: tuple[int, int, int, int]) -> None:
    ImageDraw.Draw(target).rectangle(box, fill=1)


def line(target: Image.Image, points: Iterable[tuple[int, int]], width: int = 1) -> None:
    ImageDraw.Draw(target).line(list(points), fill=1, width=width)


def shear(source: Image.Image, amount: int) -> Image.Image:
    """Swing the far/top end while leaving the near axle almost planted."""
    out = mask(source.width, source.height)
    src = source.load()
    dst = out.load()
    for y in range(source.height):
        shift = round(amount * (1 - y / max(1, source.height - 1)))
        for x in range(source.width):
            nx = x + shift
            if 0 <= nx < source.width and src[x, y]:
                dst[nx, y] = 1
    return out


def mirror(source: Image.Image) -> Image.Image:
    return source.transpose(Image.Transpose.FLIP_LEFT_RIGHT)


def straight_cab() -> dict[str, Image.Image]:
    layers = {name: mask(CAB_W, CAB_H) for name in ("base", "red", "detail", "cyan")}
    polygon(layers["base"], [(6, 4), (17, 4), (21, 9), (21, 18), (18, 22), (5, 22), (2, 18), (2, 9)])
    polygon(layers["red"], [(7, 5), (16, 5), (19, 9), (19, 18), (17, 20), (6, 20), (4, 18), (4, 9)])
    polygon(layers["cyan"], [(7, 7), (16, 7), (18, 10), (5, 10)])
    line(layers["detail"], [(5, 11), (18, 11)])
    line(layers["detail"], [(6, 18), (17, 18)])
    rect(layers["detail"], (10, 6, 12, 10))
    return layers


def straight_trailer() -> dict[str, Image.Image]:
    names = ("base", "blue", "brightBlue", "detail", "cyan", "white", "yellow", "lamps")
    layers = {name: mask(TRAILER_W, TRAILER_H) for name in names}

    # One continuous road-train mass: narrow far roof, broad near rear wall,
    # deep under-run frame and clearly separated tyre pairs.
    polygon(layers["base"], [
        (13, 0), (26, 0), (34, 8), (37, 14), (38, 46),
        (36, 51), (32, 53), (32, 58), (25, 59), (23, 54),
        (16, 54), (14, 59), (7, 58), (7, 53), (3, 51),
        (1, 46), (2, 14), (5, 8),
    ])

    # Upper surface (visible because the camera is behind and above the truck).
    polygon(layers["brightBlue"], [(13, 2), (26, 2), (33, 10), (6, 10)])
    polygon(layers["blue"], [(5, 13), (18, 13), (18, 45), (6, 47), (4, 44)])
    polygon(layers["blue"], [(21, 13), (34, 13), (35, 44), (33, 47), (21, 45)])
    polygon(layers["brightBlue"], [(3, 15), (5, 13), (5, 46), (3, 44)])
    polygon(layers["brightBlue"], [(34, 13), (36, 15), (36, 44), (34, 46)])

    # Rear-door structure: outer frame, twin doors, three horizontal ribs and
    # hinges. These black pixels are drawn after the blue panels.
    line(layers["detail"], [(4, 12), (35, 12)], 2)
    line(layers["detail"], [(19, 13), (19, 45)], 2)
    for y in (24, 35, 46):
        line(layers["detail"], [(4, y), (35, y)])
    for y in (18, 31, 41):
        rect(layers["detail"], (6, y, 8, y + 1))
        rect(layers["detail"], (31, y, 33, y + 1))
    rect(layers["detail"], (17, 36, 18, 41))
    rect(layers["detail"], (21, 36, 22, 41))
    line(layers["detail"], [(5, 49), (34, 49)], 2)

    # Cold rim light and accumulated ice make the two planes readable without
    # smoothing or non-Spectrum colours.
    line(layers["cyan"], [(13, 0), (26, 0)])
    line(layers["cyan"], [(12, 1), (5, 10), (3, 16)])
    line(layers["cyan"], [(27, 1), (34, 10), (36, 16)])
    line(layers["cyan"], [(5, 11), (34, 11)])
    line(layers["cyan"], [(3, 15), (3, 44)])
    line(layers["cyan"], [(36, 15), (36, 44)])
    line(layers["white"], [(14, 1), (25, 1)])
    line(layers["white"], [(8, 9), (17, 9)])
    rect(layers["white"], (6, 14, 7, 18))
    rect(layers["white"], (31, 25, 32, 29))
    rect(layers["cyan"], (9, 55, 12, 57))
    rect(layers["cyan"], (27, 55, 30, 57))

    # Tail lamps are their own semantic layer; only these become bright red on
    # the brake. The yellow plate remains a separate detail.
    rect(layers["lamps"], (5, 43, 8, 46))
    rect(layers["lamps"], (31, 43, 34, 46))
    rect(layers["yellow"], (17, 47, 22, 49))
    return layers


def pose_family(base: dict[str, Image.Image], amounts: tuple[int, int, int]) -> dict[int, dict[str, Image.Image]]:
    left_hard = {name: shear(layer, amounts[0]) for name, layer in base.items()}
    left = {name: shear(layer, amounts[1]) for name, layer in base.items()}
    straight = {name: layer.copy() for name, layer in base.items()}
    return {
        -2: left_hard,
        -1: left,
        0: straight,
        1: {name: mirror(layer) for name, layer in left.items()},
        2: {name: mirror(layer) for name, layer in left_hard.items()},
    }


CABS = pose_family(straight_cab(), (-6, -3, 0))
TRAILERS = pose_family(straight_trailer(), (-6, -3, 0))


def compose(cab_angle: int, trailer_angle: int) -> list[str]:
    grid = [["."] * FRAME_W for _ in range(FRAME_H)]

    def paint(layers: dict[str, Image.Image], ox: int, oy: int, order: tuple[str, ...]) -> None:
        for name in order:
            layer = layers.get(name)
            if layer is None:
                continue
            pixels = layer.load()
            symbol = LAYER_SYMBOL[name]
            for y in range(layer.height):
                for x in range(layer.width):
                    if pixels[x, y]:
                        grid[oy + y][ox + x] = symbol

    paint(CABS[cab_angle], CAB_X_BY_ANGLE[cab_angle], CAB_Y, ("base", "red", "cyan", "detail"))
    paint(
        TRAILERS[trailer_angle], TRAILER_X, TRAILER_Y,
        ("base", "blue", "brightBlue", "detail", "cyan", "white", "lamps", "yellow"),
    )
    return ["".join(row) for row in grid]


def crop_to_byte_bounds(layer: Image.Image) -> tuple[int, int, Image.Image]:
    bounds = layer.getbbox()
    if bounds is None:
        raise ValueError("cannot export an empty layer")
    left, top, right, bottom = bounds
    left = (left // 8) * 8
    right = min(layer.width, ((right + 7) // 8) * 8)
    return left, top, layer.crop((left, top, right, bottom))


def packed(layer: Image.Image) -> list[int]:
    assert layer.width % 8 == 0
    result: list[int] = []
    pixels = layer.load()
    for y in range(layer.height):
        for byte_x in range(layer.width // 8):
            value = 0
            for bit in range(8):
                if pixels[byte_x * 8 + bit, y]:
                    value |= 0x80 >> bit
            result.append(value)
    return result


def typescript_data() -> str:
    lines = ["// Generated workbench output; copy byte data into Ice Haul."]
    for family_name, family in (("CAB", CABS), ("TRAILER", TRAILERS)):
        for angle in (-2, -1, 0):
            for layer_name, layer in family[angle].items():
                x, y, cropped = crop_to_byte_bounds(layer)
                values = packed(cropped)
                chunks = [values[i:i + 12] for i in range(0, len(values), 12)]
                ident = f"{family_name}_{angle}_{layer_name}".replace("-", "M").upper()
                lines.append(
                    f"const {ident} = layer({x}, {y}, {cropped.width}, {cropped.height}, new Uint8Array(["
                )
                for chunk in chunks:
                    lines.append("  " + ", ".join(f"0x{value:02X}" for value in chunk) + ",")
                lines.append("]))")
    return "\n".join(lines) + "\n"


def emit_typescript() -> None:
    data = typescript_data()
    (OUT / "player_road_train_data.ts").write_text(data, encoding="utf-8")

    header = '''import {
  C, bitmapPixelMask, createBitmap, drawBitmap, mirrorBitmap,
  type Bitmap, type GlowSource, type PixelMask, type SpectrumColor,
} from 'zx-kit'
import {
  GLOW_CORE_INTENSITY,
  TRUCK_GLOW_BRAKE_INTENSITY, TRUCK_GLOW_BRAKE_RADIUS,
  TRUCK_GLOW_CORE_RADIUS, TRUCK_GLOW_INTENSITY, TRUCK_GLOW_RADIUS,
} from '../../config.ts'
import { glowRadiusScale } from '../vehicleGlow.ts'

/** Code-native articulated road train, viewed from behind and slightly above. */
export const PLAYER_TRUCK_W = 40
export const PLAYER_TRUCK_H = 64

const CAB_W = 24
const CAB_H = 24
const CAB_Y = 0
const TRAILER_W = 40
const TRAILER_H = 60
const TRAILER_X = 0
const TRAILER_Y = 4

export type TruckAngle = -2 | -1 | 0 | 1 | 2
export const PLAYER_TRUCK_ANGLES: readonly TruckAngle[] = [-2, -1, 0, 1, 2]

const CAB_X_BY_ANGLE: Readonly<Record<TruckAngle, number>> = {
  [-2]: 4, [-1]: 6, [0]: 8, [1]: 10, [2]: 12,
}

export const PLAYER_TRUCK_LAYOUT = {
  cab: { y: CAB_Y, width: CAB_W, height: CAB_H, xByAngle: CAB_X_BY_ANGLE },
  trailer: { x: TRAILER_X, y: TRAILER_Y, width: TRAILER_W, height: TRAILER_H },
} as const

export interface PlayerTruckLayer {
  readonly x: number
  readonly y: number
  readonly bitmap: Bitmap
}

function layer(x: number, y: number, width: number, height: number, data: Uint8Array): PlayerTruckLayer {
  return { x, y, bitmap: createBitmap(data, width, height) }
}

'''

    footer = '''
export interface PlayerTruckCabPose {
  readonly base: PlayerTruckLayer
  readonly red: PlayerTruckLayer
  readonly detail: PlayerTruckLayer
  readonly cyan: PlayerTruckLayer
}

export interface PlayerTruckTrailerPose {
  readonly base: PlayerTruckLayer
  readonly blue: PlayerTruckLayer
  readonly brightBlue: PlayerTruckLayer
  readonly detail: PlayerTruckLayer
  readonly cyan: PlayerTruckLayer
  readonly white: PlayerTruckLayer
  readonly yellow: PlayerTruckLayer
  readonly lamps: PlayerTruckLayer
}

function mirrorLayer(source: PlayerTruckLayer, componentWidth: number): PlayerTruckLayer {
  return {
    x: componentWidth - source.x - source.bitmap.width,
    y: source.y,
    bitmap: mirrorBitmap(source.bitmap),
  }
}

function mirrorCabPose(source: PlayerTruckCabPose): PlayerTruckCabPose {
  return {
    base: mirrorLayer(source.base, CAB_W),
    red: mirrorLayer(source.red, CAB_W),
    detail: mirrorLayer(source.detail, CAB_W),
    cyan: mirrorLayer(source.cyan, CAB_W),
  }
}

function mirrorTrailerPose(source: PlayerTruckTrailerPose): PlayerTruckTrailerPose {
  return {
    base: mirrorLayer(source.base, TRAILER_W),
    blue: mirrorLayer(source.blue, TRAILER_W),
    brightBlue: mirrorLayer(source.brightBlue, TRAILER_W),
    detail: mirrorLayer(source.detail, TRAILER_W),
    cyan: mirrorLayer(source.cyan, TRAILER_W),
    white: mirrorLayer(source.white, TRAILER_W),
    yellow: mirrorLayer(source.yellow, TRAILER_W),
    lamps: mirrorLayer(source.lamps, TRAILER_W),
  }
}

const CAB_HARD_LEFT: PlayerTruckCabPose = {
  base: CAB_M2_BASE, red: CAB_M2_RED, detail: CAB_M2_DETAIL, cyan: CAB_M2_CYAN,
}
const CAB_LEFT: PlayerTruckCabPose = {
  base: CAB_M1_BASE, red: CAB_M1_RED, detail: CAB_M1_DETAIL, cyan: CAB_M1_CYAN,
}
const CAB_STRAIGHT: PlayerTruckCabPose = {
  base: CAB_0_BASE, red: CAB_0_RED, detail: CAB_0_DETAIL, cyan: CAB_0_CYAN,
}

const TRAILER_HARD_LEFT: PlayerTruckTrailerPose = {
  base: TRAILER_M2_BASE,
  blue: TRAILER_M2_BLUE,
  brightBlue: TRAILER_M2_BRIGHTBLUE,
  detail: TRAILER_M2_DETAIL,
  cyan: TRAILER_M2_CYAN,
  white: TRAILER_M2_WHITE,
  yellow: TRAILER_M2_YELLOW,
  lamps: TRAILER_M2_LAMPS,
}
const TRAILER_LEFT: PlayerTruckTrailerPose = {
  base: TRAILER_M1_BASE,
  blue: TRAILER_M1_BLUE,
  brightBlue: TRAILER_M1_BRIGHTBLUE,
  detail: TRAILER_M1_DETAIL,
  cyan: TRAILER_M1_CYAN,
  white: TRAILER_M1_WHITE,
  yellow: TRAILER_M1_YELLOW,
  lamps: TRAILER_M1_LAMPS,
}
const TRAILER_STRAIGHT: PlayerTruckTrailerPose = {
  base: TRAILER_0_BASE,
  blue: TRAILER_0_BLUE,
  brightBlue: TRAILER_0_BRIGHTBLUE,
  detail: TRAILER_0_DETAIL,
  cyan: TRAILER_0_CYAN,
  white: TRAILER_0_WHITE,
  yellow: TRAILER_0_YELLOW,
  lamps: TRAILER_0_LAMPS,
}

const CAB_POSES: Readonly<Record<TruckAngle, PlayerTruckCabPose>> = {
  [-2]: CAB_HARD_LEFT,
  [-1]: CAB_LEFT,
  [0]: CAB_STRAIGHT,
  [1]: mirrorCabPose(CAB_LEFT),
  [2]: mirrorCabPose(CAB_HARD_LEFT),
}

const TRAILER_POSES: Readonly<Record<TruckAngle, PlayerTruckTrailerPose>> = {
  [-2]: TRAILER_HARD_LEFT,
  [-1]: TRAILER_LEFT,
  [0]: TRAILER_STRAIGHT,
  [1]: mirrorTrailerPose(TRAILER_LEFT),
  [2]: mirrorTrailerPose(TRAILER_HARD_LEFT),
}

/** Small packed runtime bitmaps; no screen-sized image data is retained. */
export const PLAYER_TRUCK_POSES = { cab: CAB_POSES, trailer: TRAILER_POSES } as const

function drawLayer(
  ctx: CanvasRenderingContext2D,
  source: PlayerTruckLayer,
  x: number,
  y: number,
  color: SpectrumColor,
): void {
  drawBitmap(ctx, source.bitmap, x + source.x, y + source.y, color)
}

export interface PlayerTruckArticulation {
  cabYaw: number
  trailerYaw: number
  cabAngle: TruckAngle
  trailerAngle: TruckAngle
}

function clampSteering(value: number): number {
  return Math.max(-1, Math.min(1, value))
}

export function quantizeTruckAngle(yaw: number): TruckAngle {
  const scaled = clampSteering(yaw) * 2
  const rounded = scaled < 0 ? -Math.round(-scaled) : Math.round(scaled)
  if (Object.is(rounded, -0)) return 0
  return Math.max(-2, Math.min(2, rounded)) as TruckAngle
}

export function createPlayerTruckArticulation(steering = 0): PlayerTruckArticulation {
  const yaw = clampSteering(steering)
  const angle = quantizeTruckAngle(yaw)
  return { cabYaw: yaw, trailerYaw: yaw, cabAngle: angle, trailerAngle: angle }
}

/** Mutates and returns the same object; dt is clamped to 50 ms. */
export function updatePlayerTruckArticulation(
  state: PlayerTruckArticulation,
  steering: number,
  dtMs: number,
): PlayerTruckArticulation {
  const target = clampSteering(steering)
  const dt = Math.max(0, Math.min(50, dtMs))
  state.cabYaw += (target - state.cabYaw) * (1 - Math.exp(-dt / 100))
  state.trailerYaw += (state.cabYaw - state.trailerYaw) * (1 - Math.exp(-dt / 280))
  state.cabAngle = quantizeTruckAngle(state.cabYaw)
  state.trailerAngle = quantizeTruckAngle(state.trailerYaw)
  return state
}

export function playerTruckOrigin(cx: number, baseY: number, lean = 0): { x: number; y: number } {
  return {
    x: Math.round(cx - PLAYER_TRUCK_W / 2 + lean),
    y: Math.round(baseY - PLAYER_TRUCK_H),
  }
}

export const PLAYER_TRUCK_LAMP_COLORS = { rolling: C.RED, braking: C.B_RED } as const

/** Cabin first, then trailer: straight ahead hides the tractor; articulation reveals its flank. */
export function drawPlayerTruck(
  ctx: CanvasRenderingContext2D,
  cx: number,
  baseY: number,
  state: Readonly<PlayerTruckArticulation>,
  braking = false,
  lean = 0,
): void {
  const origin = playerTruckOrigin(cx, baseY, lean)
  const cabX = origin.x + CAB_X_BY_ANGLE[state.cabAngle]
  const cabY = origin.y + CAB_Y
  const cab = CAB_POSES[state.cabAngle]
  drawLayer(ctx, cab.base, cabX, cabY, C.BLACK)
  drawLayer(ctx, cab.red, cabX, cabY, C.RED)
  drawLayer(ctx, cab.cyan, cabX, cabY, C.B_CYAN)
  drawLayer(ctx, cab.detail, cabX, cabY, C.BLACK)

  const trailerX = origin.x + TRAILER_X
  const trailerY = origin.y + TRAILER_Y
  const trailer = TRAILER_POSES[state.trailerAngle]
  drawLayer(ctx, trailer.base, trailerX, trailerY, C.BLACK)
  drawLayer(ctx, trailer.blue, trailerX, trailerY, C.BLUE)
  drawLayer(ctx, trailer.brightBlue, trailerX, trailerY, C.B_BLUE)
  drawLayer(ctx, trailer.detail, trailerX, trailerY, C.BLACK)
  drawLayer(ctx, trailer.cyan, trailerX, trailerY, C.B_CYAN)
  drawLayer(ctx, trailer.white, trailerX, trailerY, C.B_WHITE)
  drawLayer(ctx, trailer.lamps, trailerX, trailerY, braking ? C.B_RED : C.RED)
  drawLayer(ctx, trailer.yellow, trailerX, trailerY, C.B_YELLOW)
}

function blitBitmap(target: Uint8Array, source: Bitmap, offsetX: number, offsetY: number): void {
  const targetBytesPerRow = PLAYER_TRUCK_W / 8
  const sourceBytesPerRow = source.width / 8
  for (let y = 0; y < source.height; y++) {
    for (let x = 0; x < source.width; x++) {
      const sourceByte = source.data[y * sourceBytesPerRow + (x >> 3)]!
      if ((sourceByte & (0x80 >> (x & 7))) === 0) continue
      const tx = offsetX + x
      const ty = offsetY + y
      if (tx < 0 || tx >= PLAYER_TRUCK_W || ty < 0 || ty >= PLAYER_TRUCK_H) {
        throw new Error(`player truck collision pixel outside ${PLAYER_TRUCK_W}x${PLAYER_TRUCK_H}`)
      }
      target[ty * targetBytesPerRow + (tx >> 3)]! |= 0x80 >> (tx & 7)
    }
  }
}

function mergeCollision(cabAngle: TruckAngle, trailerAngle: TruckAngle): Bitmap {
  const data = new Uint8Array((PLAYER_TRUCK_W / 8) * PLAYER_TRUCK_H)
  const cab = CAB_POSES[cabAngle].base
  const trailer = TRAILER_POSES[trailerAngle].base
  blitBitmap(data, cab.bitmap, CAB_X_BY_ANGLE[cabAngle] + cab.x, CAB_Y + cab.y)
  blitBitmap(data, trailer.bitmap, TRAILER_X + trailer.x, TRAILER_Y + trailer.y)
  return createBitmap(data, PLAYER_TRUCK_W, PLAYER_TRUCK_H)
}

/** All 25 unions are built once; render/update/collision allocate nothing per frame. */
export const PLAYER_TRUCK_COLLISION_BITMAPS: readonly (readonly Bitmap[])[] =
  PLAYER_TRUCK_ANGLES.map((cabAngle) =>
    PLAYER_TRUCK_ANGLES.map((trailerAngle) => mergeCollision(cabAngle, trailerAngle)),
  )

export const PLAYER_TRUCK_COLLISION_MASKS: readonly (readonly PixelMask[])[] =
  PLAYER_TRUCK_COLLISION_BITMAPS.map((row) => row.map(bitmapPixelMask))

// The sprite is a rear-high projection: its upper body is not a tyre touching
// the shoulder. Off-road physics therefore follows the two tyre contact patches,
// while traffic collision keeps the complete articulated body silhouette.
const ROAD_CONTACT_TOP = PLAYER_TRUCK_H - 12
const ROAD_LEFT_TYRE = { left: 6, right: 15 } as const
const ROAD_RIGHT_TYRE = { left: 24, right: 33 } as const
const EMPTY_MASK_ROW: readonly number[] = []

function roadContactMask(source: PixelMask): PixelMask {
  const rows = source.rows.map((row, y) => {
    if (y < ROAD_CONTACT_TOP) return EMPTY_MASK_ROW
    return row.filter((x) =>
      (x >= ROAD_LEFT_TYRE.left && x <= ROAD_LEFT_TYRE.right)
      || (x >= ROAD_RIGHT_TYRE.left && x <= ROAD_RIGHT_TYRE.right),
    )
  })
  return {
    width: source.width,
    height: source.height,
    rows,
    totalPixels: rows.reduce((sum, row) => sum + row.length, 0),
  }
}

export const PLAYER_TRUCK_ROAD_MASKS: readonly (readonly PixelMask[])[] =
  PLAYER_TRUCK_COLLISION_MASKS.map((row) => row.map(roadContactMask))

export function getPlayerTruckCollisionBitmap(state: Readonly<PlayerTruckArticulation>): Bitmap {
  return PLAYER_TRUCK_COLLISION_BITMAPS[state.cabAngle + 2]![state.trailerAngle + 2]!
}

export function getPlayerTruckCollisionMask(state: Readonly<PlayerTruckArticulation>): PixelMask {
  return PLAYER_TRUCK_COLLISION_MASKS[state.cabAngle + 2]![state.trailerAngle + 2]!
}

export function getPlayerTruckRoadMask(state: Readonly<PlayerTruckArticulation>): PixelMask {
  return PLAYER_TRUCK_ROAD_MASKS[state.cabAngle + 2]![state.trailerAngle + 2]!
}

export const PLAYER_TRUCK_STRAIGHT_COLLISION = PLAYER_TRUCK_COLLISION_BITMAPS[2]![2]!

export interface PlayerTruckPoint {
  readonly dx: number
  readonly dy: number
}

function measureLampPositions(angle: TruckAngle): readonly PlayerTruckPoint[] {
  const source = TRAILER_POSES[angle].lamps
  const sums = [{ x: 0, y: 0, count: 0 }, { x: 0, y: 0, count: 0 }]
  const bytesPerRow = source.bitmap.width / 8
  for (let y = 0; y < source.bitmap.height; y++) {
    for (let x = 0; x < source.bitmap.width; x++) {
      const byte = source.bitmap.data[y * bytesPerRow + (x >> 3)]!
      if ((byte & (0x80 >> (x & 7))) === 0) continue
      const dx = TRAILER_X + source.x + x + 0.5
      const dy = TRAILER_Y + source.y + y + 0.5
      const sum = sums[dx < PLAYER_TRUCK_W / 2 ? 0 : 1]!
      sum.x += dx
      sum.y += dy
      sum.count++
    }
  }
  return sums.map((sum) => ({ dx: sum.x / sum.count, dy: sum.y / sum.count }))
}

const LAMP_POSITIONS = Object.fromEntries(
  PLAYER_TRUCK_ANGLES.map((angle) => [angle, measureLampPositions(angle)]),
) as Record<TruckAngle, readonly PlayerTruckPoint[]>

const WHEEL_POSITIONS: readonly PlayerTruckPoint[] = [
  { dx: 11, dy: TRAILER_Y + 56.5 },
  { dx: 29, dy: TRAILER_Y + 56.5 },
]

export function getPlayerTruckLampPositions(
  state: Readonly<Pick<PlayerTruckArticulation, 'trailerAngle'>>,
): readonly PlayerTruckPoint[] {
  return LAMP_POSITIONS[state.trailerAngle]
}

export function getPlayerTruckWheelPositions(
  _state: Readonly<Pick<PlayerTruckArticulation, 'trailerAngle'>>,
): readonly PlayerTruckPoint[] {
  return WHEEL_POSITIONS
}

export function pushPlayerTruckLampSpots(
  out: GlowSource[],
  cx: number,
  baseY: number,
  state: Readonly<PlayerTruckArticulation>,
  braking: boolean,
  lean = 0,
): void {
  const origin = playerTruckOrigin(cx, baseY, lean)
  const scale = glowRadiusScale()
  const intensity = braking ? TRUCK_GLOW_BRAKE_INTENSITY : TRUCK_GLOW_INTENSITY
  const radius = (braking ? TRUCK_GLOW_BRAKE_RADIUS : TRUCK_GLOW_RADIUS) * scale
  for (const lamp of getPlayerTruckLampPositions(state)) {
    const x = origin.x + lamp.dx
    const y = origin.y + lamp.dy
    out.push({ x, y, radius, color: C.B_RED, intensity })
    if (braking) {
      out.push({
        x, y,
        radius: TRUCK_GLOW_CORE_RADIUS * scale,
        color: C.B_WHITE,
        intensity: GLOW_CORE_INTENSITY,
      })
    }
  }
}
'''
    runtime = header + data + footer
    (OUT / "playerTruck.ts").write_text(runtime, encoding="utf-8")

    target = Path("/Users/zrebec/Projects/retro/games/iceroads/src/render/sprites/playerTruck.ts")
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    patch_lines = ["*** Begin Patch"]
    if old:
        patch_lines.extend(["*** Update File: src/render/sprites/playerTruck.ts", "@@"])
        patch_lines.extend(f"-{line}" for line in old.splitlines())
        patch_lines.extend(f"+{line}" for line in runtime.splitlines())
    else:
        patch_lines.append("*** Add File: src/render/sprites/playerTruck.ts")
        patch_lines.extend(f"+{line}" for line in runtime.splitlines())
    patch_lines.append("*** End Patch")
    (OUT / "playerTruck.patch").write_text("\n".join(patch_lines) + "\n", encoding="utf-8")


def write_preview(name: str, rows: list[str]) -> None:
    (OUT / f"{name}_rows.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
    image = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(rows):
        for x, symbol in enumerate(row):
            pixels[x, y] = COLORS[symbol]
    image.save(OUT / f"{name}.png")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    samples = [
        ("player_road_train_hard_left", -2, 0),
        ("player_road_train_left", -2, -1),
        ("player_road_train_straight", 0, 0),
        ("player_road_train_right", 2, 1),
        ("player_road_train_hard_right", 2, 0),
    ]
    for name, cab_angle, trailer_angle in samples:
        write_preview(name, compose(cab_angle, trailer_angle))
    emit_typescript()

    strip = Image.new("RGBA", (FRAME_W * len(samples), FRAME_H), (0, 0, 0, 0))
    for index, (name, _, _) in enumerate(samples):
        strip.alpha_composite(Image.open(OUT / f"{name}.png"), (index * FRAME_W, 0))
    strip.resize((strip.width * 4, strip.height * 4), Image.Resampling.NEAREST).save(
        OUT / "player_road_train_strip_4x.png"
    )
    print(f"WROTE {len(samples)} 40x64 previews, packed TypeScript data and 4x strip under {OUT}")


if __name__ == "__main__":
    main()
