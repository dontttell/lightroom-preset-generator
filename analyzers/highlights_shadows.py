"""高光/阴影 (Highlights/Shadows) 推测模块 —— 基于亮度分位数与极端像素占比。"""

from __future__ import annotations

from typing import List

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class HighlightsShadowsAnalyzer(BaseAnalyzer):
    module_id = "highlights_shadows"
    display_name = "高光/阴影"

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        # 本模块一次返回多个 LR 参数，用复合 key 存储 dict
        key = "HighlightsShadows2012"
        try:
            p = ctx.stats["percentiles_l"]
            hi_ratio = ctx.stats["highlight_ratio"]
            sh_ratio = ctx.stats["shadow_ratio"]

            # 高光过多 → 负向压高光；阴影过多 → 正向提阴影
            highlights = map_linear(p[8], 0.88, 0.98, -40, 20)  # P99
            highlights -= map_linear(hi_ratio, 0.02, 0.15, 0, 25)
            highlights = round(clamp(highlights, -100, 100))

            shadows = map_linear(p[0], 0.02, 0.12, 40, -10)  # P1 低 → 提阴影
            shadows += map_linear(sh_ratio, 0.05, 0.25, 30, 0)
            shadows = round(clamp(shadows, -100, 100))

            value = {"Highlights2012": int(highlights), "Shadows2012": int(shadows)}
            confidence = clamp(0.45 + (hi_ratio + sh_ratio) * 1.5, 0.35, 0.75)

            return self._ok(
                key=key,
                display_name="高光/阴影 (Highlights/Shadows)",
                value=value,
                confidence=confidence,
                message="由亮度分位数与极端区域占比推测",
                raw_stats={"p1": p[0], "p99": p[8], "highlight_ratio": hi_ratio, "shadow_ratio": sh_ratio},
            )
        except Exception as exc:
            return self._failed(key, "高光/阴影", str(exc))

    @staticmethod
    def expand_to_xmp_params(result: ParameterResult) -> List[ParameterResult]:
        """将复合结果展开为独立 XMP 字段（供 generator 使用）。"""
        if not result.is_available or not isinstance(result.value, dict):
            return [result]
        items = []
        for k, v in result.value.items():
            items.append(
                ParameterResult(
                    key=k,
                    display_name=k,
                    value=v,
                    status=result.status,
                    confidence=result.confidence,
                    message=result.message,
                )
            )
        return items
