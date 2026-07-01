"""OpenAI 兼容服务商预设（设置页自动填充 Base URL 与字段说明）。"""

from __future__ import annotations

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
    model_placeholder="例如 doubao-seed-1-6-250615 或 ep-2024…",
    hint=(
        "在火山控制台「开通管理」复制 Model ID，或在线推理的接入点 ID（ep- 开头）。"
        "须选择支持视觉理解的模型；本程序会发送参考图进行分析。"
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
