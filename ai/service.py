"""将 AI 结果转为会话数据。"""

from __future__ import annotations

from typing import List

from ai.schema import StyleAnalysisResult
from ai.validator import build_parameter_results
from config.ai_config import AiConfig, load_ai_config
from core.inference_result import AiLearningReport
from lut.lut_generator import build_lut_from_params


def style_result_to_report(
    result: StyleAnalysisResult,
    elapsed_ms: float,
    cfg: AiConfig | None = None,
) -> AiLearningReport:
    cfg = cfg or load_ai_config()
    params: List = build_parameter_results(result.parameters, cfg)
    return AiLearningReport(
        overall_impression=result.overall_impression,
        editing_steps=result.editing_steps,
        priority_adjustments=result.priority_adjustments,
        parameters=params,
        analysis_ms=elapsed_ms,
        raw_json=result.raw,
    )


def build_lut_for_report(report: AiLearningReport):
    flat = {
        p.key: p.value
        for p in report.parameters
        if p.is_available and p.include_in_lut
    }
    if not flat:
        return None
    return build_lut_from_params(flat)
