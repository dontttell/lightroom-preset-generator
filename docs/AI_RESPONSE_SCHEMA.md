# AI Response Schema (style_analysis.v1.1)

> **用途：** 人读契约 — 审核 JSON 字段、LUT/XMP 路由与错误行为。  
> **机器读：** [`schemas/style_analysis.v1.1.json`](../schemas/style_analysis.v1.1.json)（v1 见 [`style_analysis.v1.json`](../schemas/style_analysis.v1.json)）  
> **实现：** [`ai/validator.py`](../ai/validator.py) + [`ai/parameter_registry.py`](../ai/parameter_registry.py)  
> **改 prompt 流程：** [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) §7 · 变更记录 [`PROMPT_CHANGELOG.md`](./PROMPT_CHANGELOG.md)

## Purpose

Path B (AI learning) expects the vision model to return a **single JSON object** describing grading style and suggested Lightroom parameters.

## Output modules

| Module | Keys | Required in JSON? | LUT | XMP |
|--------|------|-------------------|-----|-----|
| **§7a Core** | 11 global sliders | **Yes — all keys** | subset | yes |
| **§7b Color extension** | grading + HSL + vignette/grain (24) | **No — sparse only** | no | yes |

**§7b rule:** Omit keys when style does not warrant them. Do **not** output all 24 color-extension keys; cap non-zero §7b items at ~8 per response to avoid oversaturated / weird color.

## Top-level fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `overall_impression` | yes | string | User-facing summary |
| `editing_steps` | yes | array | Learning panel steps |
| `priority_adjustments` | yes | array | LR field names from whitelist |
| `parameters` | yes | object | Keyed by crs field name |
| `style_summary_en` | no | string | Optional |

## Parameter entries

```json
{"value": <number>, "confidence": <0..1>}
```

### §7a Core (all required)

| Key | Type | Range | LUT | XMP |
|-----|------|-------|-----|-----|
| Exposure2012 | float | −5 ~ 5 | yes | yes |
| Contrast2012 | int | −100 ~ 100 | yes | yes |
| Highlights2012 | int | −100 ~ 100 | no | yes |
| Shadows2012 | int | −100 ~ 100 | no | yes |
| Whites2012 | int | −100 ~ 100 | no | yes |
| Blacks2012 | int | −100 ~ 100 | no | yes |
| Temperature | int | 2000 ~ 50000 | yes* | yes |
| Tint | int | −150 ~ 150 | yes* | yes |
| Saturation | int | −100 ~ 100 | yes | yes |
| Vibrance | int | −100 ~ 100 | no | yes |
| Clarity2012 | int | −100 ~ 100 | yes | yes |

\* Temperature + Tint must both meet `lut_min_confidence` for LUT.

### §7b Color extension (sparse optional)

**Color grading:** `SplitToningShadowHue` (0–360), `SplitToningShadowSaturation` (0–100), `SplitToningHighlightHue`, `SplitToningHighlightSaturation`, `SplitToningBalance` (−100–100), `ColorGradeGlobalHue`, `ColorGradeGlobalSat`, `ColorGradeMidtoneHue`, `ColorGradeMidtoneSat`

**Targeted HSL:** `SaturationAdjustmentOrange`, `LuminanceAdjustmentOrange`, `SaturationAdjustmentRed`, `HueAdjustmentBlue`, `SaturationAdjustmentBlue`, `LuminanceAdjustmentBlue`, `HueAdjustmentAqua`, `SaturationAdjustmentAqua`, `LuminanceAdjustmentAqua`, `HueAdjustmentGreen`, `SaturationAdjustmentGreen`, `LuminanceAdjustmentGreen` (all −100–100 unless hue wheel 0–360 for split tone only)

**Effects:** `PostCropVignetteAmount` (−100–100), `PostCropVignetteMidpoint` (0–100), `GrainAmount` (0–100)

All §7b: **LUT no**, **XMP yes** if confidence ≥ `xmp_min_confidence`.

## LUT minimum bar

Unchanged from v1 — global keys only. §7b affects Lightroom after XMP import, not plate LUT preview.

## Versioning

- Current: **style_analysis.v1.1**
- Previous: **style_analysis.v1** (11 keys only)
- Bump version when adding/removing keys or changing semantics
