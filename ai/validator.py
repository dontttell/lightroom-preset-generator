"""
AI 响应校验与归一化
-------------------
将模型原始 JSON 转为 StyleAnalysisResult，并生成带置信度/导出标记的 ParameterResult 列表。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ai.parameter_registry import (
    LUT_SUPPORTED_KEYS,
    PARAMETER_SPECS,
    SCHEMA_VERSION,
    clamp_value,
    coerce_parameter_value,
)
from ai.schema import StyleAnalysisResult
from config.ai_config import AiConfig
from core.inference_result import ParameterResult, ParameterStatus
from core.metadata_parser import DISPLAY_NAMES


def normalize_style_analysis(raw: dict, cfg: AiConfig) -> Tuple[StyleAnalysisResult, List[ParameterResult], List[str]]:
    """
    校验并归一化 AI JSON。

    Returns:
        (StyleAnalysisResult, ParameterResult 列表, 警告/调试信息)
    """
    warnings: List[str] = []
    settings = cfg.analysis_settings()

    if not isinstance(raw, dict):
        raise ValueError("AI 响应必须是 JSON 对象")

    overall = str(raw.get("overall_impression") or "").strip()
    if not overall:
        warnings.append("缺少 overall_impression，已留空")

    editing_steps = _normalize_editing_steps(raw.get("editing_steps"), warnings)
    priority = _normalize_priority(raw.get("priority_adjustments"), warnings)
    parameters_raw = raw.get("parameters")
    if not isinstance(parameters_raw, dict):
        warnings.append("parameters 缺失或非对象，已视为空")
        parameters_raw = {}

    normalized_params: Dict[str, Dict[str, Any]] = {}
    parameter_results: List[ParameterResult] = []

    for key, item in parameters_raw.items():
        if key not in PARAMETER_SPECS:
            warnings.append(f"忽略未知参数: {key}")
            continue
        if not isinstance(item, dict):
            warnings.append(f"参数 {key} 格式无效，已跳过")
            continue

        spec = PARAMETER_SPECS[key]
        coerced = coerce_parameter_value(key, item.get("value"))
        if coerced is None:
            warnings.append(f"参数 {key} 的值无法解析，已跳过")
            continue

        value, clamped = clamp_value(spec, coerced)
        if clamped:
            warnings.append(f"参数 {key} 已 clamp 到合法范围 [{spec.min_val}, {spec.max_val}]")

        try:
            confidence = float(item.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
            warnings.append(f"参数 {key} 的 confidence 无效，已用 0.5")
        confidence = max(0.0, min(1.0, confidence))

        include_in_lut = _lut_inclusion(key, value, confidence, settings.lut_min_confidence, parameters_raw, warnings)
        include_in_xmp = confidence >= settings.xmp_min_confidence

        message = _parameter_message(confidence, include_in_lut, include_in_xmp, clamped, settings)

        normalized_params[key] = {
            "value": value,
            "confidence": confidence,
            "include_in_lut": include_in_lut,
            "include_in_xmp": include_in_xmp,
            "clamped": clamped,
        }
        parameter_results.append(
            ParameterResult(
                key=key,
                display_name=DISPLAY_NAMES.get(key, key),
                value=value,
                status=ParameterStatus.INFERRED,
                confidence=confidence,
                message=message,
                include_in_lut=include_in_lut,
                include_in_xmp=include_in_xmp,
                raw_stats={"clamped": clamped, "schema_version": SCHEMA_VERSION},
            )
        )

    # 稳定顺序：与注册表一致
    parameter_results.sort(key=lambda p: list(PARAMETER_SPECS.keys()).index(p.key))

    result = StyleAnalysisResult(
        overall_impression=overall,
        editing_steps=editing_steps,
        priority_adjustments=priority,
        parameters=normalized_params,
        raw={**raw, "_schema_version": SCHEMA_VERSION, "_warnings": warnings},
    )
    return result, parameter_results, warnings


def _normalize_editing_steps(raw: Any, warnings: List[str]) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        if raw is not None:
            warnings.append("editing_steps 非数组，已忽略")
        return []
    steps: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            warnings.append(f"editing_steps[{idx}] 非对象，已跳过")
            continue
        steps.append(
            {
                "step": int(item.get("step") or idx),
                "title": str(item.get("title") or ""),
                "description": str(item.get("description") or ""),
            }
        )
    return steps


def _normalize_priority(raw: Any, warnings: List[str]) -> List[str]:
    if not isinstance(raw, list):
        if raw is not None:
            warnings.append("priority_adjustments 非数组，已忽略")
        return []
    out: List[str] = []
    for item in raw:
        key = str(item)
        if key in PARAMETER_SPECS:
            out.append(key)
        else:
            warnings.append(f"priority_adjustments 含未知字段 {key}，已忽略")
    return out


def _lut_inclusion(
    key: str,
    value: Any,
    confidence: float,
    lut_min: float,
    parameters_raw: dict,
    warnings: List[str],
) -> bool:
    spec = PARAMETER_SPECS[key]
    if not spec.lut_eligible:
        return False
    if confidence < lut_min:
        return False
    if key in ("Temperature", "Tint"):
        other = "Tint" if key == "Temperature" else "Temperature"
        other_item = parameters_raw.get(other)
        if not isinstance(other_item, dict) or coerce_parameter_value(other, other_item.get("value")) is None:
            warnings.append(f"参数 {key} 缺少成对的 {other}，不参与 LUT")
            return False
        try:
            other_conf = float(other_item.get("confidence", 0.5))
        except (TypeError, ValueError):
            other_conf = 0.5
        if other_conf < lut_min:
            return False
    # 接近默认值且低对比时可视为无 LUT 贡献（可选，保持简单：仍 include 若过阈值）
    return key in LUT_SUPPORTED_KEYS


def _parameter_message(
    confidence: float,
    include_in_lut: bool,
    include_in_xmp: bool,
    clamped: bool,
    settings: Any,
) -> str:
    parts = ["AI 参考 · 推测"]
    if confidence < settings.lut_min_confidence:
        parts.append("低置信")
    if not include_in_lut:
        parts.append("未参与 LUT")
    if not include_in_xmp:
        parts.append("未写入 XMP")
    if clamped:
        parts.append("已校正范围")
    return " · ".join(parts)


def build_parameter_results(normalized_params: Dict[str, Dict[str, Any]], cfg: AiConfig) -> List[ParameterResult]:
    """从已归一化的 parameters 字典构建 ParameterResult（供 service 层使用）。"""
    settings = cfg.analysis_settings()
    results: List[ParameterResult] = []
    for key, item in normalized_params.items():
        if key not in PARAMETER_SPECS:
            continue
        value = item.get("value")
        confidence = float(item.get("confidence", 0.5))
        include_in_lut = bool(item.get("include_in_lut", False))
        include_in_xmp = bool(item.get("include_in_xmp", False))
        clamped = bool(item.get("clamped", False))
        results.append(
            ParameterResult(
                key=key,
                display_name=DISPLAY_NAMES.get(key, key),
                value=value,
                status=ParameterStatus.INFERRED,
                confidence=confidence,
                message=_parameter_message(confidence, include_in_lut, include_in_xmp, clamped, settings),
                include_in_lut=include_in_lut,
                include_in_xmp=include_in_xmp,
                raw_stats={"clamped": clamped, "schema_version": SCHEMA_VERSION},
            )
        )
    results.sort(key=lambda p: list(PARAMETER_SPECS.keys()).index(p.key))
    return results
