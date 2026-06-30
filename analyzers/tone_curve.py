"""色调曲线推测模块 —— 根据直方图形状选择预设曲线名。"""

from __future__ import annotations

from analyzers.base import BaseAnalyzer, ImageContext
from core.inference_result import ParameterResult


class ToneCurveAnalyzer(BaseAnalyzer):
    module_id = "tone_curve"
    display_name = "色调曲线"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "ToneCurveName2012"
        try:
            p = ctx.stats["percentiles_l"]
            std_l = ctx.stats["std_luminance"]
            spread = p[7] - p[1]

            if std_l > 0.22 and spread > 0.65:
                name = "Strong Contrast"
            elif std_l > 0.16 and spread > 0.50:
                name = "Medium Contrast"
            else:
                name = "Linear"

            confidence = 0.5 if name == "Linear" else 0.6

            return self._ok(
                key=key,
                display_name="色调曲线 (Tone Curve)",
                value=name,
                confidence=confidence,
                message="由直方图形态匹配预设曲线（非精确控制点）",
                raw_stats={"std_luminance": std_l, "spread": spread},
            )
        except Exception as exc:
            return self._failed(key, "色调曲线", str(exc))
