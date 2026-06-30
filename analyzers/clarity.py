"""清晰度 (Clarity) 推测模块 —— 基于局部对比度（Laplacian 方差）。"""

from __future__ import annotations

import cv2
import numpy as np

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class ClarityAnalyzer(BaseAnalyzer):
    module_id = "clarity"
    display_name = "清晰度"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "Clarity2012"
        try:
            gray = ctx.luminance.astype(np.uint8)
            lap = cv2.Laplacian(gray, cv2.CV_64F)
            local_contrast = float(np.var(lap))

            # 典型范围 empirically: 50~800
            clarity = round(clamp(map_linear(local_contrast, 80, 600, -20, 45), -100, 100))
            confidence = clamp(0.4 + local_contrast / 1200, 0.35, 0.7)

            return self._ok(
                key=key,
                display_name="清晰度 (Clarity)",
                value=int(clarity),
                confidence=confidence,
                message="由 Laplacian 局部对比度推测",
                raw_stats={"laplacian_variance": local_contrast},
            )
        except Exception as exc:
            return self._failed(key, "清晰度 (Clarity)", str(exc))
