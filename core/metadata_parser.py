"""
Metadata 解析 → 学习面板参数
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.inference_result import ParameterResult, ParameterStatus

# GUI 分组
PANEL_GROUPS: List[Tuple[str, List[str]]] = [
    (
        "基础",
        [
            "Exposure2012",
            "Contrast2012",
            "Highlights2012",
            "Shadows2012",
            "Whites2012",
            "Blacks2012",
        ],
    ),
    ("颜色", ["Temperature", "Tint", "Vibrance", "Saturation"]),
    (
        "分离色调",
        [
            "SplitToningShadowHue",
            "SplitToningShadowSaturation",
            "SplitToningHighlightHue",
            "SplitToningHighlightSaturation",
            "SplitToningBalance",
            "ColorGradeGlobalHue",
            "ColorGradeGlobalSat",
            "ColorGradeMidtoneHue",
            "ColorGradeMidtoneSat",
        ],
    ),
    (
        "混色器",
        [
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
        ],
    ),
    ("细节", ["Sharpness", "Clarity2012", "LuminanceSmoothing"]),
    (
        "效果",
        [
            "PostCropVignetteAmount",
            "PostCropVignetteMidpoint",
            "GrainAmount",
            "GrainSize",
            "GrainFrequency",
        ],
    ),
]

DISPLAY_NAMES = {
    "Exposure2012": "曝光",
    "Contrast2012": "对比度",
    "Highlights2012": "高光",
    "Shadows2012": "阴影",
    "Whites2012": "白色",
    "Blacks2012": "黑色",
    "Temperature": "色温",
    "Tint": "色调",
    "Vibrance": "自然饱和度",
    "Saturation": "饱和度",
    "Clarity2012": "清晰度",
    "Sharpness": "锐化",
    "SplitToningShadowHue": "阴影色相",
    "SplitToningShadowSaturation": "阴影饱和度",
    "SplitToningHighlightHue": "高光色相",
    "SplitToningHighlightSaturation": "高光饱和度",
    "SplitToningBalance": "分离色调平衡",
    "ColorGradeGlobalHue": "全局分级色相",
    "ColorGradeGlobalSat": "全局分级饱和度",
    "ColorGradeMidtoneHue": "中间调色相",
    "ColorGradeMidtoneSat": "中间调饱和度",
    "SaturationAdjustmentOrange": "橙色饱和度",
    "LuminanceAdjustmentOrange": "橙色明亮度",
    "SaturationAdjustmentRed": "红色饱和度",
    "HueAdjustmentBlue": "蓝色色相",
    "SaturationAdjustmentBlue": "蓝色饱和度",
    "LuminanceAdjustmentBlue": "蓝色明亮度",
    "HueAdjustmentAqua": "青色色相",
    "SaturationAdjustmentAqua": "青色饱和度",
    "LuminanceAdjustmentAqua": "青色明亮度",
    "HueAdjustmentGreen": "绿色色相",
    "SaturationAdjustmentGreen": "绿色饱和度",
    "LuminanceAdjustmentGreen": "绿色明亮度",
    "PostCropVignetteAmount": "暗角量",
    "PostCropVignetteMidpoint": "暗角中点",
    "GrainAmount": "颗粒量",
}


def crs_fields_to_parameters(crs_fields: Dict[str, Any]) -> List[ParameterResult]:
    """将 crs 字典转为 ParameterResult 列表。"""
    skip = {"HasSettings", "Version", "ProcessVersion", "PresetType", "UUID", "Name", "Group"}
    params: List[ParameterResult] = []
    for key, value in crs_fields.items():
        if key in skip or value is None or value == "":
            continue
        params.append(
            ParameterResult(
                key=key,
                display_name=DISPLAY_NAMES.get(key, key),
                value=value,
                status=ParameterStatus.OK,
                confidence=1.0,
                message="精确提取",
            )
        )
    return params


def group_parameters(params: List[ParameterResult]) -> List[Tuple[str, List[ParameterResult]]]:
    """按 LR 面板分组，未映射的放入「其他」。"""
    by_key = {p.key: p for p in params}
    used = set()
    groups: List[Tuple[str, List[ParameterResult]]] = []
    for group_name, keys in PANEL_GROUPS:
        items = [by_key[k] for k in keys if k in by_key]
        if items:
            groups.append((group_name, items))
            used.update(k for k in keys if k in by_key)
    others = [p for p in params if p.key not in used]
    if others:
        groups.append(("其他", others))
    return groups
