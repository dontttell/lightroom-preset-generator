"""
全局配置模块
------------
控制各推测参数模块的启用/禁用。将某个键设为 False 即可跳过该模块，
程序仍可正常运行，对应参数会在 GUI 中显示「缺失」提示。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AppSettings:
    """应用程序运行时配置。"""

    # 分析时下采样最大边长（像素）。缩小图像可显著加速，全局统计量几乎不变。
    analysis_max_size: int = 1024

    # 各参数推测模块开关 —— 设为 False 可独立禁用某一模块进行 debug
    enabled_modules: Dict[str, bool] = field(
        default_factory=lambda: {
            "exposure": True,
            "contrast": True,
            "highlights_shadows": True,
            "whites_blacks": True,
            "temperature_tint": True,
            "saturation_vibrance": True,
            "clarity": True,
            "tone_curve": True,
            "split_toning": True,
            "vignette": True,
        }
    )

    # XMP 导出默认值
    preset_group: str = "Lightroom预设生成器"
    process_version: str = "11.0"
    camera_raw_version: str = "15.4"

    # GUI
    window_title: str = "Lightroom 预设学习器"
    ui_version: str = "1.6.0"
    window_min_width: int = 1100
    window_min_height: int = 720


# 单例，供全项目引用
SETTINGS = AppSettings()
