"""OpenAI-compatible Chat Completions Vision API adapter."""

from __future__ import annotations

import base64
import time
from pathlib import Path

import httpx

from ai.base import AiAnalysisError, BaseAiProvider
from ai.capabilities import OPENAI_COMPATIBLE
from ai.response_parser import parse_json_content
from ai.schema import StyleAnalysisResult
from ai.validator import normalize_style_analysis
from config.ai_config import AiConfig


class OpenAiCompatibleProvider(BaseAiProvider):
    """
    任意 OpenAI 兼容 Vision API 的 HTTP 客户端。

    文件名历史原因见 openai_provider.py；实际绑定的是协议形态，非 OpenAI 独家。
    """

    capabilities = OPENAI_COMPATIBLE

    def __init__(self, cfg: AiConfig):
        self.cfg = cfg

    def analyze(self, image_path: str) -> StyleAnalysisResult:
        settings = self.cfg.analysis_settings()
        prompt = self._load_prompt()
        image_b64, mime = _encode_image(image_path)
        user_text = self.cfg.user_message_text()
        last_error: Exception | None = None
        attempts = max(1, settings.max_retries + 1)

        for attempt in range(attempts):
            extra_user = user_text
            if attempt > 0:
                extra_user += (
                    "\n\nYour previous response was invalid. "
                    "Return ONLY a JSON object matching style_analysis.v1. No markdown."
                )
            try:
                content = self._request_completion(prompt, extra_user, image_b64, mime, settings.use_json_mode)
                parsed = parse_json_content(content)
                result, _, warnings = normalize_style_analysis(parsed, self.cfg)
                if warnings and attempt == attempts - 1:
                    result.raw["_normalize_warnings"] = warnings
                return result
            except (AiAnalysisError, ValueError) as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                raise AiAnalysisError(str(exc)) from exc

        raise AiAnalysisError(str(last_error or "AI 分析失败"))

    def test_connection(self) -> str:
        base = self.cfg.resolved_base_url()
        url = f"{base}{self.capabilities.models_path}"
        headers = {"Authorization": f"Bearer {self.cfg.resolved_api_key()}"}
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AiAnalysisError(f"连接测试失败: {exc}") from exc
        return f"连接成功（{self.capabilities.name} / {self.cfg.model}）"

    def _request_completion(
        self,
        system_prompt: str,
        user_text: str,
        image_b64: str,
        mime: str,
        use_json_mode: bool,
    ) -> str:
        payload: dict = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    ],
                },
            ],
            "max_tokens": 2000,
        }
        if use_json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = f"{self.cfg.resolved_base_url()}{self.capabilities.chat_completions_path}"
        headers = {
            "Authorization": f"Bearer {self.cfg.resolved_api_key()}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise AiAnalysisError(f"API 请求失败: {exc}") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AiAnalysisError(f"API 响应格式异常: {repr(data)[:300]}") from exc

    def _load_prompt(self) -> str:
        rel = self.cfg.resolved_prompt_path()
        path = Path(rel)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / rel
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return "Analyze photo color grading. Output JSON only (style_analysis.v1)."


def _encode_image(image_path: str) -> tuple[str, str]:
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(
        suffix, "image/jpeg"
    )
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii"), mime
