# 风格配方库（Style Recipes）

机器可读 YAML，供 **路线 B：配方库 + 双次 AI** 使用。

## 文件格式

每个配方一个 `.yaml`，字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 唯一 ID，与文件名一致 |
| `version` | 是 | 配方版本号（整数） |
| `name_zh` | 是 | 用户可见名称 |
| `description` | 否 | 维护者备注 |
| `match.categories` | 是 | `P` / `L` / `M` |
| `match.subtypes` | 否 | 与 prompt taxonomy 一致，如 `L-natural-general` |
| `match.keywords_zh` | 否 | 画面/风格关键词，匹配加分 |
| `match.keywords_en` | 否 | 英文关键词 |
| `parameters` | 是 | §7a 基准值（11 项建议全填） |
| `default_confidence` | 否 | 配方来源项默认置信度，默认 `0.72` |
| `optional_7b` | 否 | §7b 稀疏默认（可空） |
| `tweak_limits` | 是 | AI delta 允许范围 `{key: [min_delta, max_delta]}` |
| `priority_adjustments` | 是 | 建议优先滑块顺序 |
| `editing_hints` | 否 | 供 Call② 参考的要点（非直接展示） |

## 匹配算法（`ai/style_recipes.py`）

1. `category` 不符 → 跳过  
2. `subtype` 命中 → +40 分  
3. 每个 `keywords_zh/en` 在 `scene_keywords` / `style_hints` 命中 → +15 分  
4. Call① 的 `candidate_recipe_ids` 含本 id → +20 分  
5. 取最高分；低于 **30 分** 则用 `generic-daylight-landscape`  

## 新增配方

1. 复制 `generic-daylight-landscape.yaml`  
2. 改 `id`、`match`、`parameters`、`tweak_limits`  
3. 运行 `python scripts/verify_style_recipes.py`  
4. 在 `docs/PROMPT_CHANGELOG.md` 记一笔  
