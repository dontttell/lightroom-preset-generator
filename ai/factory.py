"""按配置创建 AI Provider；未配置时抛出 AiNotConfiguredError。"""

from __future__ import annotations

from config.ai_config import AiConfig, load_ai_config
from ai.base import AiNotConfiguredError, BaseAiProvider
from ai.openai_compatible_provider import OpenAiCompatibleProvider


def create_analyzer(cfg: AiConfig | None = None) -> BaseAiProvider:
    cfg = cfg or load_ai_config()
    if not cfg.is_ready():
        raise AiNotConfiguredError(
            "AI 服务未配置。请在「设置」中填写 API Key 与模型名称。"
        )
    provider = cfg.effective_provider()
    if provider in ("openai", "openai_compatible", "custom"):
        return OpenAiCompatibleProvider(cfg)
    raise AiNotConfiguredError(f"不支持的服务商: {cfg.provider}")
