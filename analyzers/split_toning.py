"""分离色调推测模块 —— 启发式检测阴影/高光区域的色相偏移。"""

from __future__ import annotations

import numpy as np

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class SplitToningAnalyzer(BaseAnalyzer):
    module_id = "split_toning"
    display_name = "分离色调"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "SplitToning"
        try:
            hsv = ctx.hsv
            l_norm = ctx.l_norm
            hue = hsv[:, :, 0]  # 0~179 OpenCV
            sat = hsv[:, :, 1]

            shadow_mask = l_norm < 0.25
            highlight_mask = l_norm > 0.75

            def masked_mean_hue(mask: np.ndarray) -> float:
                if not np.any(mask):
                    return 0.0
                weights = sat[mask]
                if np.sum(weights) < 1:
                    return float(np.mean(hue[mask]))
                return float(np.average(hue[mask], weights=weights))

            shadow_h = masked_mean_hue(shadow_mask)
            highlight_h = masked_mean_hue(highlight_mask)

            # OpenCV hue → LR hue 0~360
            shadow_hue = int(clamp(shadow_h * 2, 0, 360))
            highlight_hue = int(clamp(highlight_h * 2, 0, 360))

            shadow_sat = int(clamp(map_linear(float(np.mean(sat[shadow_mask])) if np.any(shadow_mask) else 0, 20, 80, 0, 35), 0, 100))
            highlight_sat = int(clamp(map_linear(float(np.mean(sat[highlight_mask])) if np.any(highlight_mask) else 0, 20, 80, 0, 35), 0, 100))

            # 若分离不明显则降低饱和度
            if abs(shadow_hue - highlight_hue) < 15:
                shadow_sat = max(0, shadow_sat - 10)
                highlight_sat = max(0, highlight_sat - 10)

            value = {
                "SplitToningShadowHue": shadow_hue,
                "SplitToningShadowSaturation": shadow_sat,
                "SplitToningHighlightHue": highlight_hue,
                "SplitToningHighlightSaturation": highlight_sat,
                "SplitToningBalance": 0,
            }
            confidence = 0.4  # 分离色调从 JPG 反推置信度较低

            return self._ok(
                key=key,
                display_name="分离色调 (Split Toning)",
                value=value,
                confidence=confidence,
                message="启发式推测，精确度有限",
                raw_stats={"shadow_hue": shadow_hue, "highlight_hue": highlight_hue},
            )
        except Exception as exc:
            return self._failed(key, "分离色调", str(exc))

    @staticmethod
    def expand_to_xmp_params(result: ParameterResult):
        if not result.is_available or not isinstance(result.value, dict):
            return [result]
        return [
            ParameterResult(key=k, display_name=k, value=v, status=result.status, confidence=result.confidence)
            for k, v in result.value.items()
        ]
