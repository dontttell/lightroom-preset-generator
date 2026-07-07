"""Call② style_refine 响应解析（delta 模式）。"""

from __future__ import annotations

from typing import Any, Dict, Mapping

from ai.base import AiAnalysisError
from ai.parameter_registry import COLOR_MODULE_KEYS, CORE_PARAMETER_KEYS, PARAMETER_SPECS


def parse_refine_response(raw: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise AiAnalysisError("微调响应必须是 JSON 对象")

    if raw.get("parameters") and not raw.get("parameter_adjustments"):
        raise AiAnalysisError("微调响应禁止输出完整 parameters；请使用 parameter_adjustments (delta)")

    adjustments = raw.get("parameter_adjustments")
    if adjustments is not None and not isinstance(adjustments, dict):
        raise AiAnalysisError("parameter_adjustments 须为对象")

    if isinstance(adjustments, dict):
        for key, item in adjustments.items():
            if key not in CORE_PARAMETER_KEYS:
                raise AiAnalysisError(f"parameter_adjustments 含未知核心项: {key}")
            if not isinstance(item, dict):
                raise AiAnalysisError(f"parameter_adjustments[{key}] 须为对象")
            if "delta" not in item:
                raise AiAnalysisError(f"parameter_adjustments[{key}] 缺少 delta")

    optional_7b = raw.get("optional_7b")
    if optional_7b is not None:
        if not isinstance(optional_7b, dict):
            raise AiAnalysisError("optional_7b 须为对象")
        for key, item in optional_7b.items():
            if key not in COLOR_MODULE_KEYS:
                raise AiAnalysisError(f"optional_7b 含未知项: {key}")
            if isinstance(item, dict):
                if "value" not in item:
                    raise AiAnalysisError(f"optional_7b[{key}] 缺少 value")
            elif not isinstance(item, (int, float)):
                raise AiAnalysisError(f"optional_7b[{key}] 格式无效")

    steps = raw.get("editing_steps")
    if steps is not None and not isinstance(steps, list):
        raise AiAnalysisError("editing_steps 须为数组")

    priority = raw.get("priority_adjustments")
    if priority is not None:
        if not isinstance(priority, list):
            raise AiAnalysisError("priority_adjustments 须为数组")
        for key in priority:
            if key not in PARAMETER_SPECS:
                raise AiAnalysisError(f"priority_adjustments 含未知项: {key}")

    return dict(raw)
