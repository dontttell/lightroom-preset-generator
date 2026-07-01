# Lightroom 预设学习器 — 产品功能与实现规格（v2）

> 文档版本：v2.7.3  
> 状态：待开发（规格定稿，部分 UI 已实现 v2）  
> 目标用户：想学习调色的摄影爱好者  
> **UI/UX 专文档：** [UI_UX_DESIGN.md](./UI_UX_DESIGN.md)（布局、组件、色彩、状态机 — **改界面请先读此文档**）  
> **界面文案主库：** 同上 **[§11 文案库](./UI_UX_DESIGN.md#11-文案规范与文案库copy-deck)** — 产品规格不重复维护字句  
> **代码 / AI 实现：** [docs/README.md](./README.md) → [CODE_ARCHITECTURE.md](./CODE_ARCHITECTURE.md)、[AI_ARCHITECTURE.md](./AI_ARCHITECTURE.md)  
> **编码 Agent：** [AGENTS.md](../AGENTS.md)

---

## 1. 产品定位


| 项目      | 说明                                         |
| ------- | ------------------------------------------ |
| 产品名（建议） | Lightroom 预设学习器 / Lightroom Preset Learner |
| 核心价值    | 从成片反推 LR 调色方法：精确提取或 AI 辅助学习                |
| 不是      | 一键滤镜工具、面向普通大众的应用                           |


**两条路径：**

- **路径 A（精确学习）**：图片含 Lightroom metadata → 读取真实 Camera Raw 参数 → 导出精确 XMP  
- **路径 B（AI 辅助学习）**：无 metadata → AI 解读风格 + 修改思路 + 参考参数 → 可选导出参考 XMP / LUT

**导出原则：** 分析结果仅在内存/界面展示；**用户点击「导出」才写入磁盘**。

---

## 2. 现状 vs 目标（差距分析）

### 2.1 已有能力（v1）


| 模块  | 现状                                              |
| --- | ----------------------------------------------- |
| GUI | PyQt6 主窗口、图片预览、参数列表、工具栏                         |
| 分析  | 10 个规则分析器（全局统计 → 推测 LR 参数）                      |
| 导出  | XMP 生成（`generators/xmp_generator.py`）           |
| 预览  | OpenCV 近似 XMP 滑块（`preview/preset_simulator.py`） |
| 配置  | `config/settings.py`（模块开关，无 AI 配置）              |




### 2.2 主要问题

1. **未检测 metadata**，有 LR 导出图仍走规则推测（效果差）
2. **规则推测作为默认路径**，与「精确提取」定位冲突
3. **UI 面向 Debug**（参数列表、缺失提示、统计区常驻）
4. **无 AI 接入**、无 LUT 生成与导出
5. **预览语义错误**（「原图 vs 模拟」；用户上传的已是成片）
6. **打开即分析/导出逻辑**需改为「用户确认 + 手动导出」



### 2.3 v2 目标

见下文功能清单与模块划分。

---



## 3. v1.0 功能清单



### 3.1 必须实现（P0）


| ID  | 功能           | 说明                                          |
| --- | ------------ | ------------------------------------------- |
| F01 | 图片导入         | 支持 JPG / JPEG / PNG / WebP；拖拽 + 文件对话框       |
| F02 | Metadata 检测  | 上传后自动检测是否含 Adobe Camera Raw / Lightroom XMP |
| F03 | 路径 A：精确提取    | 解析 metadata → 按 LR 面板分组展示参数 → 标签「精确提取」      |
| F04 | 路径 A：导出      | 用户点击「导出…」；默认仅 XMP；可选勾选「同时导出 LUT」（见 §4.4） |
| F05 | 路径 B：AI 确认门  | 无 metadata 时提示；用户点击「开始 AI 分析」才调用 API        |
| F06 | 路径 B：AI 风格解读 | 返回：整体印象、分步修改思路、参考参数（带置信度）                   |
| F07 | 路径 B：参考 XMP  | 由 AI JSON 转 XMP（标注「AI 参考 · 推测」）             |
| F08 | LUT 生成（本地）   | 由参数字典烘焙 33³ LUT 至内存；路径 B 在 AI 分析后；路径 A 在用户勾选导出 LUT 时 |
| F09 | 路径 B：导出      | 用户在导出对话框勾选参考 XMP / LUT（可单选或双选），点击确认后写盘 |
| F10 | 设置页          | **API Key、Base URL（可选）、模型名称**（默认全空）；测试连接；**不设「服务商」字段** |
| F11 | 不默认导出        | 全流程无自动写文件                                   |
| F12 | 状态标签         | 状态栏/卡片显示：`精确提取` 或 `AI 参考分析`                 |




### 3.2 应该实现（P1）


| ID  | 功能            | 说明                                      |
| --- | ------------- | --------------------------------------- |
| F13 | 底片 LUT 预览     | 左栏参考图在上 + 底片预览在下 + 右栏试看控制卡（UI §3.4）；本地 3D LUT 查表（路径 B 为主） |
| F14 | 导出对话框         | 预设名称、勾选 XMP/LUT、各自保存路径（预设名从主界面移入此处） |
| F16 | AI 未配置可见提醒 | **三层提醒**（状态栏红标 + 顶栏 Banner + 路径 B 红色 StatusCard/InlineAlert）；详见 [UI_UX_DESIGN.md §6.8](./UI_UX_DESIGN.md#68-ai-未配置提醒aiconfigreminder定稿) |
| F23 | UI 控件去重        | 设置单入口；主操作仅工具栏；见 §7.3 |
| F24 | UI 轻量美化（L1）   | 全局 QSS、卡片化 StatusCard；底片试看见 UI §3.4 |
| F25 | AI 未配置提醒 UI    | 与 F16 同规格；实现见 UI 文档 §6.8 |
| F17 | 隐私说明          | 明确 AI 路径会上传图片至所选服务商；设置页可链接 OpenAI 隐私政策 |




### 3.3 可选 / v1.1（P2）


| ID  | 功能                | 说明                        |
| --- | ----------------- | ------------------------- |
| F19 | 导出学习笔记            | Markdown：思路 + 参数          |
| F20 | XMP 近似预览          | 底片 + 参考 XMP（OpenCV，标注近似）  |
| F21 | 部分 metadata 降级    | 字段不全时列出可读/缺失项             |
| F22 | 规则引擎 fallback     | 仅当 AI 失败且用户同意时（需明确标注，非默认） |

> **说明：** 原 F18「metadata 路径可选 LUT」已并入 **F04 / §4.4**，不再单独列为 P2。




### 3.4 明确不做（v1）

- 批量处理、工程文件、历史记录  
- 嵌入 Lightroom / Camera Raw 引擎  
- 从单张成片「还原修前原图」  
- 自训练深度学习模型  
- 打开图片即自动 AI 分析

---



## 4. 用户流程



### 4.1 主流程

```
[打开图片]
     │
     ▼
[Metadata 检测] ──后台线程，不阻塞 UI──
     │
 ┌───┴───┐
 │       │
有       无
 │       │
 ▼       ▼
路径 A   路径 B
 │       │
 │       ├─ 显示说明 + 「开始 AI 分析」（需已配置 API）
 │       ├─ 用户确认 → 调用 AI → 展示思路 + 参数 + 内存 LUT
 │       │
 ▼       ▼
展示精确参数   展示 AI 学习面板
 │       │
 │       └─ [可选] 右栏试看控制卡 → 左栏参考图下方底片/LUT 对比（UI §3.4）
 │
 ▼
[导出…] ← 用户主动触发，勾选格式，选路径
```



### 4.2 路径 A 界面要点

- 状态卡片：「已精确识别 Lightroom 编辑数据」  
- 图片区：当前成片（即最终效果，不做假 Before/After）  
- 学习面板：按 LR 面板分组的全量参数  
- 主按钮：**「导出…」**（与路径 B 同一入口，不单独增设「导出 LUT」按钮）  
- 导出默认：**仅 XMP**；LUT 为导出对话框内**高级可选项**（见 §4.4）  
- 无强制预览步骤



### 4.3 路径 B 界面要点

- 状态卡片：「未能精确识别 · 可使用 AI 辅助学习」  
  - **API 未配置时：** 左边条改为**红色**，文案强调「AI 服务未配置」+「前往设置」（见 UI §6.8）  
- 图片区：参考风格图  
- 学习面板（分析后）：  
  1. 整体印象（自然语言）
  2. 修改思路（分步骤教程）
  3. 参考参数（分组 + 置信度 + 「建议优先调整」高亮）
- **API 未配置时：** LearningPanel 顶部显示红色 InlineAlert + Banner/状态栏常驻提醒  
- 主按钮：`导出…`（勾选 XMP / LUT）；**「开始 AI 分析」禁用直至配置完成**  
- 试看（v1.4）：右栏「在自己的底片上试看」控制卡 → 参考图保持可见，底片预览在下方对比（需先完成 AI 分析，见 UI §3.4）

### 4.3.1 AI 未配置时的全局提醒（产品定稿）

无论是否已打开图片，只要 `AiConfig.is_ready() == False`：

| 层级 | 位置 | 行为 |
|------|------|------|
| L1 | 状态栏 | 红色 `● AI 未配置`，可点击进设置 |
| L2 | 主工具栏下方 Banner | ⚠ + 说明 +「前往设置」；配置后隐藏 |
| L3 | 路径 B 专用 | 红色 StatusCard + LearningPanel InlineAlert |

**路径 A（已精确识别）** 不显示 L3，避免干扰精确提取；L1/L2 仍显示，提示用户「将来未能精确识别的图需先配 AI」。

完整视觉与交互见 **[UI_UX_DESIGN.md §6.8](./UI_UX_DESIGN.md#68-ai-未配置提醒aiconfigreminder定稿)**。

---

### 4.4 产品设计决策：路径 A 是否提供 LUT 导出？

**结论：提供，但不作为主按钮；与路径 B 共用「导出…」对话框，LUT 为默认不勾选的可选项。**

| 考量 | 说明 |
|------|------|
| 用户是谁 | 摄影爱好者；在 LR 里学滑块仍是主诉求，**XMP 是权威输出** |
| LUT 的价值 | 跨软件（PR / 达芬奇）、快速套 look、配合底片试看 |
| LUT 的局限 | 由 XMP 参数经**本地简化公式**烘焙，≠ Adobe 引擎，≠ 100% 还原 LR |
| 单独「导出 LUT」按钮 | **不需要** — 避免路径 A/B 两套入口，增加「哪个为准」的困惑 |

**路径 A 导出对话框（定稿）：**

```
预设名称  [____________]
☑ 导出 XMP 预设          ← 默认勾选
☐ 同时导出 LUT (.cube)   ← 默认不勾选，归入「高级/可选」
   ⓘ 由当前 XMP 参数本地烘焙，供跨软件使用；学习调色请以 XMP 为准

XMP 保存路径  [________] [浏览…]
LUT 保存路径  [________] [浏览…]   （仅在上项勾选时显示）
```

**为何不默认提供 LUT：**

1. 精确 metadata 场景下，用户要的是**可编辑滑块**，不是颜色表  
2. 烘焙 LUT 多一步近似误差，不应与「精确提取」并列为主输出  
3. 保持路径 A 界面简洁；有跨软件需求的用户可自行勾选  

**底片 LUT 预览（路径 A）：** 若用户在本次会话中勾选了 LUT 导出（或触发了 LUT 烘焙），折叠区可启用预览；**v1 不强制**，与 F13 一致，优先级低于路径 B。

---

### 4.5 产品设计决策：设置页是否需要「服务商」字段？

**结论：v1 设置页不显示「服务商」；统一按 OpenAI 兼容 Vision API 配置即可。**

| 字段 | v1 是否保留 | 说明 |
|------|-------------|------|
| ~~服务商~~ | **否** | 与 Base URL 信息重复；`openai` / `custom` 对爱好者无清晰区分 |
| **API Key** | 是 | 必填（启用 AI 时） |
| **API Base URL** | 是 | 可选；留空 = OpenAI 官方默认地址；填 URL = 兼容中转/本地网关 |
| **模型名称** | 是 | 必填（启用 AI 时）；如 `gpt-4o-mini` |

**理由：**

- v1 仅实现一种调用方式：`POST {base_url}/chat/completions` + 图片 Vision  
- 用户真正关心的是 **Key + 地址 + 模型**，不是抽象「服务商」标签  
- 将来若支持 Claude 原生 API 等非兼容协议，再在「高级」中增加 **API 类型**（P2），而非 v1 必填下拉  

**设置页布局（定稿）：**

```
API Key        [ ************ ]
API Base URL   [ 留空则使用 OpenAI 默认 ]   （可选）
模型名称       [ 例如 gpt-4o-mini ]
[ 测试连接 ]

ⓘ 使用 OpenAI 兼容的 Vision API；图片将上传至 Base URL 对应服务。
```

配置文件同步去掉 `provider` 对外要求（实现层可保留内部默认值，文档不再要求用户填写）。

---



## 5. 系统架构（目标模块）

```
lightroom_preset_generator/
├── main.py
├── config/
│   ├── settings.py          # 扩展：AI、UI、导出默认值
│   ├── ai_config.yaml       # 用户 AI 配置（.gitignore）
│   └── prompts/
│       └── style_analysis.txt
├── core/
│   ├── inference_result.py  # 扩展：AnalysisMode, AiLearningReport
│   ├── metadata_detector.py # 【新】检测 JPG/XMP sidecar 是否含 crs 数据
│   ├── metadata_parser.py   # 【新】解析 crs 字段 → ParameterResult 列表
│   └── pipeline.py          # 【改】先 metadata，无则标记 AI 路径
├── generators/
│   └── xmp_generator.py     # 【改】支持精确参数 & AI 参考参数
├── ai/
│   ├── base.py              # 【新】AiStyleAnalyzer 协议
│   ├── openai_provider.py   # 【新】
│   ├── factory.py           # 【新】按配置创建 provider
│   └── schema.py            # 【新】StyleAnalysisResult dataclass
├── lut/
│   ├── lut_generator.py     # 【新】StyleProfile → 33³ cube
│   └── lut_applier.py       # 【新】3D LUT 三线性插值（OpenCV/NumPy）
├── gui/
│   ├── main_window.py       # 【大改】双路径 UI、导出对话框
│   ├── settings_dialog.py   # 【新】AI 配置
│   ├── widgets.py           # 【改】LearningPanel, StatusCard, ExportDialog
│   └── workers.py           # 【新】MetadataWorker, AiAnalysisWorker
├── preview/
│   └── preset_simulator.py  # 【保留】v1.1 XMP 近似预览可选
└── analyzers/               # 【保留但降级】v1 默认不走规则推测主路径
```

---



## 6. 核心实现逻辑



### 6.1 Metadata 检测（F02）

**输入：** 图片路径  
**输出：** `MetadataScanResult`

```python
@dataclass
class MetadataScanResult:
    has_lightroom_metadata: bool
    source: Literal["embedded_xmp", "sidecar_xmp", "none"]
    raw_xmp_bytes: Optional[bytes]
    crs_fields: Dict[str, Any]   # 解析后的 crs 键值
    message: str
```

**检测顺序：**

1. 读 JPG/PNG 内嵌 XMP（优先纯 Python 解析 `APP1` 段）
2. 同目录查找 `{stem}.xmp` sidecar（**仅当用户打开的是 JPG 且 sidecar 在同文件夹**）
3. 检查是否含 `crs:` 命名空间及 `crs:HasSettings=True` 或关键 Develop 字段

**判定为「有 metadata」的最低条件（建议）：** 至少存在若干核心 crs 字段（如 `Exposure2012` / `Temperature` / `Contrast2012` 等之一），避免空 XMP 误判。

**依赖建议：** 优先纯 Python；解析失败时可选用 ExifTool 作 fallback（可选依赖，不强制用户安装）。

**路径判定：**

- `has_lightroom_metadata == True` → **路径 A**，不调用规则分析器、不调用 AI  
- `False` → **路径 B**，等待用户触发 AI

---



### 6.2 Metadata 解析（F03）

**输入：** `MetadataScanResult.crs_fields`  
**输出：** `List[ParameterResult]`，`status=OK`，`confidence=1.0`，标签「精确提取」

**分组映射（GUI 展示）：**


| LR 面板 | crs 字段示例                                                                        |
| ----- | ------------------------------------------------------------------------------- |
| 基础    | Exposure2012, Contrast2012, Highlights2012, Shadows2012, Whites2012, Blacks2012 |
| 颜色    | Temperature, Tint, Vibrance, Saturation                                         |
| 分离色调  | SplitToning*                                                                    |
| 细节    | Sharpness, Clarity2012, ...                                                     |
| 效果    | PostCropVignette*, Grain*                                                       |


**XMP 导出：** 直接使用解析字段 + 标准 preset 头（UUID、ProcessVersion 等）。

---



### 6.3 AI 分析（F05–F08）

**触发条件：** 无 metadata + 用户点击「开始 AI 分析」+ API 已配置  

**Provider 抽象：**

```python
class AiStyleAnalyzer(Protocol):
    def analyze(self, image_path: str) -> StyleAnalysisResult: ...
```

**StyleAnalysisResult（**`ai/schema.py`**）：**

```json
{
  "overall_impression": "偏暖、低对比、阴影略抬...",
  "editing_steps": [
    {"step": 1, "title": "白平衡", "description": "..."},
    {"step": 2, "title": "影调", "description": "..."}
  ],
  "priority_adjustments": ["Temperature", "Shadows2012", "Saturation"],
  "parameters": {
    "Exposure2012": {"value": 0.3, "confidence": 0.65},
    "Temperature": {"value": 6000, "confidence": 0.7}
  },
  "style_summary_en": "optional"
}
```

**配置（**`config/ai_config.example.yaml`**）— 默认全部留空：**

```yaml
api_key: ""
base_url: ""    # 留空 → OpenAI 官方默认 endpoint
model: ""

analysis:
  language: zh-CN
  prompt_file: config/prompts/style_analysis.txt
```

用户保存至 `config/ai_config.local.yaml` 或在软件「设置」中填写。**留空时路径 B 不可用，路径 A 与 LUT 本地烘焙/预览不受影响。**

**就绪条件（**`AiConfig.is_ready()`**）：** `api_key`（或环境变量）与 `model` 非空；`base_url` 可空。

**流程：**

1. 读取配置 → `factory.create_analyzer()`
2. 后台线程上传图片 + prompt → 解析 JSON
3. 校验 schema → 转 `ParameterResult`（status=OK, 标签「AI 参考 · 推测」）
4. 调用 `LutGenerator.from_style_profile()` → 内存 `Lut3D`
5. UI 展示思路 + 参数；**不写文件**

**v1 API 形态：** 统一 OpenAI 兼容 Vision API；不在 UI 暴露「服务商」选择。

---



### 6.4 LUT 生成（F08）

**实现：** `lut/lut_generator.py`  
**输入：** 参数字典 — 路径 B 来自 AI；路径 A 来自 metadata 解析的 crs 字段（用户勾选导出 LUT 时）  
**输出：** `numpy.ndarray` shape `(size, size, size, 3)`，默认 size=33  

**方法：**

1. 在 RGB 网格 [0,1]³ 上逐点应用简化调色公式（与现有 `preset_simulator` 类似但系统化）
2. 顺序：曝光 → 对比 → 色温/色调 → 饱和 → 分离色调（简化）→ clamp
3. 可选写入 `.cube`（Export 时）

**注意：** 这是 **本地确定性算法**，不是 LR 引擎，不是 AI。

---



### 6.5 底片 LUT 预览（F13）

**实现：** `lut/lut_applier.py`  
**输入：** 底片 BGR + 内存 `Lut3D`  
**输出：** 应用 LUT 后的 BGR  

**算法：** 3D LUT 三线性插值（OpenCV / NumPy）  

```
对每个像素 (r,g,b) ∈ [0,1]:
  在 LUT 立方体中 trilinear_interpolate → (r',g',b')
```

**UI：**

- 布局与交互见 **[UI_UX_DESIGN.md §3.4](./UI_UX_DESIGN.md#34-底片试看布局定稿-v14)**（v1.5：参考图在上 + 底片预览在下；**AI 完成后左栏默认可见**，见 §3.4.6）  
- 文案 key：`plate.*`、`status.lut_preview_ok`（§11）  
- 仅路径 B 且已有内存 LUT 时启用  
- 免责声明：§11 `plate.footnote`

**不调用：** Lightroom、AI  

---



### 6.6 导出（F04, F09, F11, F14）

**触发：** 用户点击「导出…」  

**导出路径：** **必须由用户选择** — 通过系统「另存为」对话框或导出窗内的「浏览…」指定完整保存路径（含目录与文件名）。程序**不会**在未确认路径的情况下写入默认目录。

**对话框字段：**

- 预设名称  
- **路径 A：**  
  - ☑ 导出 XMP（默认勾选）→ XMP 保存路径  
  - ☐ 同时导出 LUT（**默认不勾选**）→ LUT 保存路径；勾选时才显示路径行  
- **路径 B：**  
  - ☑ 参考 XMP（默认勾选）  
  - ☐ LUT（默认不勾选，分析完成后可勾选）  
  - 各自独立路径，均可「浏览…」修改  
- 确认后才会写盘  

**路径 A / B 共用同一「导出…」按钮，不单独提供「导出 LUT」主按钮。**

**逻辑：**

- 仅勾选且用户确认路径后调用 `XMPGenerator.save()` / `LutGenerator.save_cube()`  
- 导出成功日志 + 状态栏提示

---



## 7. GUI 改造规格

> **完整 UE/UI 设计说明见独立文档：[UI_UX_DESIGN.md](./UI_UX_DESIGN.md)**  
> 本节保留问题清单、去重定稿与实施索引；色彩 Token、组件规格、状态机、快捷键等细节以 UI 文档为准。

### 7.0 当前 UI 问题（v2 实现现状）

| 问题 | 现状 | 影响 |
|------|------|------|
| **设置入口重复** | 顶栏「⚙ 设置」按钮 **+** 菜单「设置 → AI 服务…」 | 同一功能两处入口，显得粗糙 |
| **主操作重复** | 工具栏「打开 / AI / 导出」**+** 右侧面板同名按钮 | 视觉噪音，布局不统一 |
| **打开入口重复** | 菜单「打开图片」+ 工具栏「打开图片」 | 可保留其一或菜单+快捷键即可 |
| **视觉层级弱** | 大量 QGroupBox + 默认系统样式 | 不像摄影类工具，偏「调试面板」 |
| **信息密度不均** | 右侧 QTextEdit 长文 + 顶栏预设名常驻 | 主流程不突出 |

以下 §7.1–§7.5 为**定稿目标布局**（含去重与视觉改版评估）。

---

### 7.1 主窗口布局（v2.4+ / UI v1.3）

**完整线框与尺寸见 [UI_UX_DESIGN.md §3](./UI_UX_DESIGN.md#3-布局规格)。** 要点：

- 左右分栏：**左 = 参考图（上）+ 底片预览（下）**，**右 = StatusCard + LearningPanel + 试看控制卡**
- 取消窗口底部全宽底片预览条（v1.2 已弃用）
- 预设名称在导出对话框内填写

```
┌─────────────────────────────────────────────────────────────┐
│  菜单栏：文件 | 设置 | 帮助                                    │
├─────────────────────────────────────────────────────────────┤
│  [ 打开图片 ]  [ 开始 AI 分析 ]  [ 导出… ]                     │
├────────────────────────────┬────────────────────────────────┤
│  左：参考图（上）/ 底片预览（下） │  StatusCard                  │
│                            │  LearningPanel                 │
│                            │  底片试看控制卡（可折叠）        │
├────────────────────────────┴────────────────────────────────┤
│  状态栏                                                      │
└─────────────────────────────────────────────────────────────┘
```

**预设名称：** 移至 **「导出…」对话框** 内填写，不再占用主界面顶栏（减少一行控件）。

---

### 7.2 设置对话框

- **API Key**（密码框，本地存储）  
- **API Base URL**（可选；留空 = OpenAI 默认）  
- **模型名称**  
- 「测试连接」按钮  
- 隐私说明（图片上传至 Base URL 对应服务）  

**不包含：** 「服务商」下拉（见 §4.5）



### 7.3 控件去重规范（定稿）

**原则：** 每个用户动作 **只有一个主入口**；菜单提供等价路径或快捷键，不与主界面重复堆按钮。

#### 7.3.1 设置入口 — 只保留一处

| 方案 | 建议 |
|------|------|
| A. 仅菜单「设置 → AI 服务…」 | ✅ **推荐（v2.4 定稿）** |
| B. 仅顶栏齿轮按钮 | 可行，但 Windows 用户更习惯菜单 |
| C. 菜单 + 顶栏按钮 | ❌ **当前问题所在，需删除其一** |

**定稿：**

- **保留：** 菜单栏 `设置 → AI 服务…`（可选快捷键 `Ctrl+,`）  
- **删除：** 主界面顶栏「⚙ 设置」按钮（与 `btn_settings` 对应）  
- **状态栏可选：** 显示「● AI 未配置 / ● AI 已配置」（**v2.6 定为必做 L1**，见 UI §6.8）  
- **AiConfigBanner（L2）：** 未配置时在工具栏下常驻，**不可关闭**  

#### 7.3.2 主操作按钮 — 只保留工具栏一组

| 操作 | 定稿入口 | 移除 |
|------|----------|------|
| 打开图片 | 工具栏 + 菜单「文件→打开」+ `Ctrl+O` | — |
| 开始 AI 分析 | **仅工具栏** | 右侧面板底部重复按钮 |
| 导出 | **仅工具栏** + 菜单「文件→导出」+ `Ctrl+S` | 右侧面板底部重复按钮 |

菜单与工具栏并存属桌面软件常规（Lightroom / VS Code 同理）；**同区域两套相同文字按钮**才视为需去重的重复。

#### 7.3.3 去重后代码/module 对应（实施时参考）

| 删除/合并 | 保留 |
|-----------|------|
| `top` 布局中的 `btn_settings` | `settings_menu → open_settings` |
| 右侧 `action_row` 的 `btn_ai`、`btn_export` | 工具栏 `btn_ai`、`btn_export` + menu actions |
| 顶栏「预设名称」输入框 | 移至 `ExportDialog` |

---

### 7.4 视觉改版 — 可操作性评估

**结论：完全可行，且建议在 v2.4 与去重一并做「轻量美化」；不必更换 GUI 框架。**

PyQt6 足以做出整洁的摄影工具风格，无需改为 Electron / Web UI。

#### 7.4.1 可行性分级

| 阶段 | 内容 | 工作量 | 风险 | 建议版本 |
|------|------|--------|------|----------|
| **L1 轻量** | 去重 + 间距 + 统一 QSS 主题 + 预设名移入导出窗 | 1–2 天 | 低 | **v2.4（与去重同期）** |
| **L2 中度** | 深色摄影风、StatusCard/LearningPanel 卡片化、底片试看左栏对比（UI §3.4）、图标 | 2–4 天 | 低 | v2.5 |
| **L3 重度** | 自定义控件、动画、仿 LR 面板树 | 1–2 周 | 中 | 非 MVP，暂不规划 |

**推荐目标：** L1 + 部分 L2（深色主题 + 卡片），在爱好者工具中达到「专业但不花哨」即可，不必复刻 Lightroom。

#### 7.4.2 参考方向（摄影 / 调色类工具）

| 参考 | 可借鉴 | 不照搬 |
|------|--------|--------|
| **Lightroom Classic** | 深色背景、图像区突出、右侧信息面板、状态清晰 | 复杂面板树、双模式 Develop |
| **Capture One** | 克制配色、大预览 | 商业级布局密度 |
| **DaVinci Resolve** | 工具栏图标化、折叠 Inspector | 视频时间线 |
| **macOS 原生工具** | 留白、单一主操作条 | — |

**本产品定位：** 轻量「预设学习器」，不是完整修图软件 — 界面应 **比 LR 简单一个数量级**。

#### 7.4.3 L1 具体改动清单（文档定稿，待编码）

| 项 | 说明 |
|----|------|
| 全局 QSS | 单文件 `gui/styles/app_dark.qss` 或 `app_light.qss`；中性灰背景 `#1e1e1e` / 卡片 `#2d2d2d` |
| 字体 | 中文：系统 UI 字体；代码/参数：`Consolas` / `Cascadia Mono` |
| 预览区 | 圆角 4–6px、浅边框；空状态居中提示「拖入图片或点击打开」 |
| StatusCard | 固定高度、左侧色条（绿=精确 / 橙=待 AI / 紫=AI 完成） |
| LearningPanel | 分组标题加粗；参数行适当行高；AI 思路与参数分区 |
| 底片试看 | 仅左栏 `ImageZone` 参考图下方预览区（UI §3.4 v1.6）；启动即显示，LUT 未就绪时按钮禁用 | v1.6 |
| 按钮 | Primary（导出）、Secondary（AI 分析）、Ghost（选择底片）；避免 emoji 与文字混用 |
| 窗口标题 | 菜单栏显示应用名即可，不再在内容区重复大标题 |

#### 7.4.4 技术实现方式（仍用 PyQt6）

```
gui/
├── styles/
│   ├── app_dark.qss      # L1/L2 主题
│   └── tokens.py         # 颜色/间距常量（可选）
├── widgets.py            # StatusCard / LearningPanel 样式增强
└── main_window.py        # 去重后的单一工具栏布局
```

- **不引入** Qt Quick / QML（重写成本高）  
- **可选** `qtawesome` 或 SVG 图标（L2，小依赖）  
- **主题切换** light/dark 可放「设置 → 外观」（P2）

#### 7.4.5 美观改版的风险与边界

| 风险 | 对策 |
|------|------|
| QSS 维护难 | 集中单文件 + 设计 token |
| 深色主题下图片预览失真 | 预览区外框深色，图片本身不改色 |
| 过度设计拖慢 MVP | L1 必做，L2 只做 StatusCard + 全局深色 |
| 与功能开发冲突 | **先去重（§7.3），再套 QSS（§7.4.3）**，不改业务逻辑 |

---

### 7.5 移除 / 降级（相对 v1 / v2 初版 UI）


| v1 元素          | v2.4 处理                       |
| -------------- | --------------------------- |
| 顶栏「⚙ 设置」按钮 | **删除**；仅保留菜单「设置 → AI 服务…」 |
| 右侧底部 AI / 导出按钮 | **删除**；仅保留工具栏一组 |
| 顶栏「预设名称」常驻 | **移至导出对话框** |
| 工具栏「开始分析」      | 路径 A 自动检测；路径 B 为「开始 AI 分析」 |
| 常驻参数列表 + 缺失提示  | 改为 LearningPanel，按路径展示      |
| Debug 统计区      | 已移除                |
| 「预览效果」（XMP 模拟） | 路径 A 移除；路径 B 改为 LUT 底片预览    |
| 打开即规则分析          | 已改为 metadata 优先分支  |
| 默认系统灰样式 | L1 QSS 深色摄影风（§7.4.3） |


---



## 8. 数据流与线程模型


| 操作             | 线程                         | 说明               |
| -------------- | -------------------------- | ---------------- |
| Metadata 检测/解析 | `MetadataWorker`           | 打开图片后自动          |
| AI 分析          | `AiAnalysisWorker`         | 用户确认后            |
| LUT 烘焙         | 可在 AI worker 内或主线程（33³ 很快） |                  |
| LUT 预览         | 主线程或 `PreviewWorker`       | 底片可能较大，建议 worker |
| 导出             | 主线程                        | 写文件              |


---



## 9. 依赖变更

```text
# 新增（建议）
openai>=1.0.0          # 或 httpx 自行调 API
pyyaml>=6.0            # ai_config.yaml
# 可选
exifread 或 pyexiv2     # metadata 解析备选
```

`requirements.txt` 在开发阶段更新。

---



## 10. 文件与配置安全


| 文件                              | Git                                    |
| ------------------------------- | -------------------------------------- |
| `config/ai_config.example.yaml` | 提交仓库（无真实 Key）                         |
| `config/ai_config.local.yaml`   | .gitignore，用户本地配置                      |
| 用户 API Key                      | 仅本地；优先读环境变量 `OPENAI_API_KEY`          |


---

## 11. AI 服务、费用与 Cursor 说明

### 11.1 Cursor 能否替代 OpenAI API？

**不能。** 两者是不同东西：

| | Cursor 内置 AI | 本软件调用的 OpenAI API |
|--|----------------|-------------------------|
| 用途 | 在 IDE 里帮你写代码、聊天 | 用户运行程序时分析照片 |
| 计费 | Cursor 订阅（Pro 等） | **OpenAI 账户按量计费** |
| 能否给本软件用 | ❌ 不能嵌入 PyQt 程序 | ✅ 需在设置里填用户自己的 API Key |

结论：**验证 AI 路径、开发测试、最终用户使用，都需要自备 OpenAI（或兼容）API Key；Cursor 订阅不覆盖这部分。**

### 11.2 验证阶段会不会花钱？

**会，但很少（若用 gpt-4o-mini）。**

| 操作 | 是否计费 | 粗算 |
|------|----------|------|
| 路径 A（metadata 精确提取） | ❌ | ¥0 |
| 路径 B 单次 AI 分析 | ✅ | 约 ¥0.02–0.15 / 张 |
| 设置页「测试连接」 | ✅（极小） | 可忽略 |
| LUT 生成 / 底片预览 / 导出 | ❌ 本地 | ¥0 |

**建议验证预算：** 在 [OpenAI Platform](https://platform.openai.com/) 充值 **$5–10**（约 ¥35–70），可支撑数百次分析；仅测 Phase 1（metadata）则 **$0**。建议设置 Usage limit 防误触。

### 11.3 如何获取 API Key

1. 注册 OpenAI Platform → 绑定支付方式  
2. 创建 API Key  
3. 填入软件设置页或环境变量 `OPENAI_API_KEY`  
4. **不要** 提交到 GitHub  

### 11.4 费用归属（v1）

- **开发者自测：** 开发者自己的 OpenAI 账户  
- **爱好者使用：** 用户自己的 Key（设置页配置）  
- v1 不内置、不分摊 API 费用  

---

## 12. 开发阶段划分



### Phase 1 — 精确路径（约 3–5 天）

- [ ] `metadata_detector.py` + `metadata_parser.py`  
- [ ] 主窗口路径 A UI + 精确导出  
- [ ] 移除「打开即规则分析」为默认行为  



### Phase 2 — AI 路径（约 4–6 天）

- [ ] 设置页 + `ai_config`  
- [ ] OpenAI provider + prompt + schema  
- [ ] 路径 B UI（思路 + 参数）  
- [ ] 参考 XMP 导出  



### Phase 3 — LUT（约 2–3 天）

- [ ] `lut_generator.py` + `lut_applier.py`  
- [ ] 内存 LUT + 导出 .cube  
- [ ] 底片试看 UI v1.5（UI §3.4.6：AI 完成后左栏默认显示底片区 + 双按钮；见 §3.4.5 差距说明）  



### Phase 4 — 打磨（约 2 天）

- [ ] 导出对话框、文案、错误处理  
- [ ] 测试连接、隐私说明文案  
- [ ] 手动测试矩阵（见 §13）  

### Phase 5 — UI 去重与轻量美化（约 1–2 天，可与 Phase 4 并行）

- [x] §7.3 控件去重（设置单入口、移除右侧重复按钮、预设名移入导出窗）  
- [x] §7.4.3 L1 QSS 主题 + StatusCard / 预览区样式  
- [x] **UI §3.4.6 底片试看可见性**（v1.5 已编码）  
- [x] **UI §6.8 AI 未配置三层提醒**（Banner + 状态栏红标 + 路径 B InlineAlert）  

**合计估算：** 约 12–18 人天（单人，含 Phase 5）  

---



## 13. 验收标准



### 路径 A


| #   | 用例                    | 预期                 |
| --- | --------------------- | ------------------ |
| A1  | LR 导出 JPG（含 metadata） | 显示「精确提取」，参数与 LR 一致 |
| A2  | 点击导出 XMP              | 导入 LR 后滑块与源一致      |
| A3  | 无 metadata 图          | 不走路径 A             |




### 路径 B


| #   | 用例                | 预期                       |
| --- | ----------------- | ------------------------ |
| B1  | 无 metadata，未配 API | Banner + 状态栏红标 + 红色 StatusCard/InlineAlert；「开始 AI 分析」禁用；点击「前往设置」可打开设置 |
| B1a | 启动且未配 API | 无图片时仍显示 L1+L2 Banner/状态栏 |
| B1b | 路径 A + 未配 API | L1+L2 显示；StatusCard 仍为绿色精确态，无 L3 |
| B2  | 配置 API，用户确认分析     | 展示思路 + 参数 + 置信度          |
| B3  | 导出 XMP + LUT      | 文件可导入 LR / 其他软件          |
| B4  | 选底片 LUT 预览        | AI 完成后**无需手动展开**右栏；左栏即见「上传底片」「应用 LUT 预览」；本地 Before/After（UI §3.4.6） |
| B4a | 路径 A 图              | **无**底片试看 UI（左栏仅当前图） |
| B4b | 路径 B AI 完成默认态   | 左栏参考图 + 底片预览区**同时可见** |
| B5  | 未点导出              | 磁盘无新文件                   |


---



## 14. 风险与对策


| 风险             | 对策                           |
| -------------- | ---------------------------- |
| metadata 解析兼容性 | 多样本测试；ExifTool 作为 fallback   |
| AI JSON 格式不稳定  | strict schema + retry + 错误提示 |
| LUT 与 LR 视觉差异  | UI 明确免责声明                    |
| API 费用         | 用户自备 Key；确认门控                |
| 规则分析器闲置        | 保留代码，v1 不暴露为主入口              |


---



## 15. 术语表


| 术语         | 含义                                 |
| ---------- | ---------------------------------- |
| 参考风格图      | 用户上传的无 metadata 成片，代表目标 look       |
| 底片         | 用户另选的未修图，用于试 LUT                   |
| 精确提取       | 来自 embedded/sidecar XMP 的真实 crs 参数 |
| AI 参考 · 推测 | AI 推断参数，非 ground truth             |
| LUT 预览     | 本地 3D LUT 查表，非 LR 引擎               |


---



## 16. 修订记录


| 版本   | 日期         | 说明                        |
| ---- | ---------- | ------------------------- |
| v2.0 | 2026-06-30 | 初始规格：双路径、AI、LUT、底片预览、手动导出 |
| v2.1 | 2026-06-30 | 补充 AI 费用/Cursor 说明；修正文档笔误与 F15 删除 |
| v2.2 | 2026-06-30 | 明确导出路径必选；API 默认留空；补充可运行性保障策略 §17 |
| v2.3 | 2026-06-30 | §4.4 路径 A LUT 导出决策；§4.5 移除「服务商」字段；F04/F08/F10 同步 |
| v2.4 | 2026-06-30 | §7.3 控件去重；§7.4 视觉改版评估；F23/F24；Phase 5 |
| v2.5 | 2026-06-30 | 新增独立 [UI_UX_DESIGN.md](./UI_UX_DESIGN.md)；§7 改为索引 |
| v2.7.3 | 2026-06-30 | UI §3.4.5–§3.4.6：v1.4 可见性差距与 v1.5 验收；Phase 5 底片项改回待办 |
| v2.7.2 | 2026-06-30 | 底片预览改参考图下方（UI §3.4 v1.4）；上传底片按钮 |
| v2.7.1 | 2026-06-30 | 与 UI v1.3.1 交叉校对；§6.5/§7.4/F24/Phase 5 同步 |
| v2.7 | 2026-06-30 | 底片试看布局改 UI §3.4；文案统一引用 UI §11 |
| v2.6 | 2026-06-30 | F16/F25 AI 未配置三层提醒；§4.3.1；验收 B1a/b；UI §6.8 |


---

## 17. 可运行性保障策略（无 API 时如何保证软件可用）

### 17.1 设计原则

| 原则 | 实现 |
|------|------|
| **API 可选** | `AiConfig.is_ready()` 为 False 时不创建 Provider、不发起网络请求 |
| **启动零依赖** | 启动不读 API、不 ping 网络；metadata 路径立即可用 |
| **失败可理解** | 未配置 → 引导设置；已配置但失败 → 明确错误，不 crash |
| **模块隔离** | metadata / AI / LUT / 导出 各自独立，单模块缺失不拖垮全局 |

### 17.2 无 API 时可用的功能

- 打开图片、metadata 自动检测  
- 路径 A：精确参数展示 + 导出 XMP（用户自选路径）  
- 设置页打开与保存（空配置合法）  
- 程序正常退出  

### 17.3 无 API 时不可用但可感知的功能

- 「开始 AI 分析」按钮禁用（路径 B）  
- **页面常驻提醒：** 状态栏红色 `● AI 未配置` + 工具栏下 AiConfigBanner（见 UI §6.8）  
- 路径 B 导出 / LUT / 底片 LUT 预览（需先 AI 分析）  

### 17.4 开发者自测清单（无需 API Key）

1. `python main.py` 启动无报错  
2. 打开含 metadata 的 LR 导出 JPG → 显示「精确提取」→ 导出 XMP  
3. 打开无 metadata 图 → AI 未配置提醒可见（Banner + 红 StatusCard）；按钮禁用  
4. 打开含 metadata 图 → 精确提取正常；Banner/状态栏仍提示 AI 未配置（L1+L2 only）  
5. 设置页保存空配置 → 重启仍正常  
6. 填写 Key 后 → Banner 隐藏、状态栏变绿「已配置」；路径 B 可 AI 分析  

### 17.5 用户只需「导入 API」即可启用路径 B

用户在 **设置 → 填写 API Key + 模型名称（Base URL 可选）→ 保存 → 测试连接** 后，无需改代码、无需重装，路径 B 自动解锁。


