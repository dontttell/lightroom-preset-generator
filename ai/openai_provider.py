"""OpenAI / OpenAI-compatible Vision API。"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import httpx

from ai.base import AiAnalysisError, BaseAiProvider
from ai.schema import StyleAnalysisResult
from config.ai_config import AiConfig


class OpenAiCompatibleProvider(BaseAiProvider):
    def __init__(self, cfg: AiConfig):
        self.cfg = cfg

    def analyze(self, image_path: str) -> StyleAnalysisResult:
        prompt = self._load_prompt()
        image_b64, mime = _encode_image(image_path)
        payload = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请分析这张图片的调色风格，仅输出 JSON。"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                    ],
                },
            ],
            "max_tokens": 2000,
        }
        url = f"{self.cfg.resolved_base_url()}/chat/completions"
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

        content = data["choices"][0]["message"]["content"]
        parsed = _parse_json_content(content)
        return _to_style_result(parsed)

    def test_connection(self) -> str:
        url = f"{self.cfg.resolved_base_url()}/models"
        headers = {"Authorization": f"Bearer {self.cfg.resolved_api_key()}"}
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
        return f"连接成功（{self.cfg.provider} / {self.cfg.model}）"

    def _load_prompt(self) -> str:
        path = Path(self.cfg.prompt_file)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / path
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return "Analyze photo color grading and return JSON only."


def _encode_image(image_path: str) -> tuple[str, str]:
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(
        suffix, "image/jpeg"
    )
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii"), mime


def _parse_json_content(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AiAnalysisError(f"AI 返回非 JSON: {text[:200]}") from exc


def _to_style_result(data: dict) -> StyleAnalysisResult:
    return StyleAnalysisResult(
        overall_impression=str(data.get("overall_impression") or ""),
        editing_steps=list(data.get("editing_steps") or []),
        priority_adjustments=list(data.get("priority_adjustments") or []),
        parameters=dict(data.get("parameters") or {}),
        raw=data,
    )
