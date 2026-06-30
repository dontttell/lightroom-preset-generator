"""饱和度/自然饱和度推测模块。"""

from __future__ import annotations

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class SaturationVibranceAnalyzer(BaseAnalyzer):
    module_id = "saturation_vibrance"
    display_name = "饱和度"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "SaturationVibrance"
        try:
            mean_s = ctx.stats["mean_saturation"]
            std_s = ctx.stats["std_saturation"]

            saturation = round(clamp(map_linear(mean_s, 0.15, 0.55, -40, 40), -100, 100))
            # 自然饱和度：低饱和区域提升倾向，用 std 作为启发
            vibrance = round(clamp(map_linear(std_s, 0.08, 0.25, 10, -5), -100, 100))

            value = {"Saturation": int(saturation), "Vibrance": int(vibrance)}
            confidence = clamp(0.45 + mean_s * 0.5, 0.4, 0.75)

            return self._ok(
                key=key,
                display_name="饱和度/自然饱和度",
                value=value,
                confidence=confidence,
                message="由 HSV 饱和度统计推测",
                raw_stats={"mean_saturation": mean_s, "std_saturation": std_s},
            )
        except Exception as exc:
            return self._failed(key, "饱和度", str(exc))

    @staticmethod
    def expand_to_xmp_params(result: ParameterResult):
        if not result.is_available or not isinstance(result.value, dict):
            return [result]
        return [
            ParameterResult(key=k, display_name=k, value=v, status=result.status, confidence=result.confidence)
            for k, v in result.value.items()
        ]
