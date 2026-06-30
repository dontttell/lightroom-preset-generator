"""
分析器基类
----------
所有参数推测模块继承 BaseAnalyzer，实现 analyze() 方法。
彼此独立，单个模块异常不影响其他模块。
"""

from __future__ import annotations

import abc
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from core.inference_result import ParameterResult, ParameterStatus


class ImageContext:
    """
    共享图像上下文 —— 在 pipeline 中预计算一次，供各模块只读使用。

    采用下采样 + 直方图/分位数统计，比全分辨率逐像素遍历更快，
    对全局影调/色彩推测足够准确。
    """

    def __init__(self, bgr: np.ndarray, max_size: int = 1024):
        self.original_shape = bgr.shape[:2]
        self.bgr = self._downsample(bgr, max_size)
        self.rgb = cv2.cvtColor(self.bgr, cv2.COLOR_BGR2RGB)
        self.lab = cv2.cvtColor(self.bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        self.hsv = cv2.cvtColor(self.bgr, cv2.COLOR_BGR2HSV).astype(np.float32)

        # 亮度通道 L: 0~255
        self.luminance = self.lab[:, :, 0]
        # 归一化亮度 0~1
        self.l_norm = self.luminance / 255.0

        self.stats: Dict[str, Any] = self._compute_global_stats()

    @staticmethod
    def _downsample(bgr: np.ndarray, max_size: int) -> np.ndarray:
        h, w = bgr.shape[:2]
        scale = min(1.0, max_size / max(h, w))
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return bgr

    def _compute_global_stats(self) -> Dict[str, Any]:
        """预计算全局统计量，各模块可复用。"""
        l = self.l_norm
        r, g, b = self.rgb[:, :, 0], self.rgb[:, :, 1], self.rgb[:, :, 2]
        s = self.hsv[:, :, 1] / 255.0  # 饱和度 0~1
        a_ch, b_ch = self.lab[:, :, 1], self.lab[:, :, 2]

        # 分位数用于高光/阴影推测
        percentiles = np.percentile(l, [1, 5, 10, 25, 50, 75, 90, 95, 99])

        return {
            "mean_luminance": float(np.mean(l)),
            "std_luminance": float(np.std(l)),
            "median_luminance": float(np.median(l)),
            "percentiles_l": percentiles.tolist(),
            "mean_saturation": float(np.mean(s)),
            "std_saturation": float(np.std(s)),
            "mean_rgb": [float(np.mean(r)), float(np.mean(g)), float(np.mean(b))],
            "mean_lab_ab": [float(np.mean(a_ch)), float(np.mean(b_ch))],
            "highlight_ratio": float(np.mean(l > 0.85)),
            "shadow_ratio": float(np.mean(l < 0.15)),
            "pixel_count": int(l.size),
            "downsampled_shape": self.bgr.shape[:2],
        }


class BaseAnalyzer(abc.ABC):
    """参数推测模块抽象基类。"""

    module_id: str = "base"
    display_name: str = "Base"

    @abc.abstractmethod
    def analyze(self, ctx: ImageContext) -> ParameterResult:
        """从 ImageContext 推测参数，返回 ParameterResult。"""

    def _ok(
        self,
        key: str,
        display_name: str,
        value: Any,
        confidence: float,
        message: str = "",
        raw_stats: Optional[Dict[str, Any]] = None,
    ) -> ParameterResult:
        return ParameterResult(
            key=key,
            display_name=display_name,
            value=value,
            status=ParameterStatus.OK,
            confidence=confidence,
            message=message,
            raw_stats=raw_stats or {},
        )

    def _failed(self, key: str, display_name: str, error: str) -> ParameterResult:
        return ParameterResult(
            key=key,
            display_name=display_name,
            status=ParameterStatus.FAILED,
            message=f"推测失败: {error}",
        )

    def _skipped(self, key: str, display_name: str, reason: str) -> ParameterResult:
        return ParameterResult(
            key=key,
            display_name=display_name,
            status=ParameterStatus.SKIPPED,
            message=reason,
        )

    def _missing(self, key: str, display_name: str) -> ParameterResult:
        return ParameterResult(
            key=key,
            display_name=display_name,
            status=ParameterStatus.MISSING,
            message="模块已禁用",
        )


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def map_linear(value: float, in_lo: float, in_hi: float, out_lo: float, out_hi: float) -> float:
    """将 value 从 [in_lo, in_hi] 线性映射到 [out_lo, out_hi]。"""
    if in_hi == in_lo:
        return out_lo
    t = (value - in_lo) / (in_hi - in_lo)
    return out_lo + t * (out_hi - out_lo)
