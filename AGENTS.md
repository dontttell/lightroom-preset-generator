# Agent Guide — Lightroom Preset Learner

Quick orientation for **Cursor / coding agents**. Human-readable docs live under [`docs/`](docs/README.md).

---

## What this repo is

Desktop **PyQt6** app: learn Lightroom grading from a reference image.

| Path | Trigger | Code |
|------|---------|------|
| **A — Precise** | LR edit metadata found | `core/metadata_*` → XMP export |
| **B — AI** | No metadata + user clicks AI + API configured | `ai/*` → optional LUT plate preview |

**Never commit:** `config/ai_config.local.yaml`, test images, API keys.

---

## Read first (by task)

| Task | Read |
|------|------|
| Any change | [`docs/README.md`](docs/README.md) — doc layers L0–L5 |
| Product behavior | [`docs/PRODUCT_SPEC_v2.md`](docs/PRODUCT_SPEC_v2.md) |
| UI / copy | [`docs/UI_UX_DESIGN.md`](docs/UI_UX_DESIGN.md) §11, [`gui/copy.py`](gui/copy.py) |
| Code flow | [`docs/CODE_ARCHITECTURE.md`](docs/CODE_ARCHITECTURE.md) |
| AI / prompt / JSON | [`docs/AI_ARCHITECTURE.md`](docs/AI_ARCHITECTURE.md), [`docs/AI_RESPONSE_SCHEMA.md`](docs/AI_RESPONSE_SCHEMA.md) |
| Style recipes / Plan B | [`docs/STYLE_RECIPE_SYSTEM.md`](docs/STYLE_RECIPE_SYSTEM.md), [`config/style_recipes/`](config/style_recipes/) |
| Prompt history (audit) | [`docs/PROMPT_CHANGELOG.md`](docs/PROMPT_CHANGELOG.md) |

**Rules (must follow):** [`.cursor/rules/`](.cursor/rules/)

---

## Key paths

```
main.py → gui/main_window.py
gui/workers.py     MetadataWorker | AiAnalysisWorker
core/metadata_*    Path A
ai/                Path B provider, parse, validate
config/prompts/    System prompts (versioned)
config/style_recipes/  Plan B YAML looks + README
ai/style_recipes.py    match_recipe(), merge_recipe_with_refine()
schemas/           style_analysis.v1.1.json (active); style_classify.v1.json (Plan B Call①)
lut/               LUT bake + plate preview
generators/        XMP export
```

Legacy (do not wire as default): `analyzers/`, `preview/preset_simulator.py`

---

## Checklists

### Editing AI or prompts

1. Follow [`docs/AI_ARCHITECTURE.md`](docs/AI_ARCHITECTURE.md) §7 SOP  
2. Update [`docs/PROMPT_CHANGELOG.md`](docs/PROMPT_CHANGELOG.md) when changing `config/prompts/`  
3. Keep `schemas/`, `ai/parameter_registry.py`, and prompt field lists aligned  
4. Run `python scripts/verify_ai_schema.py` if present  
5. After editing recipes: `python scripts/verify_style_recipes.py`  
6. Plan B dual-call: see [`docs/STYLE_RECIPE_SYSTEM.md`](docs/STYLE_RECIPE_SYSTEM.md) before wiring Provider  
7. Commit message: `prompt(style_analysis.v1.1): …` or `feat(ai): …`

### Editing UI copy

1. Change [`docs/UI_UX_DESIGN.md`](docs/UI_UX_DESIGN.md) §11 first  
2. Sync [`gui/copy.py`](gui/copy.py)  
3. User-facing text: use **精确识别 / 未能精确识别** — not “metadata”

### Editing layout / widgets

1. [`docs/UI_UX_DESIGN.md`](docs/UI_UX_DESIGN.md) §3–§7  
2. Plate preview: **left column only** (UI v1.6); vertical splitter + scroll in plate section (§3.4.5); no `PlateControlCard`

---

## Verification

```bash
python scripts/verify_ui.py      # before UI changes
python scripts/verify_ai_schema.py   # after AI/schema changes
python main.py                   # smoke start
```

Windows: `run.bat`

---

## Schema version

Current: **`style_analysis.v1.1`**. Bump only with new JSON schema file + changelog + registry update.
