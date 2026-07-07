# 文档索引

> 本目录是项目的**正式文档根**。  
> 改功能前先确认：你要改的是「产品行为」「界面」还是「代码 / AI 契约」——再打开对应文档。

---

## 1. 分层原则

| 层级 | 读者 | 目的 | 代表文件 |
|------|------|------|----------|
| **L0 入口** | 人 + AI | 5 分钟定位「改哪里、读什么」 | 根目录 [`README.md`](../README.md)、[`AGENTS.md`](../AGENTS.md) |
| **L1 人读 · 审核** | 产品 / 维护者 / Code Review | 理解做什么、为什么、改了什么 | 本页下列 L1 文档 |
| **L2 人读 · 实现** | 开发者 / 审核代码结构 | 模块职责、调用链、改 prompt SOP | [`CODE_ARCHITECTURE.md`](./CODE_ARCHITECTURE.md)、[`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) |
| **L3 契约 · 双读** | 人审核 + 代码 / 校验器引用 | 字段、范围、版本；与实现必须一致 | [`AI_RESPONSE_SCHEMA.md`](./AI_RESPONSE_SCHEMA.md)、[`../schemas/`](../schemas/) |
| **L4 机器读** | Provider、validator、脚本 | 运行时输入 / JSON Schema / 校验 | [`config/prompts/`](../config/prompts/)、`schemas/*.json` |
| **L5 AI 规则** | Cursor 等编码 Agent | 改代码时的硬约束（短、可执行） | [`.cursor/rules/`](../.cursor/rules/) |

**分工口诀：**

- **产品能不能做** → `PRODUCT_SPEC_v2.md`
- **界面长什么样、字写什么** → `UI_UX_DESIGN.md` §11 + `gui/copy.py`
- **代码怎么串起来** → `CODE_ARCHITECTURE.md`
- **AI / prompt 怎么改、怎么回溯** → `AI_ARCHITECTURE.md` + `PROMPT_CHANGELOG.md`
- **JSON 长什么样** → `AI_RESPONSE_SCHEMA.md` + `schemas/`
- **Agent 别乱改什么** → `AGENTS.md` + `.cursor/rules/`

---

## 2. L1 — 人读（产品 / 体验 / 变更审计）

| 文档 | 内容 | 何时更新 |
|------|------|----------|
| [`PRODUCT_SPEC_v2.md`](./PRODUCT_SPEC_v2.md) | 产品定位、功能 ID、验收场景、风险 | 新增功能、改路径行为、改验收标准 |
| [`UI_UX_DESIGN.md`](./UI_UX_DESIGN.md) | 布局、状态机、组件、**§11 文案库** | 改界面、改交互、改用户可见文案 |
| [`PROMPT_CHANGELOG.md`](./PROMPT_CHANGELOG.md) | Prompt 版本、变更原因、影响面 | **每次**改 `config/prompts/` 或 bump schema 版本 |
| 根目录 [`README.md`](../README.md) / [`README.zh-CN.md`](../README.zh-CN.md) | 对外概览、安装、v1/v2、路线图 | 发布里程碑、安装方式变化 |

> **审核建议：** PR 涉及 AI 时，除代码 diff 外，应同时审 `PROMPT_CHANGELOG.md` 与 `AI_RESPONSE_SCHEMA.md` 是否同步。

---

## 3. L2 — 人读（代码框架 / 实现）

| 文档 | 内容 | 何时更新 |
|------|------|----------|
| [`CODE_ARCHITECTURE.md`](./CODE_ARCHITECTURE.md) | 全项目模块图、路径 A/B 调用链、配置与导出 | 新增模块、改主流程、改线程模型 |
| [`AI_ARCHITECTURE.md`](./AI_ARCHITECTURE.md) | Path B 专章：Provider → Prompt → 解析 → LUT/XMP | 改 `ai/`、改 prompt 加载、改校验策略 |
| [`STYLE_RECIPE_SYSTEM.md`](./STYLE_RECIPE_SYSTEM.md) | 路线 B：配方库、双次 AI、merge 规则 | 增改配方 YAML、接线双次调用、改匹配/合并逻辑 |

`PRODUCT_SPEC_v2.md` §5–§6 保留**产品向**架构摘要；**实现细节以 L2 为准**，避免两处重复维护长段落。

---

## 4. L3 / L4 — 契约与机器读

| 资产 | 类型 | 说明 |
|------|------|------|
| [`AI_RESPONSE_SCHEMA.md`](./AI_RESPONSE_SCHEMA.md) | 人读契约说明 | 字段表、LUT/XMP 路由、错误行为、版本策略 |
| [`schemas/style_analysis.v1.1.json`](../schemas/style_analysis.v1.1.json) | 机器读 Schema | 当前版本；与 validator / prompt 一致 |
| [`schemas/style_analysis.v1.json`](../schemas/style_analysis.v1.json) | 机器读 Schema | 历史 v1（11 项核心） |
| [`config/prompts/style_analysis.txt`](../config/prompts/style_analysis.txt) | 运行时 Prompt（zh-CN） | 正文可人工审核；须声明 schema 版本 |
| [`config/prompts/style_analysis.en.txt`](../config/prompts/style_analysis.en.txt) | 运行时 Prompt（en） | 同上 |
| [`config/style_recipes/*.yaml`](../config/style_recipes/) | 配方数据 | 路线 B 基准参数 + tweak_limits |
| [`config/prompts/style_classify.txt`](../config/prompts/style_classify.txt) | Call① Prompt | 分类 only；schema `style_classify.v1` |
| [`config/prompts/style_analysis_refine.txt`](../config/prompts/style_analysis_refine.txt) | Call② Prompt | 配方 delta 微调 |
| [`schemas/style_classify.v1.json`](../schemas/style_classify.v1.json) | 机器读 Schema | Call① 分类 JSON |
| [`ai/style_recipes.py`](../ai/style_recipes.py) | 配方加载 / 匹配 / merge | 与 YAML 同步 |
| [`ai/parameter_registry.py`](../ai/parameter_registry.py) | 代码内白名单 | 与 schema、prompt 参数列表一致 |

**版本号：** 当前 **`style_analysis.v1.1`**。破坏性变更 → 新 schema 文件 + 新 prompt 版本段 + changelog 条目。

---

## 5. L5 — AI 编码规则

| 文件 | 作用域 | 作用 |
|------|--------|------|
| [`AGENTS.md`](../AGENTS.md) | 全仓库 | Agent 入口：目录、双路径、改 AI 的检查清单 |
| [`.cursor/rules/project-context.mdc`](../.cursor/rules/project-context.mdc) | 始终生效 | 产品定位、文档指针、UI v1.6 要点 |
| [`.cursor/rules/ai-module.mdc`](../.cursor/rules/ai-module.mdc) | `ai/`、`config/prompts/`、`schemas/`、`docs/AI_*`、`docs/PROMPT_*` | 改 AI / prompt 时的强制同步规则 |
| [`.cursor/rules/ui-copy.mdc`](../.cursor/rules/ui-copy.mdc) | `gui/`、`docs/UI_UX_DESIGN.md` | 界面文案只改 §11 / `copy.py` |

---

## 6. 与代码的映射（速查）

```
main.py → gui/main_window.py
          ├─ MetadataWorker ──→ core/metadata_*     （路径 A）
          └─ AiAnalysisWorker ─→ ai/* → lut/*       （路径 B）
gui/copy.py          ← UI_UX_DESIGN.md §11
config/ai_config.*   ← 用户 API（local 不入库）
scripts/verify_ui.py ← 启动前 UI 版本检查
scripts/verify_ai_schema.py ← schema / registry 一致性（可选）
```

---

## 7. 文档维护约定

1. **一处权威：** 同一事实只在一类文档里写全；其它文档用链接引用。  
2. **先文档后代码（AI / prompt）：** 改 prompt 或 schema 前更新 changelog；改完跑校验脚本。  
3. **Git 追溯：** prompt 变更使用独立 commit，message 建议 `prompt(style_analysis.v1.1): …` 或 `feat(ai): …`。  
4. **不提交：** `config/ai_config.local.yaml`、测试图片、含真实 Key 的文件。

---

## 8. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-02 | schema v1.1、服务商预设、试看区滚动/分割；README 当前状态 |
| 2026-06-30 | 初版：建立 L0–L5 分层与索引 |
