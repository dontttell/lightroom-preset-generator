"""
LUT 生成：由参数字典烘焙 33³ .cube 数据（本地，非 LR 引擎）
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from preview.preset_simulator import apply_clarity, apply_contrast, apply_exposure, apply_saturation, apply_temperature_tint


def build_lut_from_params(params: Dict[str, Any], size: int = 33) -> np.ndarray:
    """
    返回 shape (size, size, size, 3) 的 LUT，RGB 顺序，值域 0~1。
    """
    grid = np.linspace(0, 1, size, dtype=np.float32)
    r, g, b = np.meshgrid(grid, grid, grid, indexing="ij")
    colors = np.stack([r, g, b], axis=-1).reshape(-1, 1, 3)
    colors_u8 = (colors * 255.0).astype(np.uint8)

    out = colors_u8.copy()
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

    lut = out.reshape(size, size, size, 3).astype(np.float32) / 255.0
    return lut


def save_cube(lut: np.ndarray, output_path: str, title: str = "Generated LUT") -> str:
    size = lut.shape[0]
    lines = [f"TITLE \"{title}\"", f"LUT_3D_SIZE {size}"]
    for ri in range(size):
        for gi in range(size):
            for bi in range(size):
                r, g, b = lut[ri, gi, bi]
                lines.append(f"{r:.6f} {g:.6f} {b:.6f}")
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
