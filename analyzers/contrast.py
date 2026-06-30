"""对比度 (Contrast) 推测模块 —— 基于亮度标准差与分位差。"""

from __future__ import annotations

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class ContrastAnalyzer(BaseAnalyzer):
    module_id = "contrast"
    display_name = "对比度"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "Contrast2012"
        try:
            std_l = ctx.stats["std_luminance"]
            p = ctx.stats["percentiles_l"]
            spread = p[7] - p[1]  # P95 - P5

            # 低对比 flat image: std~0.12, 高对比: std~0.28+
            contrast_std = map_linear(std_l, 0.10, 0.30, -30, 45)
            contrast_spread = map_linear(spread, 0.35, 0.85, -20, 40)
            contrast = round(clamp(0.55 * contrast_std + 0.45 * contrast_spread, -50, 80))

            confidence = clamp(0.5 + std_l, 0.4, 0.8)

            return self._ok(
                key=key,
                display_name="对比度 (Contrast)",
                value=int(contrast),
                confidence=confidence,
                message="由亮度离散程度推测",
                raw_stats={"std_luminance": std_l, "p95_p5_spread": spread},
            )
        except Exception as exc:
            return self._failed(key, "对比度 (Contrast)", str(exc))
