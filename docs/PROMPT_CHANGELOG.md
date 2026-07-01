# AI Prompt Changelog

> **用途：** 人读审计日志 — 记录 prompt 改了什么、为什么、影响哪些字段。  
> **流程：** 见 [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) §7。  
> **文档分层：** 见 [`README.md`](./README.md)。

Prompt files live under `config/prompts/`. Runtime path is chosen by `analysis.language` and optional `analysis.prompt_file` in `config/ai_config.local.yaml`.

## style_analysis.v1 — prompt revision 4 (2026-07-01)

- **Files:** `style_analysis.txt`, `style_analysis.en.txt` (full parity incl. §8 JSON)
- **Schema:** unchanged `style_analysis.v1`
- **Motivation:** Close taxonomy gaps; night subtype split; output completeness; pre-graded JPG & uncertain fallback
- **Changes:**
  - §1: require all 11 parameter keys; small non-zero for weak fields; fix §7 whitelist ref; priority_adjustments 3–5
  - §2: M mixed checklist; L-Blue hour / L-Night street lamps vs L-Neon table; pre-graded JPG rules; uncertain subtype fallback
  - §3: bands for P-Studio, P-Backlit (A/B), P-Window mixed, M mixed, L-Snow, L-Blue hour, L-Night street lamps
  - §5/§9: confidence caps for pre-graded & uncertain; expanded anti-patterns
  - English prompt: full §8 examples (was stub)
- **Regression:** Portrait studio, backlit, mixed env, blue hour, street-lamp night, pre-filtered JPG

## style_analysis.v1 — prompt revision 3 (2026-07-01)

- **Files:** `style_analysis.txt`, `style_analysis.en.txt`
- **Schema:** unchanged `style_analysis.v1`
- **Motivation:** Scene-first analysis — portrait vs landscape with subtypes; category-specific checklists and reference bands; night neon vs astro separation
- **Changes:**
  - Mandatory scene tag in `overall_impression` (`【大类/子类/光线】`)
  - editing_steps step 1 fixed to「场景识别」
  - Portrait: face vs ambient, skin, subject separation / mask guidance
  - Landscape subtypes: natural, urban day, night neon, astro, snow, fog, industrial
  - Per-subtype parameter reference tables (non-zero, banded)
  - §4 LUT vs local mask limits; global proxy confidence cap 0.52
  - Three positive examples: golden hour portrait, night neon, astro
- **Not in schema v1:** PostCropVignette / local masks — documented in editing_steps only
- **Regression:** Test portrait, neon night, astro samples separately

## style_analysis.v1 — prompt revision 2 (2026-07-01)

- **Files:** `style_analysis.txt` (zh-CN), `style_analysis.en.txt` (en)
- **Schema:** unchanged `style_analysis.v1`
- **Motivation:** Thicken prompt without multi-agent; embed imaging heuristics; enforce non-zero, range-bound parameters
- **Changes:**
  - §2 five-step flow: global tone → color tendency → zone tone → texture → LR mapping
  - Scene lookup table (golden hour, overcast, tungsten, shade, etc.)
  - Neutral-area color judgment guide (skin, shadows, gray surfaces)
  - Confidence rubric with minimum ≥0.55 on 3+ fields
  - Realistic positive example (warm portrait); explicit anti-patterns (all-zero, markdown)
  - Ban all-zero / uniform-confidence outputs
- **Affected fields:** All parameters; prioritizes LUT keys (Exposure, Contrast, Temperature+Tint, Saturation, Clarity)
- **Regression:** Run Path B on 1–3 sample images; compare non-zero count and Temperature deviation from 5500

## style_analysis.v1 (2026-07-01)

- **Files:** `style_analysis.txt` (zh-CN), `style_analysis.en.txt` (en)
- **Schema:** `schemas/style_analysis.v1.json` / `docs/AI_RESPONSE_SCHEMA.md`
- **Changes:**
  - Explicit schema version `style_analysis.v1` in system prompt
  - Documented which parameters participate in LUT vs XMP-only
  - Listed numeric ranges per Lightroom field
  - Aligned with `ai/parameter_registry.py` whitelist

## Migration notes

- When bumping schema version, add a new JSON schema file and keep prompts referencing the active version.
- Tune prompts on a dedicated git branch; merge to main after validator + sample-image regression.
