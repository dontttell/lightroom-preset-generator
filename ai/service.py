"""将 AI 结果转为会话数据。"""

from __future__ import annotations

import time
from typing import List

from ai.schema import StyleAnalysisResult
from core.inference_result import AiLearningReport, ParameterResult, ParameterStatus
from core.metadata_parser import DISPLAY_NAMES, group_parameters
from lut.lut_generator import build_lut_from_params


def style_result_to_report(result: StyleAnalysisResult, elapsed_ms: float) -> AiLearningReport:
    params: List[ParameterResult] = []
    flat_params = {}
    for key, item in result.parameters.items():
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        conf = float(item.get("confidence", 0.5))
        params.append(
            ParameterResult(
                key=key,
                display_name=DISPLAY_NAMES.get(key, key),
                value=value,
                status=ParameterStatus.INFERRED,
                confidence=conf,
                message="AI 参考 · 推测",
            )
        )
        flat_params[key] = value

    return AiLearningReport(
        overall_impression=result.overall_impression,
        editing_steps=result.editing_steps,
        priority_adjustments=result.priority_adjustments,
        parameters=params,
        analysis_ms=elapsed_ms,
        raw_json=result.raw,
    )


def build_lut_for_report(report: AiLearningReport):
    flat = {p.key: p.value for p in report.parameters if p.is_available}
    if not flat:
        return None
    return build_lut_from_params(flat)
