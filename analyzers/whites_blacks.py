"""白色/黑色色阶 (Whites/Blacks) 推测模块。"""

from __future__ import annotations

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class WhitesBlacksAnalyzer(BaseAnalyzer):
    module_id = "whites_blacks"
    display_name = "白色/黑色"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "WhitesBlacks2012"
        try:
            p = ctx.stats["percentiles_l"]
            p99, p1 = p[8], p[0]

            whites = map_linear(p99, 0.92, 1.0, -15, 35)
            whites = round(clamp(whites, -100, 100))

            blacks = map_linear(p1, 0.0, 0.08, 35, -15)
            blacks = round(clamp(blacks, -100, 100))

            value = {"Whites2012": int(whites), "Blacks2012": int(blacks)}
            confidence = 0.55

            return self._ok(
                key=key,
                display_name="白色/黑色 (Whites/Blacks)",
                value=value,
                confidence=confidence,
                message="由最亮/最暗分位数推测",
                raw_stats={"p1": p1, "p99": p99},
            )
        except Exception as exc:
            return self._failed(key, "白色/黑色", str(exc))

    @staticmethod
    def expand_to_xmp_params(result: ParameterResult):
        if not result.is_available or not isinstance(result.value, dict):
            return [result]
        return [
            ParameterResult(key=k, display_name=k, value=v, status=result.status, confidence=result.confidence)
            for k, v in result.value.items()
        ]
