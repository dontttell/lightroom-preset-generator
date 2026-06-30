"""
AI 配置读写
-----------
默认全部留空；未配置时 is_ready() 为 False，程序其余功能正常运行。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent
LOCAL_CONFIG = ROOT / "config" / "ai_config.local.yaml"
EXAMPLE_CONFIG = ROOT / "config" / "ai_config.example.yaml"


@dataclass
class AiConfig:
    provider: str = ""
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    language: str = "zh-CN"
    prompt_file: str = "config/prompts/style_analysis.txt"

    def is_ready(self) -> bool:
        """API 是否已足够发起分析（UI 不设「服务商」字段，仅需 Key + 模型）。"""
        key = (self.api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
        model = self.model.strip()
        return bool(key and model)

    def effective_provider(self) -> str:
        """内部 provider；UI 不展示，保存时默认 openai_compatible。"""
        p = self.provider.strip().lower()
        if p in ("openai", "openai_compatible", "custom"):
            return p
        return "openai_compatible"

    def resolved_api_key(self) -> str:
        return (self.api_key or os.environ.get("OPENAI_API_KEY", "")).strip()

    def resolved_base_url(self) -> str:
        url = self.base_url.strip()
        if url:
            return url.rstrip("/")
        if self.provider.strip().lower() in ("openai", "openai_compatible", "") or not self.provider.strip():
            return "https://api.openai.com/v1"
        return url

    def status_message(self) -> str:
        if self.is_ready():
            url_hint = self.base_url.strip() or "默认 OpenAI 端点"
            return f"已配置 · 模型 {self.model} · {url_hint}"
        return "未配置 — 请在设置中填写 API Key 与模型"


def load_ai_config() -> AiConfig:
    path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    if not path.exists():
        return AiConfig()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    analysis = data.get("analysis") or {}
    return AiConfig(
        provider=str(data.get("provider") or ""),
        api_key=str(data.get("api_key") or ""),
        base_url=str(data.get("base_url") or ""),
        model=str(data.get("model") or ""),
        language=str(analysis.get("language") or "zh-CN"),
        prompt_file=str(analysis.get("prompt_file") or "config/prompts/style_analysis.txt"),
    )


def save_ai_config(cfg: AiConfig) -> None:
    LOCAL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    provider = cfg.provider.strip() or cfg.effective_provider()
    payload = {
        "provider": provider,
        "api_key": cfg.api_key,
        "base_url": cfg.base_url,
        "model": cfg.model,
        "analysis": {"language": cfg.language, "prompt_file": cfg.prompt_file},
    }
    with open(LOCAL_CONFIG, "w", encoding="utf-8") as f:
        yaml.dump(payload, f, allow_unicode=True, default_flow_style=False)
