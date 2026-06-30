"""
预设效果模拟器（预览）
----------------------
用 OpenCV 近似模拟 LR 全局调整，仅供 GUI 预览参考，非 Adobe 引擎。
各效果独立函数，缺失参数时跳过对应步骤。
"""

from __future__ import annotations

from typing import Dict, Optional

import cv2
import numpy as np


def _clamp_u8(arr: np.ndarray) -> np.ndarray:
    return np.clip(arr, 0, 255).astype(np.uint8)


def apply_exposure(bgr: np.ndarray, exposure: float) -> np.ndarray:
    """近似曝光：线性缩放。"""
    factor = 2.0 ** exposure
    out = bgr.astype(np.float32) * factor
    return _clamp_u8(out)


def apply_contrast(bgr: np.ndarray, contrast: int) -> np.ndarray:
    """对比度：围绕中灰缩放。"""
    factor = 1.0 + contrast / 100.0
    out = (bgr.astype(np.float32) - 128.0) * factor + 128.0
    return _clamp_u8(out)


def apply_saturation(bgr: np.ndarray, saturation: int) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    factor = 1.0 + saturation / 100.0
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def apply_temperature_tint(bgr: np.ndarray, temperature: int, tint: int) -> np.ndarray:
    """简化的色温/色调调整。"""
    out = bgr.astype(np.float32)
    # 色温：暖 = 增 R 减 B
    temp_delta = (temperature - 5500) / 5500.0
    out[:, :, 2] += temp_delta * 25  # R
    out[:, :, 0] -= temp_delta * 25  # B
    # 色调：绿-洋红
    out[:, :, 1] -= tint * 0.15
    return _clamp_u8(out)


def apply_clarity(bgr: np.ndarray, clarity: int) -> np.ndarray:
    """清晰度：反遮罩锐化/柔化近似。"""
    if clarity == 0:
        return bgr
    blur = cv2.GaussianBlur(bgr, (0, 0), 3)
    amount = clarity / 100.0 * 0.5
    out = cv2.addWeighted(bgr, 1 + amount, blur, -amount, 0)
    return _clamp_u8(out)


def apply_vignette(bgr: np.ndarray, amount: int) -> np.ndarray:
    if amount == 0:
        return bgr
    h, w = bgr.shape[:2]
    yy, xx = np.indices((h, w))
    cx, cy = w / 2, h / 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    mask = 1.0 - (dist / max_dist) * (amount / 100.0) * 0.6
    mask = np.clip(mask, 0.5, 1.2)
    out = bgr.astype(np.float32) * mask[:, :, np.newaxis]
    return _clamp_u8(out)


def simulate_preset(bgr: np.ndarray, params: Dict[str, object]) -> np.ndarray:
    """
    按可用参数依次应用预览效果。
    params 键名与 XMP crs 字段一致。
    """
    out = bgr.copy()

    if "Exposure2012" in params:
        out = apply_exposure(out, float(params["Exposure2012"]))

    if "Contrast2012" in params:
        out = apply_contrast(out, int(params["Contrast2012"]))

    if "Temperature" in params and "Tint" in params:
        out = apply_temperature_tint(out, int(params["Temperature"]), int(params["Tint"]))

    if "Saturation" in params:
        out = apply_saturation(out, int(params["Saturation"]))

    if "Clarity2012" in params:
        out = apply_clarity(out, int(params["Clarity2012"]))

    if "PostCropVignetteAmount" in params:
        out = apply_vignette(out, int(params["PostCropVignetteAmount"]))

    return out
