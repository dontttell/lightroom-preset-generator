"""
GUI 组件
--------
ImagePreviewLabel: 可缩放图像显示
ParameterListWidget: 参数结果列表（含缺失/失败状态着色）
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QSizePolicy, QLabel

from core.inference_result import ParameterResult, ParameterStatus


class ImagePreviewLabel(QLabel):
    """保持宽高比的图像预览区域，支持拖拽提示。"""

    def __init__(self, placeholder: str = "未加载图片", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            "QLabel { background: #1e1e1e; color: #888; border: 1px solid #333; border-radius: 4px; }"
        )
        self._source_bgr: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None
        self.setText(placeholder)

    def set_image_bgr(self, bgr: np.ndarray) -> None:
        self._source_bgr = bgr
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        self._pixmap = QPixmap.fromImage(qimg)
        self._refresh_scaled()

    def clear_image(self, placeholder: str = "未加载图片") -> None:
        self._source_bgr = None
        self._pixmap = None
        self.setPixmap(QPixmap())
        self.setText(placeholder)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_scaled()

    def _refresh_scaled(self) -> None:
        if self._pixmap is None or self._pixmap.isNull():
            return
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)


class ParameterListWidget(QListWidget):
    """展示推测参数，按状态着色。"""

    STATUS_COLORS = {
        ParameterStatus.OK: "#c8e6c9",
        ParameterStatus.MISSING: "#fff9c4",
        ParameterStatus.FAILED: "#ffcdd2",
        ParameterStatus.SKIPPED: "#e0e0e0",
    }

    def set_parameters(self, parameters: list[ParameterResult]) -> None:
        self.clear()
        for param in parameters:
            item = QListWidgetItem(param.to_display_line())
            color = self.STATUS_COLORS.get(param.status, "#ffffff")
            item.setBackground(Qt.GlobalColor.transparent)
            item.setData(Qt.ItemDataRole.UserRole, param)
            item.setToolTip(self._tooltip(param))
            self.addItem(item)
            # 使用 stylesheet 逐行着色较繁琐，改用 foreground
            from PyQt6.QtGui import QColor, QBrush

            if param.status == ParameterStatus.OK:
                item.setForeground(QBrush(QColor("#2e7d32")))
            elif param.status == ParameterStatus.MISSING:
                item.setForeground(QBrush(QColor("#f57f17")))
            elif param.status == ParameterStatus.FAILED:
                item.setForeground(QBrush(QColor("#c62828")))
            else:
                item.setForeground(QBrush(QColor("#616161")))

    @staticmethod
    def _tooltip(param: ParameterResult) -> str:
        lines = [f"字段: {param.key}", f"状态: {param.status.value}"]
        if param.message:
            lines.append(f"说明: {param.message}")
        if param.raw_stats:
            stats = ", ".join(f"{k}={v}" for k, v in param.raw_stats.items())
            lines.append(f"Debug: {stats}")
        return "\n".join(lines)
