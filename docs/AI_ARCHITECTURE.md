# AI 模块架构（路径 B）

> **读者：** 改 prompt、改 Provider、改 JSON 校验或 LUT 路由的维护者。  
> **契约：** [`AI_RESPONSE_SCHEMA.md`](./AI_RESPONSE_SCHEMA.md) + [`schemas/style_analysis.v1.1.json`](../schemas/style_analysis.v1.1.json)（v1 见 [`style_analysis.v1.json`](../schemas/style_analysis.v1.json)）  
> **变更审计：** [`PROMPT_CHANGELOG.md`](./PROMPT_CHANGELOG.md)  
> **全项目上下文：** [`CODE_ARCHITECTURE.md`](./CODE_ARCHITECTURE.md)

---

## 1. 边界

Path B **仅**在以下条件同时满足时运行：

1. `MetadataWorker` 判定未能精确识别 LR 编辑数据  
2. `AiConfig.is_ready()` 为真  
3. 用户点击 **开始 AI 分析**

不上传网络的操作：Path A、本地 LUT 烘焙、XMP 写入。

---

## 2. 调用链

**当前默认（单次 AI）：**

```
gui/main_window.run_ai_analysis()
  └─ AiAnalysisWorker.run()                    [gui/workers.py]
       ├─ load_ai_config()
       ├─ create_analyzer(cfg)                  [ai/factory.py]
       │    └─ OpenAiCompatibleProvider(cfg)   [ai/openai_compatible_provider.py]
       │         ├─ _load_prompt()  ← config/prompts/*.txt
       │         ├─ HTTP Vision API (httpx)
       │         ├─ parse_json_content()       [ai/response_parser.py]
       │         └─ normalize_style_analysis() [ai/validator.py]
       │              └─ parameter_registry 白名单 / 范围 / LUT·XMP 标记
       ├─ style_result_to_report()             [ai/service.py]
       └─ build_lut_for_report()               [ai/service.py → lut/lut_generator.py]
```

**路线 B — 配方库 + 双次 AI（`use_recipe_pipeline: true` 时，待接线）：**

见 [`STYLE_RECIPE_SYSTEM.md`](./STYLE_RECIPE_SYSTEM.md)。概要：Call① `style_classify.v1` → `ai/style_recipes.match_recipe()` → Call② `style_analysis_refine`（delta）→ `merge_recipe_with_refine()` → 仍走 `normalize_style_analysis()`。

失败类型：

| 异常 | 含义 |
|------|------|
| `AiNotConfiguredError` | Key 或 model 缺失 |
| `AiAnalysisError` | HTTP 失败、非 JSON、校验失败（含 retry 后） |

---

## 3. 文件职责

| 文件 | 职责 |
|------|------|
| `ai/base.py` | `BaseAiProvider` 协议、异常基类 |
| `ai/factory.py` | 按配置实例化 Provider |
| `ai/openai_compatible_provider.py` | OpenAI 兼容 Chat Completions + 图片 |
| `ai/schema.py` | `StyleAnalysisResult` 数据结构 |
| `ai/response_parser.py` | 从模型文本中提取 JSON |
| `ai/validator.py` | 规范化、clamp、confidence 阈值、warnings |
| `ai/parameter_registry.py` | 参数白名单、数值范围、LUT/XMP 参与规则 |
| `ai/service.py` | AI 结果 → `AiLearningReport` + 内存 LUT |
| `ai/capabilities.py` | Provider 能力常量 |
| `config/ai_config.py` | 加载 yaml、prompt 路径、`lut_min_confidence` 等 |
| `config/provider_presets.py` | 设置页服务商预设（OpenAI / 火山方舟 / 自定义 URL 提示） |
| `config/prompts/style_analysis.txt` | 中文 system prompt |
| `config/prompts/style_analysis.en.txt` | 英文 system prompt |
| `config/prompts/style_classify.txt` | Call① 分类 prompt（路线 B） |
| `config/prompts/style_analysis_refine.txt` | Call② 配方微调 prompt（路线 B） |
| `config/style_recipes/*.yaml` | 风格配方库 |
| `ai/style_recipes.py` | 配方加载、匹配、merge |
| `docs/STYLE_RECIPE_SYSTEM.md` | 路线 B + 双次 AI 设计说明 |

---

## 4. Prompt 加载

配置项（`ai_config.local.yaml` → `analysis`）：

| 键 | 默认 | 说明 |
|----|------|------|
| `language` | `zh-CN` | 影响 user message 语言提示 |
| `prompt_file` | `config/prompts/style_analysis.txt` | 可指向自定义 prompt |

Prompt 正文必须：

1. 声明 schema 版本（当前 **`style_analysis.v1.1`**）  
2. 要求 **仅输出 JSON**（无 markdown 围栏）  
3. 列出允许的 CRS 字段名（与 `parameter_registry` 一致）  
4. 说明哪些字段参与 **LUT 试看** vs **仅 XMP/学习**

---

## 5. 响应处理

```
Raw model text
  → parse_json_content
  → normalize_style_analysis(parsed, cfg)
       ├─ 丢弃未知 key（warning）
       ├─ clamp 到合法范围
       ├─ 应用 lut_min_confidence / xmp_min_confidence
       └─ 设置 ParameterResult.include_in_lut / include_in_xmp
  → StyleAnalysisResult
  → AiLearningReport + optional Lut3D
```

Retry：Provider 内 `max_retries`；重试时在 user message 追加「仅 JSON」提醒。

可选：`use_json_mode`（若 API 支持 JSON mode）。

---

## 6. 与 LUT / XMP 的关系

| 输出 | 来源 | 说明 |
|------|------|------|
| LearningPanel 文案 | `overall_impression`、`editing_steps` | 直接展示 |
| 参数列表 | `parameters` + confidence | 低置信度可仍展示但可能不参与 LUT |
| 内存 LUT | `include_in_lut` 为 true 的参数字典 | 供底片试看 |
| 导出 XMP | `include_in_xmp` | 用户在 ExportDialog 确认路径 |

LUT 最低门槛见 [`AI_RESPONSE_SCHEMA.md`](./AI_RESPONSE_SCHEMA.md) § LUT minimum bar。

---

## 7. 改 Prompt / Schema 标准流程（SOP）

**人读审核 + AI 编码时均应遵守：**

### 7.1 小改（同一 `style_analysis.v1.1`，或仅措辞不改字段）

1. 编辑 `config/prompts/style_analysis.txt`（及 `.en.txt` 若需同步）  
2. 在 [`PROMPT_CHANGELOG.md`](./PROMPT_CHANGELOG.md) 追加条目：**日期、动机、影响字段**  
3. 确认未引入 schema 未声明的新参数 key  
4. 运行 `python scripts/verify_ai_schema.py`  
5. 用 1～3 张样图手动跑 Path B，记录观察（可写在 changelog 或 PR）  
6. Git commit 建议：`prompt(style_analysis.v1.1): <简短说明>`

### 7.2 大改（破坏性 / 新版本号）

1. 复制 `schemas/style_analysis.v1.1.json` → 下一版本，更新 [`AI_RESPONSE_SCHEMA.md`](./AI_RESPONSE_SCHEMA.md)  
2. 更新 `ai/parameter_registry.py`、`ai/validator.py`  
3. 新建 `config/prompts/...` 并引用新版本号  
4. changelog 写 **Migration** 小节  
5. 全量回归 Path B + 导出 + LUT 试看  

### 7.3 禁止

- 只改 prompt 不记 changelog  
- 在 prompt 中新增字段却不更新 registry / schema  
- 提交 `ai_config.local.yaml` 或真实 API Key  

---

## 8. 扩展 Provider

1. 实现 `BaseAiProvider.analyze()` → `StyleAnalysisResult`  
2. 在 `ai/factory.py` 注册  
3. 在 `ai/capabilities.py` 声明能力  
4. 若请求/响应格式不同，仍应归一化为同一 `StyleAnalysisResult`（不要分叉 UI 逻辑）  
5. 更新本文档 §2 调用链与 PRODUCT_SPEC 若涉及用户可见行为  

---

## 9. 相关脚本

| 脚本 | 用途 |
|------|------|
| `scripts/verify_ai_schema.py` | registry ↔ JSON schema 一致性 |
| `scripts/verify_ui.py` | 与 AI 无直接关系；全 app 启动前检查 |

---

## 10. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-30 | 初版：Path B 调用链、SOP、与 schema/changelog 联动 |
