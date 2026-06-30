"""
分析器注册表
------------
新增参数模块时：1) 实现 BaseAnalyzer 子类  2) 在此注册  3) 在 settings 添加开关
"""

from __future__ import annotations

from typing import Dict, List, Type

from analyzers.base import BaseAnalyzer
from analyzers.clarity import ClarityAnalyzer
from analyzers.contrast import ContrastAnalyzer
from analyzers.exposure import ExposureAnalyzer
from analyzers.highlights_shadows import HighlightsShadowsAnalyzer
from analyzers.saturation_vibrance import SaturationVibranceAnalyzer
from analyzers.split_toning import SplitToningAnalyzer
from analyzers.temperature_tint import TemperatureTintAnalyzer
from analyzers.tone_curve import ToneCurveAnalyzer
from analyzers.vignette import VignetteAnalyzer
from analyzers.whites_blacks import WhitesBlacksAnalyzer

# 复合结果展开器：将 dict 型 value 拆成多个 XMP 字段
EXPANDERS = {
    "HighlightsShadows2012": HighlightsShadowsAnalyzer.expand_to_xmp_params,
    "WhitesBlacks2012": WhitesBlacksAnalyzer.expand_to_xmp_params,
    "TemperatureTint": TemperatureTintAnalyzer.expand_to_xmp_params,
    "SaturationVibrance": SaturationVibranceAnalyzer.expand_to_xmp_params,
    "SplitToning": SplitToningAnalyzer.expand_to_xmp_params,
    "PostCropVignette": VignetteAnalyzer.expand_to_xmp_params,
}

ANALYZER_REGISTRY: List[Type[BaseAnalyzer]] = [
    ExposureAnalyzer,
    ContrastAnalyzer,
    HighlightsShadowsAnalyzer,
    WhitesBlacksAnalyzer,
    TemperatureTintAnalyzer,
    SaturationVibranceAnalyzer,
    ClarityAnalyzer,
    ToneCurveAnalyzer,
    SplitToningAnalyzer,
    VignetteAnalyzer,
]


def build_analyzers(enabled: Dict[str, bool]) -> List[BaseAnalyzer]:
    """根据配置实例化已启用的分析器。"""
    instances: List[BaseAnalyzer] = []
    for cls in ANALYZER_REGISTRY:
        if enabled.get(cls.module_id, True):
            instances.append(cls())
    return instances
