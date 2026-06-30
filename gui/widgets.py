"""
GUI 组件 — 学习面板、状态卡片、图像区、AI 提醒
对齐 UI_UX_DESIGN.md v1.6.0
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.inference_result import AiLearningReport, AnalysisMode, ImageSession, ParameterResult
from gui import copy as C
from gui.styles import tokens as T

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


def _is_image_path(path: str) -> bool:
    return path.lower().endswith(IMAGE_SUFFIXES)


class ImagePreviewLabel(QLabel):
    """图像预览；可选接受拖放。"""

    file_dropped = pyqtSignal(str)

    def __init__(
        self,
        placeholder: str | None = None,
        *,
        accept_drops: bool = False,
        min_width: int = 280,
        min_height: int = 420,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("imagePreview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(min_width, min_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setWordWrap(True)
        self._placeholder = placeholder or C.t("image.empty")
        self._pixmap: Optional[QPixmap] = None
        self._accept_drops = accept_drops
        if accept_drops:
            self.setAcceptDrops(True)
        self._set_placeholder_text()

    def _set_placeholder_text(self) -> None:
        self.setPixmap(QPixmap())
        self.setText(self._placeholder)

    def set_image_bgr(self, bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        self._pixmap = QPixmap.fromImage(qimg)
        self._refresh_scaled()

    def clear_image(self, placeholder: str | None = None) -> None:
        self._placeholder = placeholder or C.t("image.empty")
        self._pixmap = None
        self._set_placeholder_text()

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
        self.setText("")

    def _set_drop_hover(self, active: bool) -> None:
        self.setProperty("dropHover", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if not self._accept_drops or not event.mimeData().hasUrls():
            return
        path = event.mimeData().urls()[0].toLocalFile()
        if _is_image_path(path):
            event.acceptProposedAction()
            self._set_drop_hover(True)

    def dragLeaveEvent(self, event) -> None:
        self._set_drop_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if not self._accept_drops:
            return
        self._set_drop_hover(False)
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if _is_image_path(path):
            self.file_dropped.emit(path)
            event.acceptProposedAction()


class LabeledPreview(QWidget):
    """对比模式单格：标签 + 预览。"""

    file_dropped = pyqtSignal(str)

    def __init__(
        self,
        label_text: str,
        placeholder: str,
        *,
        accept_drops: bool = False,
        min_width: int = 280,
        min_height: int = 420,
        parent=None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._caption = QLabel(label_text)
        self._caption.setObjectName("previewCellLabel")
        self.preview = ImagePreviewLabel(
            placeholder,
            accept_drops=accept_drops,
            min_width=280,
            min_height=420,
        )
        if accept_drops:
            self.preview.file_dropped.connect(self.file_dropped.emit)
        layout.addWidget(self._caption)
        layout.addWidget(self.preview, stretch=1)

    def set_image_bgr(self, bgr: np.ndarray) -> None:
        self.preview.set_image_bgr(bgr)

    def clear_image(self, placeholder: str) -> None:
        self.preview.clear_image(placeholder)


class ImageZone(QWidget):
    """左侧图像区：参考图（上）+ 底片预览（下，§3.4 v1.6）。"""

    pick_requested = pyqtSignal()
    apply_lut_requested = pyqtSignal()
    plate_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(520)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        ref_caption = QLabel(C.t("image.reference"))
        ref_caption.setObjectName("previewCellLabel")
        root.addWidget(ref_caption)

        self._reference = ImagePreviewLabel(min_width=400, min_height=280)
        root.addWidget(self._reference, stretch=3)

        self._plate_section = QGroupBox(C.t("plate.section_title"))
        self._plate_section.setObjectName("platePreviewSection")
        plate_outer = QVBoxLayout(self._plate_section)
        plate_outer.setContentsMargins(8, 12, 8, 8)
        plate_outer.setSpacing(8)

        self._plate_toolbar = QWidget()
        self._plate_toolbar_layout = QHBoxLayout(self._plate_toolbar)
        self._plate_toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._btn_upload = QPushButton(C.t("plate.pick"))
        self._btn_upload.setObjectName("btnSecondary")
        self._btn_upload.setEnabled(False)
        self._btn_upload.clicked.connect(self.pick_requested.emit)
        self._plate_toolbar_layout.addWidget(self._btn_upload)
        self._btn_apply_lut = QPushButton(C.t("plate.apply_lut"))
        self._btn_apply_lut.setObjectName("btnSecondary")
        self._btn_apply_lut.setEnabled(False)
        self._btn_apply_lut.clicked.connect(self.apply_lut_requested.emit)
        self._plate_toolbar_layout.addWidget(self._btn_apply_lut)
        self._drop_hint = QLabel(C.t("plate.drop_hint"))
        self._drop_hint.setObjectName("previewCellLabel")
        self._drop_hint.setWordWrap(True)
        self._plate_toolbar_layout.addWidget(self._drop_hint, stretch=1)
        plate_outer.addWidget(self._plate_toolbar)

        self._pick_guide = QLabel(C.t("plate.idle_hint"))
        self._pick_guide.setObjectName("previewCellLabel")
        self._pick_guide.setWordWrap(True)
        plate_outer.addWidget(self._pick_guide)

        self._plate_status = QLabel(C.t("plate.no_plate"))
        self._plate_status.setObjectName("statusSubtitle")
        self._plate_status.setWordWrap(True)
        plate_outer.addWidget(self._plate_status)

        self._plate_stack = QStackedWidget()
        plate_outer.addWidget(self._plate_stack, stretch=2)

        self._pick_preview = ImagePreviewLabel(
            C.t("plate.placeholder_before"),
            accept_drops=False,
            min_width=360,
            min_height=280,
        )
        self._pick_preview.file_dropped.connect(self.plate_dropped.emit)
        self._plate_stack.addWidget(self._pick_preview)

        compare_root = QWidget()
        compare_layout = QVBoxLayout(compare_root)
        compare_layout.setContentsMargins(0, 0, 0, 0)
        self._compare_split = QSplitter(Qt.Orientation.Horizontal)
        self._pane_before = LabeledPreview(
            C.t("plate.label_before"),
            C.t("plate.placeholder_before"),
            accept_drops=False,
            min_width=240,
            min_height=280,
        )
        self._pane_before.file_dropped.connect(self.plate_dropped.emit)
        self._pane_after = LabeledPreview(
            C.t("plate.label_after"),
            C.t("plate.placeholder_after"),
            min_width=240,
            min_height=280,
        )
        self._compare_split.addWidget(self._pane_before)
        self._compare_split.addWidget(self._pane_after)
        self._compare_split.setSizes([500, 500])
        self._compare_split.setChildrenCollapsible(False)
        compare_layout.addWidget(self._compare_split)
        self._plate_stack.addWidget(compare_root)

        footnote = QLabel(C.t("plate.footnote"))
        footnote.setWordWrap(True)
        footnote.setObjectName("statusSubtitle")
        plate_outer.addWidget(footnote)

        root.addWidget(self._plate_section, stretch=2)
        self.show_plate_pick(guide=C.t("plate.idle_hint"))

    def _set_upload_button_label(self, *, replace: bool) -> None:
        self._btn_upload.setText(
            C.t("plate.pick_replace") if replace else C.t("plate.pick")
        )

    def set_plate_section_visible(self, visible: bool) -> None:
        self._plate_section.setVisible(visible)

    def set_upload_enabled(self, enabled: bool) -> None:
        self._btn_upload.setEnabled(enabled)

    def set_apply_lut_enabled(self, enabled: bool) -> None:
        self._btn_apply_lut.setEnabled(enabled)

    def set_plate_drop_enabled(self, enabled: bool) -> None:
        self._pick_preview.setAcceptDrops(enabled)
        self._pick_preview._accept_drops = enabled
        self._pane_before.preview.setAcceptDrops(enabled)
        self._pane_before.preview._accept_drops = enabled

    def set_plate_status(self, path: Optional[str]) -> None:
        if path:
            name = Path(path).name
            if len(name) > 40:
                name = name[:37] + "…"
            self._plate_status.setText(C.t("plate.selected", filename=name))
        else:
            self._plate_status.setText(C.t("plate.no_plate"))

    def set_reference(self, bgr: np.ndarray) -> None:
        self._reference.set_image_bgr(bgr)

    def show_empty(self) -> None:
        self._reference.clear_image()
        self.show_plate_pick(guide=C.t("plate.idle_hint"))
        self.set_plate_status(None)

    def show_plate_pick(self, *, guide: str | None = None) -> None:
        """参考图下方待选区（§3.4.1）。"""
        self._set_upload_button_label(replace=False)
        self._pick_guide.setText(guide or C.t("plate.pick_panel_hint"))
        self._pick_guide.show()
        self._plate_stack.setCurrentWidget(self._pick_preview)
        self._pick_preview.clear_image(C.t("plate.placeholder_before"))
        self.set_plate_section_visible(True)

    def show_compare(
        self,
        plate_bgr: np.ndarray,
        after_bgr: np.ndarray | None = None,
    ) -> None:
        self._set_upload_button_label(replace=True)
        self._pick_guide.hide()
        self._plate_stack.setCurrentIndex(1)
        self._pane_before.set_image_bgr(plate_bgr)
        if after_bgr is not None:
            self._pane_after.set_image_bgr(after_bgr)
        else:
            self._pane_after.clear_image(C.t("plate.placeholder_after"))
        self.set_plate_section_visible(True)


class AiStatusChip(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aiStatusChip")
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_state(False)

    def update_state(self, ready: bool) -> None:
        self.setProperty("configured", "true" if ready else "false")
        if ready:
            self.setText(C.t("ai.chip_configured"))
            self.setToolTip(C.t("ai.chip_tooltip_ready"))
        else:
            self.setText(C.t("ai.chip_unconfigured"))
            self.setToolTip(C.t("ai.chip_tooltip_setup"))
        self.style().unpolish(self)
        self.style().polish(self)


class AiConfigBanner(QFrame):
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aiConfigBanner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        icon = QLabel("⚠")
        icon.setObjectName("bannerIcon")
        layout.addWidget(icon)

        text = QLabel(C.t("ai.banner"))
        text.setObjectName("bannerText")
        layout.addWidget(text, stretch=1)

        btn = QPushButton(C.t("ai.banner_action"))
        btn.setObjectName("btnLink")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(btn)

    def set_visible(self, visible: bool) -> None:
        self.setVisible(visible)


class InlineAlert(QFrame):
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inlineAlert")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        title = QLabel(C.t("ai.inline_title"))
        title.setObjectName("inlineAlertTitle")
        layout.addWidget(title)

        body = QLabel(C.t("ai.inline_body"))
        body.setObjectName("inlineAlertBody")
        body.setWordWrap(True)
        layout.addWidget(body)

        btn = QPushButton(C.t("ai.banner_action"))
        btn.setObjectName("btnGhost")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)


class StatusCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 12, 0)
        root.setSpacing(0)

        self._bar = QFrame()
        self._bar.setFixedWidth(4)
        root.addWidget(self._bar)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(12, 10, 0, 10)
        self._title = QLabel()
        self._title.setObjectName("statusTitle")
        self._title.setWordWrap(True)
        self._subtitle = QLabel()
        self._subtitle.setObjectName("statusSubtitle")
        self._subtitle.setWordWrap(True)
        text_col.addWidget(self._title)
        text_col.addWidget(self._subtitle)
        root.addLayout(text_col, stretch=1)

        self._set_accent(T.ACCENT_AI_PENDING)
        self.set_empty()

    def _set_accent(self, color: str) -> None:
        self._bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")

    def set_empty(self) -> None:
        self._set_accent(T.BORDER_DEFAULT)
        self._title.setText(C.t("status.welcome.title"))
        self._subtitle.setText(C.t("status.welcome.subtitle"))

    def set_precise(self, message: str = "") -> None:
        self._set_accent(T.ACCENT_PRECISE)
        self._title.setText(C.t("status.precise.title"))
        self._subtitle.setText(message or C.t("status.precise.subtitle"))

    def set_ai_unconfigured(self) -> None:
        self._set_accent(T.ACCENT_DANGER)
        self._title.setText(C.t("status.no_meta_unconfigured.title"))
        self._subtitle.setText(C.t("status.no_meta_unconfigured.subtitle"))

    def set_ai_pending(self) -> None:
        self._set_accent(T.ACCENT_AI_PENDING)
        self._title.setText(C.t("status.no_meta_ready.title"))
        self._subtitle.setText(C.t("status.no_meta_ready.subtitle"))

    def set_ai_analyzing(self) -> None:
        self._set_accent(T.ACCENT_AI_PENDING)
        self._title.setText(C.t("status.ai_analyzing.title"))
        self._subtitle.setText(C.t("status.ai_analyzing.subtitle"))

    def set_ai_done(self) -> None:
        self._set_accent(T.ACCENT_AI_DONE)
        self._title.setText(C.t("status.ai_done.title"))
        self._subtitle.setText(C.t("status.ai_done.subtitle"))


class LearningPanel(QWidget):
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._inline_alert = InlineAlert()
        self._inline_alert.settings_clicked.connect(self.settings_clicked.emit)
        self._inline_alert.hide()
        layout.addWidget(self._inline_alert)

        self._editor = QTextEdit()
        self._editor.setObjectName("learningPanel")
        self._editor.setReadOnly(True)
        layout.addWidget(self._editor, stretch=1)

    def set_inline_alert_visible(self, visible: bool) -> None:
        self._inline_alert.setVisible(visible)

    def show_welcome(self, ai_ready: bool) -> None:
        self.set_inline_alert_visible(False)
        key = "learn.welcome_ready" if ai_ready else "learn.welcome_unconfigured"
        self._editor.setPlainText(C.t(key))

    def show_path_b_placeholder(self) -> None:
        self.set_inline_alert_visible(False)
        self._editor.setPlainText(C.t("learn.path_b_ready"))

    def show_path_b_unconfigured(self) -> None:
        self.set_inline_alert_visible(True)
        self._editor.setPlainText(C.t("learn.path_b_unconfigured"))

    def clear(self) -> None:
        self._editor.clear()
        self.set_inline_alert_visible(False)

    def show_session(self, session: ImageSession) -> None:
        self.set_inline_alert_visible(False)
        if session.mode == AnalysisMode.PRECISE:
            self._show_precise(session.parameter_groups)
        elif session.ai_report:
            self._show_ai(session.ai_report, session.parameter_groups)
        else:
            self.show_path_b_placeholder()

    def _show_precise(self, groups: List[Tuple[str, List[ParameterResult]]]) -> None:
        lines = ["【精确提取 — Camera Raw 参数】\n"]
        for group_name, params in groups:
            lines.append(f"■ {group_name}")
            for p in params:
                lines.append(f"  · {p.to_display_line()}")
            lines.append("")
        self._editor.setPlainText("\n".join(lines))

    def _show_ai(
        self,
        report: AiLearningReport,
        groups: List[Tuple[str, List[ParameterResult]]],
    ) -> None:
        lines = ["【整体印象】", report.overall_impression, "", "【修改思路】"]
        for step in report.editing_steps:
            title = step.get("title", "")
            desc = step.get("description", "")
            num = step.get("step", "")
            lines.append(f"{num}. {title} — {desc}")
        if report.priority_adjustments:
            lines.extend(["", "【建议优先调整】", " · ".join(report.priority_adjustments)])
        lines.extend(["", "【参考参数 · AI 推测】"])
        for group_name, params in groups:
            lines.append(f"■ {group_name}")
            for p in params:
                lines.append(f"  · {p.to_display_line()}")
        self._editor.setPlainText("\n".join(lines))
