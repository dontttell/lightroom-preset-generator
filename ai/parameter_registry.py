"""
Lightroom 参数字段注册表
------------------------
AI 校验、LUT 烘焙、XMP 导出的单一来源。见 docs/AI_RESPONSE_SCHEMA.md。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Tuple, Union


@dataclass(frozen=True)
class ParameterSpec:
    key: str
    value_type: type
    min_val: Union[int, float]
    max_val: Union[int, float]
    default: Union[int, float]
    lut_eligible: bool
    """是否参与本地 LUT 烘焙（与 lut/lut_generator.py 一致）。"""


SCHEMA_VERSION = "style_analysis.v1"

# LUT 烘焙支持的字段（Temperature 与 Tint 必须成对）
LUT_SUPPORTED_KEYS: FrozenSet[str] = frozenset(
    {
        "Exposure2012",
        "Contrast2012",
        "Temperature",
        "Tint",
        "Saturation",
        "Clarity2012",
    }
)

PARAMETER_SPECS: Dict[str, ParameterSpec] = {
    "Exposure2012": ParameterSpec("Exposure2012", float, -5.0, 5.0, 0.0, True),
    "Contrast2012": ParameterSpec("Contrast2012", int, -100, 100, 0, True),
    "Highlights2012": ParameterSpec("Highlights2012", int, -100, 100, 0, False),
    "Shadows2012": ParameterSpec("Shadows2012", int, -100, 100, 0, False),
    "Whites2012": ParameterSpec("Whites2012", int, -100, 100, 0, False),
    "Blacks2012": ParameterSpec("Blacks2012", int, -100, 100, 0, False),
    "Temperature": ParameterSpec("Temperature", int, 2000, 50000, 5500, True),
    "Tint": ParameterSpec("Tint", int, -150, 150, 0, True),
    "Saturation": ParameterSpec("Saturation", int, -100, 100, 0, True),
    "Vibrance": ParameterSpec("Vibrance", int, -100, 100, 0, False),
    "Clarity2012": ParameterSpec("Clarity2012", int, -100, 100, 0, True),
}


def clamp_value(spec: ParameterSpec, value: Union[int, float]) -> Tuple[Union[int, float], bool]:
    """返回 (clamped_value, was_clamped)。"""
    lo, hi = spec.min_val, spec.max_val
    if value < lo:
        return (spec.value_type(lo), True)
    if value > hi:
        return (spec.value_type(hi), True)
    if spec.value_type is int:
        return (int(round(float(value))), False)
    return (round(float(value), 2), False)


def coerce_parameter_value(key: str, raw_value: object) -> Optional[Union[int, float]]:
    spec = PARAMETER_SPECS.get(key)
    if spec is None or raw_value is None:
        return None
    try:
        if spec.value_type is int:
            return int(round(float(raw_value)))
        return float(raw_value)
    except (TypeError, ValueError):
        return None
