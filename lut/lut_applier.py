"""
3D LUT 应用 — 三线性插值（OpenCV/NumPy，非 LR 引擎）
"""

from __future__ import annotations

import numpy as np


def apply_lut(bgr: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """
    对 BGR uint8 图像应用 LUT。
    lut: (size, size, size, 3) RGB 0~1
    """
    if lut is None:
        raise ValueError("LUT 为空")
    size = lut.shape[0]
    scale = size - 1

    rgb = bgr[:, :, ::-1].astype(np.float32) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    r0 = np.clip(np.floor(r * scale), 0, scale - 1).astype(np.int32)
    g0 = np.clip(np.floor(g * scale), 0, scale - 1).astype(np.int32)
    b0 = np.clip(np.floor(b * scale), 0, scale - 1).astype(np.int32)
    r1 = np.clip(r0 + 1, 0, scale - 1)
    g1 = np.clip(g0 + 1, 0, scale - 1)
    b1 = np.clip(b0 + 1, 0, scale - 1)

    fr = r * scale - r0
    fg = g * scale - g0
    fb = b * scale - b0

    def sample(ri, gi, bi):
        return lut[ri, gi, bi]

    c000 = sample(r0, g0, b0)
    c001 = sample(r0, g0, b1)
    c010 = sample(r0, g1, b0)
    c011 = sample(r0, g1, b1)
    c100 = sample(r1, g0, b0)
    c101 = sample(r1, g0, b1)
    c110 = sample(r1, g1, b0)
    c111 = sample(r1, g1, b1)

    fr = fr[..., None]
    fg = fg[..., None]
    fb = fb[..., None]

    c00 = c000 * (1 - fb) + c001 * fb
    c01 = c010 * (1 - fb) + c011 * fb
    c10 = c100 * (1 - fb) + c101 * fb
    c11 = c110 * (1 - fb) + c111 * fb
    c0 = c00 * (1 - fg) + c01 * fg
    c1 = c10 * (1 - fg) + c11 * fg
    out_rgb = c0 * (1 - fr) + c1 * fr

    out_bgr = np.clip(out_rgb * 255.0, 0, 255).astype(np.uint8)
    return out_bgr[:, :, ::-1]
