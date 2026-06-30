"""色温/色调 (Temperature/Tint) 推测模块 —— 基于 LAB a/b 通道均值。"""

from __future__ import annotations

from analyzers.base import BaseAnalyzer, ImageContext, clamp, map_linear
from core.inference_result import ParameterResult


class TemperatureTintAnalyzer(BaseAnalyzer):
    module_id = "temperature_tint"
    display_name = "色温/色调"

    # D65 中性参考 (OpenCV LAB 8-bit 空间)
    NEUTRAL_A = 128.0
    NEUTRAL_B = 128.0

    def analyze(self, ctx: ImageContext) -> ParameterResult:
        key = "TemperatureTint"
        try:
            mean_a, mean_b = ctx.stats["mean_lab_ab"]
            delta_b = mean_b - self.NEUTRAL_B  # 正 → 偏黄
            delta_a = mean_a - self.NEUTRAL_A  # 正 → 偏绿 (OpenCV LAB)

            # 色温：b 轴偏移映射到 Kelvin，中性约 5500K
            temp_offset = map_linear(delta_b, -15, 15, 800, -800)
            temperature = round(clamp(5500 + temp_offset, 2000, 12000))

            # 色调：a 轴偏移，绿-洋红
            tint = round(clamp(map_linear(delta_a, -12, 12, 30, -30), -150, 150))

            value = {"Temperature": int(temperature), "Tint": int(tint)}
            color_dev = (abs(delta_a) + abs(delta_b)) / 30.0
            confidence = clamp(0.4 + color_dev * 0.3, 0.35, 0.7)

            return self._ok(
                key=key,
                display_name="色温/色调 (Temp/Tint)",
                value=value,
                confidence=confidence,
                message="由 LAB 色彩偏移推测；无法区分白平衡与后期调色",
                raw_stats={"mean_a": mean_a, "mean_b": mean_b, "delta_a": delta_a, "delta_b": delta_b},
            )
        except Exception as exc:
            return self._failed(key, "色温/色调", str(exc))

    @staticmethod
    def expand_to_xmp_params(result: ParameterResult):
        if not result.is_available or not isinstance(result.value, dict):
            return [result]
        return [
            ParameterResult(key=k, display_name=k, value=v, status=result.status, confidence=result.confidence)
            for k, v in result.value.items()
        ]
