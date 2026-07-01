"""OpenAI 兼容服务商预设（设置页自动填充 Base URL 与字段说明）。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ProviderPreset:
    id: str
    label: str
    default_base_url: str
    model_field_label: str
    model_placeholder: str
    hint: str


PRESET_OPENAI = ProviderPreset(
    id="openai",
    label="OpenAI 官方",
    default_base_url="https://api.openai.com/v1",
    model_field_label="模型名称",
    model_placeholder="例如 gpt-4o、gpt-4o-mini",
    hint="API Key 与模型名称必填；Base URL 已预填 OpenAI 默认地址。",
)

PRESET_VOLCENGINE = ProviderPreset(
    id="volcengine",
    label="火山方舟（豆包）",
    default_base_url="https://ark.cn-beijing.volces.com/api/v3",
    model_field_label="模型 ID / 接入点",
    model_placeholder="例如 doubao-seed-evolving、doubao-1-5-vision-pro-32k-250115、ep-…",
    hint=(
        "本程序使用 OpenAI 兼容接口（/api/v3/chat/completions）。"
        "勿填 Claude Code 文档里的 ANTHROPIC_BASE_URL（/api/compatible 或 /api/coding），"
        "那是 Anthropic 协议，与本程序不兼容。"
        "Model 可填 doubao-seed-evolving 或开通管理里的完整 Model ID / ep- 接入点；须支持视觉。"
    ),
)

PRESET_CUSTOM = ProviderPreset(
    id="custom",
    label="自定义（OpenAI 兼容）",
    default_base_url="",
    model_field_label="模型名称 / ID",
    model_placeholder="填写服务商文档中的 model 参数",
    hint="请自行填写兼容 OpenAI Chat Completions 的 Base URL 与 model。",
)

PRESETS: Dict[str, ProviderPreset] = {
    PRESET_OPENAI.id: PRESET_OPENAI,
    PRESET_VOLCENGINE.id: PRESET_VOLCENGINE,
    PRESET_CUSTOM.id: PRESET_CUSTOM,
}

DEFAULT_PRESET_ID = PRESET_OPENAI.id


def list_presets() -> List[ProviderPreset]:
    return [PRESET_OPENAI, PRESET_VOLCENGINE, PRESET_CUSTOM]


def get_preset(preset_id: str) -> Optional[ProviderPreset]:
    return PRESETS.get((preset_id or "").strip().lower())


def infer_preset_id(*, base_url: str = "", provider: str = "", provider_preset: str = "") -> str:
    """从已保存配置推断预设（兼容旧版无 provider_preset 的配置）。"""
    explicit = (provider_preset or "").strip().lower()
    if explicit in PRESETS:
        return explicit

    url = (base_url or "").strip().lower()
    if "volces.com" in url or "volcengine" in url:
        return PRESET_VOLCENGINE.id

    prov = (provider or "").strip().lower()
    if prov == "volcengine":
        return PRESET_VOLCENGINE.id

    if url and "openai.com" not in url:
        return PRESET_CUSTOM.id

    return DEFAULT_PRESET_ID


def volcengine_model_format_warning(model: str) -> Optional[str]:
    """
    若 model 像控制台展示名而非 API Model ID，返回警告文案。
    火山方舟用展示名（如 Doubao-1.5-vision-pro）调用常会 404。
    """
    m = model.strip()
    if not m:
        return None
    if m in ("doubao-seed-evolving", "ark-code-latest"):
        return None
    if m.startswith("ep-"):
        return None
    if "." in m:
        return (
            f"「{m}」含小数点，像是控制台展示名。"
            "请改为完整 Model ID（如 doubao-1-5-vision-pro-32k-250115），"
            "或在「在线推理」创建接入点后使用 ep- 开头的 ID。"
        )
    if m[0].isupper():
        return (
            f"「{m}」以大写开头，可能不是 API Model ID。"
            "请在火山控制台复制小写的完整 Model ID 或 ep- 接入点 ID。"
        )
    # 已像 doubao-xxx-250115 这类带日期后缀的 ID
    if re.search(r"-\d{6}$", m):
        return None
    if re.match(r"^(doubao|deepseek|kimi|glm)-", m, re.I) and len(m) < 20:
        return (
            "模型 ID 可能不完整。"
            "火山 Model ID 通常含上下文与版本后缀，例如 doubao-1-5-vision-pro-32k-250115。"
        )
    return None


def openai_compatible_base_url_warning(base_url: str) -> Optional[str]:
    """
    检测火山 Anthropic/Coding Plan 网关地址；本程序仅支持 OpenAI Chat Completions。
    """
    u = (base_url or "").strip().lower().rstrip("/")
    if not u:
        return None
    if "/api/compatible" in u:
        return (
            "当前 Base URL 为火山 Anthropic 兼容网关（Claude Code / ANTHROPIC_BASE_URL），"
            "本程序无法使用。"
            "请改选「火山方舟（豆包）」预设，或填写 OpenAI 地址："
            "https://ark.cn-beijing.volces.com/api/v3"
        )
    if u.endswith("/api/coding"):
        return (
            "当前 Base URL 为 Coding Plan 的 Anthropic 网关（/api/coding），本程序无法使用。"
            "请改用 OpenAI 地址：https://ark.cn-beijing.volces.com/api/v3"
            "（Coding Plan 的 OpenAI 网关为 …/api/coding/v3，须确认支持视觉分析）。"
        )
    return None


def resolve_openai_chat_url(base_url: str, chat_path: str = "/chat/completions") -> str:
    """拼接 Chat Completions URL；若 base 已含 chat/completions 则不再重复。"""
    root = (base_url or "").strip().rstrip("/")
    suffix = chat_path if chat_path.startswith("/") else f"/{chat_path}"
    if root.lower().endswith("/chat/completions"):
        return root
    return f"{root}{suffix}"
