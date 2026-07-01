"""Provider 能力描述（OpenAI 兼容层）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapabilities:
    """当前适配器假设的能力；将来多 provider 时可按配置切换。"""

    name: str = "openai_compatible"
    supports_vision: bool = True
    supports_json_mode: bool = True
    chat_completions_path: str = "/chat/completions"
    models_path: str = "/models"


OPENAI_COMPATIBLE = ProviderCapabilities()
