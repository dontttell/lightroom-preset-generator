# AI Prompt Changelog

> **用途：** 人读审计日志 — 记录 prompt 改了什么、为什么、影响哪些字段。  
> **流程：** 见 [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) §7。  
> **文档分层：** 见 [`README.md`](./README.md)。

Prompt files live under `config/prompts/`. Runtime path is chosen by `analysis.language` and optional `analysis.prompt_file` in `config/ai_config.local.yaml`.

## style_classify.v1 + style_refine prompts — Plan B recipe pipeline (2026-07-07)

- **Files:** `style_classify.txt`, `style_analysis_refine.txt`, `config/style_recipes/*.yaml`, `ai/style_recipes.py`, `schemas/style_classify.v1.json`, `docs/STYLE_RECIPE_SYSTEM.md`, `scripts/verify_style_recipes.py`
- **Schema:** new **`style_classify.v1`** (Call①); Call② refine output shape documented in `STYLE_RECIPE_SYSTEM.md` (not yet a separate JSON schema file)
- **Motivation:** Anchor slider baselines in curated YAML recipes; AI classifies then applies bounded deltas instead of guessing all 11 core values from scratch
- **Runtime:** **Wired** — default `use_recipe_pipeline: true` in `OpenAiCompatibleProvider.analyze()`; Settings checkbox to disable
- **Recipes (7):** generic-daylight-landscape, film-lowsat-meadow, cinematic-teal-orange, soft-portrait-natural, golden-hour-portrait, blue-hour-landscape, neon-night-city
- **Regression:** `python scripts/verify_style_recipes.py`; meadow keyword smoke test in script

## style_analysis.v1.1 — color extension whitelist (2026-07-02)

- **Files:** `style_analysis.txt`, `style_analysis.en.txt`, `ai/parameter_registry.py`, `schemas/style_analysis.v1.1.json`, `core/metadata_parser.py`, `docs/AI_RESPONSE_SCHEMA.md`
- **Schema:** `style_analysis.v1` → **`style_analysis.v1.1`** (backward compatible: §7a core 11 unchanged)
- **Motivation:** Better film / night / teal-orange / neon / skin / sky / grass / vignette / grain via XMP; avoid forcing all color keys (oversaturated weird output)
- **Added fields (24, sparse optional §7b):**
  - Color grading: SplitToning* (5), ColorGradeGlobal/Midtone (4)
  - Targeted HSL: Orange/Red/Blue/Aqua/Green (12)
  - Effects: PostCropVignetteAmount/Midpoint, GrainAmount (3)
- **LUT:** unchanged — only 6 global keys; §7b is XMP + learning panel only
- **Prompt rules:** §7a all 11 required; §7b omit by default, ≤8 non-zero, no stacking, lower confidence
- **Regression:** Neon night (B), golden hour portrait (A), plain daylight (should omit §7b)

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
