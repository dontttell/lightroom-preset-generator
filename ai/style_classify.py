"""Call① style_classify.v1 解析与校验。"""

from __future__ import annotations

from typing import Any, Mapping

from ai.base import AiAnalysisError
from ai.style_recipes import ClassifyResult

_VALID_CATEGORIES = frozenset({"P", "L", "M"})


def parse_classify_response(raw: Mapping[str, Any]) -> ClassifyResult:
    if not isinstance(raw, Mapping):
        raise AiAnalysisError("分类响应必须是 JSON 对象")

    category = str(raw.get("category", "")).strip().upper()
    if category not in _VALID_CATEGORIES:
        raise AiAnalysisError(f"分类 category 无效: {category!r}（须为 P/L/M）")

    subtype = str(raw.get("subtype", "")).strip()
    if not subtype:
        raise AiAnalysisError("分类响应缺少 subtype")

    scene_keywords = raw.get("scene_keywords")
    if not isinstance(scene_keywords, list) or not scene_keywords:
        raise AiAnalysisError("分类响应须包含非空 scene_keywords")

    try:
        subtype_confidence = float(raw.get("subtype_confidence", 0.0))
    except (TypeError, ValueError) as exc:
        raise AiAnalysisError("subtype_confidence 无效") from exc
    subtype_confidence = max(0.0, min(1.0, subtype_confidence))

    data = dict(raw)
    data["category"] = category
    data["subtype_confidence"] = subtype_confidence
    return ClassifyResult.from_dict(data)
