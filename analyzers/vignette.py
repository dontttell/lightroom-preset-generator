"""暗角 (Vignette) 推测模块 —— 比较中心与边缘亮度。"""

from __future__ import annotations

import numpy as np

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class VignetteAnalyzer(BaseAnalyzer):
    module_id = "vignette"
    display_name = "暗角"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "PostCropVignette"
        try:
            l = ctx.l_norm
            h, w = l.shape
            cy, cx = h // 2, w // 2
            radius = min(h, w) * 0.45

            yy, xx = np.ogrid[:h, :w]
            dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
            center_mask = dist < radius * 0.35
            edge_mask = dist > radius * 0.85

            if not np.any(center_mask) or not np.any(edge_mask):
                return self._skipped(key, "暗角 (Vignette)", "图像尺寸过小，无法分析边缘")

            center_mean = float(np.mean(l[center_mask]))
            edge_mean = float(np.mean(l[edge_mask]))
            vignette_delta = edge_mean - center_mean  # 负值 → 边缘更暗 → 已有暗角

            amount = round(clamp(map_linear(vignette_delta, -0.12, 0.05, 25, -25), -100, 100))
            midpoint = 50
            confidence = clamp(abs(vignette_delta) * 4, 0.3, 0.65)

            value = {
                "PostCropVignetteAmount": int(amount),
                "PostCropVignetteMidpoint": int(midpoint),
                "PostCropVignetteFeather": 50,
                "PostCropVignetteRoundness": 0,
            }

            return self._ok(
                key=key,
                display_name="暗角 (Vignette)",
                value=value,
                confidence=confidence,
                message="由中心/边缘亮度差推测",
                raw_stats={"center_mean": center_mean, "edge_mean": edge_mean, "delta": vignette_delta},
            )
        except Exception as exc:
            return self._failed(key, "暗角", str(exc))

    @staticmethod
    def expand_to_xmp_params(result: ParameterResult):
        if not result.is_available or not isinstance(result.value, dict):
            return [result]
        return [
            ParameterResult(key=k, display_name=k, value=v, status=result.status, confidence=result.confidence)
            for k, v in result.value.items()
        ]
