# AI Response Schema (style_analysis.v1)

> **用途：** 人读契约 — 审核 JSON 字段、LUT/XMP 路由与错误行为。  
> **机器读：** [`schemas/style_analysis.v1.json`](../schemas/style_analysis.v1.json)  
> **实现：** [`ai/validator.py`](../ai/validator.py) + [`ai/parameter_registry.py`](../ai/parameter_registry.py)  
> **改 prompt 流程：** [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) §7 · 变更记录 [`PROMPT_CHANGELOG.md`](./PROMPT_CHANGELOG.md)

Machine-readable schema: [`schemas/style_analysis.v1.json`](../schemas/style_analysis.v1.json)  
Runtime validation: [`ai/validator.py`](../ai/validator.py) + [`ai/parameter_registry.py`](../ai/parameter_registry.py)
## Purpose

Path B (AI learning) expects the vision model to return a **single JSON object** describing grading style and suggested Lightroom parameters. This document is the contract between:

- Prompt files (`config/prompts/`)
- Provider adapters (`ai/openai_compatible_provider.py`)
- LUT / XMP pipelines

## Top-level fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `overall_impression` | yes | string | User-facing summary; language = `analysis.language` |
| `editing_steps` | yes | array | Learning panel steps |
| `priority_adjustments` | yes | array | LR field names, subset of parameter whitelist |
| `parameters` | yes | object | Keyed by LR crs field name |
| `style_summary_en` | no | string | Optional |

## Parameter entries

Each key in `parameters` must be in the whitelist below. Each value:

```json
{"value": <number>, "confidence": <0..1>}
```

### Whitelist, ranges, and routing

| Key | Type | Range | LUT preview | XMP export |
|-----|------|-------|-------------|------------|
| Exposure2012 | float | −5 ~ 5 | yes | if confidence ≥ xmp_min |
| Contrast2012 | int | −100 ~ 100 | yes | if confidence ≥ xmp_min |
| Highlights2012 | int | −100 ~ 100 | no | if confidence ≥ xmp_min |
| Shadows2012 | int | −100 ~ 100 | no | if confidence ≥ xmp_min |
| Whites2012 | int | −100 ~ 100 | no | if confidence ≥ xmp_min |
| Blacks2012 | int | −100 ~ 100 | no | if confidence ≥ xmp_min |
| Temperature | int | 2000 ~ 50000 | yes (pair) | if confidence ≥ xmp_min |
| Tint | int | −150 ~ 150 | yes (pair) | if confidence ≥ xmp_min |
| Saturation | int | −100 ~ 100 | yes | if confidence ≥ xmp_min |
| Vibrance | int | −100 ~ 100 | no | if confidence ≥ xmp_min |
| Clarity2012 | int | −100 ~ 100 | yes | if confidence ≥ xmp_min |

**LUT pair rule:** `Temperature` and `Tint` must both be present with confidence ≥ `lut_min_confidence` to participate in LUT baking.

Defaults (configurable in `ai_config.local.yaml`):

- `lut_min_confidence`: 0.35
- `xmp_min_confidence`: 0.25

## Processing pipeline

```
Raw JSON → parse_json_content → normalize_style_analysis → ParameterResult list
                                      ├─ clamp to range
                                      ├─ drop unknown keys (warn)
                                      └─ set include_in_lut / include_in_xmp
```

## LUT minimum bar

| Level | Requirement |
|-------|-------------|
| Runnable | ≥1 LUT-eligible parameter with confidence ≥ lut_min |
| Visible | Exposure ≠ 0, or Temperature/Tint off defaults, or \|Contrast/Saturation\| ≥ ~15 |
| Recommended | Exposure + Contrast + Temperature/Tint + Saturation |

## Errors

| Condition | Behavior |
|-----------|----------|
| Non-JSON response | Retry up to `max_retries`, then `AiAnalysisError` |
| Unknown parameter key | Ignored + warning in `raw._warnings` |
| Out-of-range value | Clamped + warning |
| Low confidence | Shown in UI; may skip LUT / XMP per thresholds |

## Versioning

- Current: **style_analysis.v1**
- Bump version when adding/removing keys or changing semantics
- Update prompt, changelog, and `ai/parameter_registry.py` together
