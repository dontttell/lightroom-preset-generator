# AI Prompt Changelog

> **用途：** 人读审计日志 — 记录 prompt 改了什么、为什么、影响哪些字段。  
> **流程：** 见 [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) §7。  
> **文档分层：** 见 [`README.md`](./README.md)。

Prompt files live under `config/prompts/`. Runtime path is chosen by `analysis.language` and optional `analysis.prompt_file` in `config/ai_config.local.yaml`.
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
