# ZX Spectrum Palette

This document defines the complete set of RGB colors permitted by the ZX Spectrum image-generation skill.

The image may use only these RGB values.

## Normal Colors

| Name    | RGB               | Hex       |
| ------- | ----------------- | --------- |
| BLACK   | `(0, 0, 0)`       | `#000000` |
| BLUE    | `(0, 0, 205)`     | `#0000CD` |
| RED     | `(205, 0, 0)`     | `#CD0000` |
| MAGENTA | `(205, 0, 205)`   | `#CD00CD` |
| GREEN   | `(0, 205, 0)`     | `#00CD00` |
| CYAN    | `(0, 205, 205)`   | `#00CDCD` |
| YELLOW  | `(205, 205, 0)`   | `#CDCD00` |
| WHITE   | `(205, 205, 205)` | `#CDCDCD` |

## Bright Colors

| Name      | RGB               | Hex       |
| --------- | ----------------- | --------- |
| B_BLACK   | `(0, 0, 0)`       | `#000000` |
| B_BLUE    | `(0, 0, 255)`     | `#0000FF` |
| B_RED     | `(255, 0, 0)`     | `#FF0000` |
| B_MAGENTA | `(255, 0, 255)`   | `#FF00FF` |
| B_GREEN   | `(0, 255, 0)`     | `#00FF00` |
| B_CYAN    | `(0, 255, 255)`   | `#00FFFF` |
| B_YELLOW  | `(255, 255, 0)`   | `#FFFF00` |
| B_WHITE   | `(255, 255, 255)` | `#FFFFFF` |

## Unique RGB Colors

`BLACK` and `B_BLACK` have the same RGB value:

```text
#000000
```

Therefore the palette contains **15 unique RGB colors**, not 16.

The complete unique RGB palette is:

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

## Important

Do not substitute similar RGB values.

For example:

```text
#0000CC
#CC0000
#00CC00
```

are NOT valid ZX Spectrum colors.

The validator performs exact RGB matching.
