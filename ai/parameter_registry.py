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
    color_module: bool = False
    """色彩扩展模块（分级/HSL/颗粒暗角）；AI 输出为稀疏可选，非必填。"""


SCHEMA_VERSION = "style_analysis.v1.1"

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

# 基础 11 项：AI 须全量输出
CORE_PARAMETER_KEYS: Tuple[str, ...] = (
    "Exposure2012",
    "Contrast2012",
    "Highlights2012",
    "Shadows2012",
    "Whites2012",
    "Blacks2012",
    "Temperature",
    "Tint",
    "Saturation",
    "Vibrance",
    "Clarity2012",
)

# 色彩扩展：稀疏可选（见 prompt §7b）
COLOR_MODULE_KEYS: Tuple[str, ...] = (
    # 颜色分级 / 分离色调
    "SplitToningShadowHue",
    "SplitToningShadowSaturation",
    "SplitToningHighlightHue",
    "SplitToningHighlightSaturation",
    "SplitToningBalance",
    "ColorGradeGlobalHue",
    "ColorGradeGlobalSat",
    "ColorGradeMidtoneHue",
    "ColorGradeMidtoneSat",
    # 定向 HSL
    "SaturationAdjustmentOrange",
    "LuminanceAdjustmentOrange",
    "SaturationAdjustmentRed",
    "HueAdjustmentBlue",
    "SaturationAdjustmentBlue",
    "LuminanceAdjustmentBlue",
    "HueAdjustmentAqua",
    "SaturationAdjustmentAqua",
    "LuminanceAdjustmentAqua",
    "HueAdjustmentGreen",
    "SaturationAdjustmentGreen",
    "LuminanceAdjustmentGreen",
    # 暗角 / 颗粒
    "PostCropVignetteAmount",
    "PostCropVignetteMidpoint",
    "GrainAmount",
)

PARAMETER_SPECS: Dict[str, ParameterSpec] = {
    # —— 基础（全量输出）——
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
    # —— 颜色分级（稀疏）——
    "SplitToningShadowHue": ParameterSpec(
        "SplitToningShadowHue", int, 0, 360, 0, False, color_module=True
    ),
    "SplitToningShadowSaturation": ParameterSpec(
        "SplitToningShadowSaturation", int, 0, 100, 0, False, color_module=True
    ),
    "SplitToningHighlightHue": ParameterSpec(
        "SplitToningHighlightHue", int, 0, 360, 0, False, color_module=True
    ),
    "SplitToningHighlightSaturation": ParameterSpec(
        "SplitToningHighlightSaturation", int, 0, 100, 0, False, color_module=True
    ),
    "SplitToningBalance": ParameterSpec(
        "SplitToningBalance", int, -100, 100, 0, False, color_module=True
    ),
    "ColorGradeGlobalHue": ParameterSpec(
        "ColorGradeGlobalHue", int, 0, 360, 0, False, color_module=True
    ),
    "ColorGradeGlobalSat": ParameterSpec(
        "ColorGradeGlobalSat", int, 0, 100, 0, False, color_module=True
    ),
    "ColorGradeMidtoneHue": ParameterSpec(
        "ColorGradeMidtoneHue", int, 0, 360, 0, False, color_module=True
    ),
    "ColorGradeMidtoneSat": ParameterSpec(
        "ColorGradeMidtoneSat", int, 0, 100, 0, False, color_module=True
    ),
    # —— 定向 HSL（稀疏）——
    "SaturationAdjustmentOrange": ParameterSpec(
        "SaturationAdjustmentOrange", int, -100, 100, 0, False, color_module=True
    ),
    "LuminanceAdjustmentOrange": ParameterSpec(
        "LuminanceAdjustmentOrange", int, -100, 100, 0, False, color_module=True
    ),
    "SaturationAdjustmentRed": ParameterSpec(
        "SaturationAdjustmentRed", int, -100, 100, 0, False, color_module=True
    ),
    "HueAdjustmentBlue": ParameterSpec(
        "HueAdjustmentBlue", int, -100, 100, 0, False, color_module=True
    ),
    "SaturationAdjustmentBlue": ParameterSpec(
        "SaturationAdjustmentBlue", int, -100, 100, 0, False, color_module=True
    ),
    "LuminanceAdjustmentBlue": ParameterSpec(
        "LuminanceAdjustmentBlue", int, -100, 100, 0, False, color_module=True
    ),
    "HueAdjustmentAqua": ParameterSpec(
        "HueAdjustmentAqua", int, -100, 100, 0, False, color_module=True
    ),
    "SaturationAdjustmentAqua": ParameterSpec(
        "SaturationAdjustmentAqua", int, -100, 100, 0, False, color_module=True
    ),
    "LuminanceAdjustmentAqua": ParameterSpec(
        "LuminanceAdjustmentAqua", int, -100, 100, 0, False, color_module=True
    ),
    "HueAdjustmentGreen": ParameterSpec(
        "HueAdjustmentGreen", int, -100, 100, 0, False, color_module=True
    ),
    "SaturationAdjustmentGreen": ParameterSpec(
        "SaturationAdjustmentGreen", int, -100, 100, 0, False, color_module=True
    ),
    "LuminanceAdjustmentGreen": ParameterSpec(
        "LuminanceAdjustmentGreen", int, -100, 100, 0, False, color_module=True
    ),
    # —— 效果（稀疏）——
    "PostCropVignetteAmount": ParameterSpec(
        "PostCropVignetteAmount", int, -100, 100, 0, False, color_module=True
    ),
    "PostCropVignetteMidpoint": ParameterSpec(
        "PostCropVignetteMidpoint", int, 0, 100, 50, False, color_module=True
    ),
    "GrainAmount": ParameterSpec("GrainAmount", int, 0, 100, 0, False, color_module=True),
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


def all_parameter_keys() -> Tuple[str, ...]:
    return tuple(PARAMETER_SPECS.keys())
