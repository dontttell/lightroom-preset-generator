"""曝光 (Exposure) 推测模块 —— 基于平均亮度与中间调分布。"""

from __future__ import annotations

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class ExposureAnalyzer(BaseAnalyzer):
    module_id = "exposure"
    display_name = "曝光"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "Exposure2012"
        try:
            mean_l = ctx.stats["mean_luminance"]
            median_l = ctx.stats["median_luminance"]
            # 参考：中性曝光约 mean_l ≈ 0.45~0.55
            target = 0.50
            blend = 0.6 * mean_l + 0.4 * median_l
            # LR Exposure 范围约 -5 ~ +5，每档约 0.08~0.12 亮度偏移（启发式）
            exposure = map_linear(blend, 0.25, 0.75, -1.5, 1.5)
            exposure = round(clamp(exposure, -3.0, 3.0), 2)

            deviation = abs(blend - target)
            confidence = clamp(1.0 - deviation * 2.5, 0.35, 0.85)

            return self._ok(
                key=key,
                display_name="曝光 (Exposure)",
                value=exposure,
                confidence=confidence,
                message="由整体亮度推测；JPG 已压缩，结果仅为近似",
                raw_stats={"mean_luminance": mean_l, "median_luminance": median_l, "blend": blend},
            )
        except Exception as exc:
            return self._failed(key, "曝光 (Exposure)", str(exc))
