"""解析模型返回的 JSON 文本。"""

from __future__ import annotations

import json
import re

from ai.base import AiAnalysisError


def parse_json_content(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AiAnalysisError(f"AI 返回非 JSON: {text[:200]}") from exc
    if not isinstance(data, dict):
        raise AiAnalysisError("AI 返回的 JSON 必须是对象")
    return data
