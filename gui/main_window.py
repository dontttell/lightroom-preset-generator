"""
主窗口 v2 — 双路径：metadata 精确提取 / AI 辅助学习
布局与交互对齐 UI_UX_DESIGN.md v1.6.0
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QGroupBox,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from config.ai_config import load_ai_config
from config.settings import SETTINGS
from core.inference_result import AnalysisMode, ImageSession
from generators.xmp_generator import XMPGenerator
from gui import copy as C
from gui.export_dialog import ExportDialog
from gui.settings_dialog import SettingsDialog
from gui.widgets import (
    AiConfigBanner,
    AiStatusChip,
    ImageZone,
    LearningPanel,
    StatusCard,
)
from gui.workers import AiAnalysisWorker, MetadataWorker
from lut.lut_applier import apply_lut
from lut.lut_generator import build_lut_from_params, save_cube


def _load_stylesheet(app: QApplication) -> None:
    qss_path = Path(__file__).resolve().parent / "styles" / "app_dark.qss"
    if qss_path.is_file():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{SETTINGS.window_title}  (UI {SETTINGS.ui_version})")
        self.setMinimumSize(SETTINGS.window_min_width, SETTINGS.window_min_height)

        self.current_path: Optional[str] = None
        self.current_bgr: Optional[np.ndarray] = None
        self.session: Optional[ImageSession] = None
        self.plate_bgr: Optional[np.ndarray] = None
        self.plate_path: Optional[str] = None
        self.plate_lut_bgr: Optional[np.ndarray] = None
        self._ai_analyzing = False
        self._meta_worker: Optional[MetadataWorker] = None
        self._ai_worker: Optional[AiAnalysisWorker] = None

        self.setAcceptDrops(True)
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._connect_signals()
        self._sync_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.ai_banner = AiConfigBanner()
        root.addWidget(self.ai_banner)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        preview_box = QGroupBox("图像")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(8, 12, 8, 8)
        self.image_zone = ImageZone()
        preview_layout.addWidget(self.image_zone, stretch=1)
        splitter.addWidget(preview_box)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        self.status_card = StatusCard()
        right_layout.addWidget(self.status_card)
        self.learning_panel = LearningPanel()
        right_layout.addWidget(self.learning_panel, stretch=1)
        splitter.addWidget(right)
        self._content_splitter = splitter
        self._split_normal = [638, 462]
        self._split_plate = [682, 418]
        splitter.setSizes(self._split_plate)
        root.addWidget(splitter, stretch=1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.ai_status_chip = AiStatusChip()
        self.status_bar.addPermanentWidget(self.ai_status_chip)
        self.status_bar.showMessage(C.t("status.ready"))

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("文件")
        self.action_open = QAction(C.t("toolbar.open"), self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addAction(self.action_open)
        self.action_export = QAction(C.t("toolbar.export"), self)
        self.action_export.setShortcut("Ctrl+S")
        self.action_export.setEnabled(False)
        file_menu.addAction(self.action_export)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)

        settings_menu = self.menuBar().addMenu("设置")
        self.action_settings = QAction(C.t("menu.settings_ai"), self)
        self.action_settings.setShortcut("Ctrl+,")
        settings_menu.addAction(self.action_settings)

        help_menu = self.menuBar().addMenu("帮助")
        help_menu.addAction(C.t("menu.about"), self.show_about)

    def _build_toolbar(self) -> None:
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)

        self.btn_open = QPushButton(C.t("toolbar.open"))
        self.btn_open.setObjectName("btnSecondary")
        self.btn_ai = QPushButton(C.t("toolbar.ai_analyze"))
        self.btn_ai.setObjectName("btnSecondary")
        self.btn_ai.setEnabled(False)
        self.btn_ai.setToolTip(C.t("ai.tooltip_disabled"))
        self.btn_export = QPushButton(C.t("toolbar.export"))
        self.btn_export.setObjectName("btnPrimary")
        self.btn_export.setEnabled(False)

        tb.addWidget(self.btn_open)
        tb.addWidget(self.btn_ai)
        tb.addWidget(self.btn_export)

    def _connect_signals(self) -> None:
        self.action_open.triggered.connect(self.open_image)
        self.action_export.triggered.connect(self.export_files)
        self.action_settings.triggered.connect(self.open_settings)
        self.btn_open.clicked.connect(self.open_image)
        self.btn_ai.clicked.connect(self.run_ai_analysis)
        self.btn_export.clicked.connect(self.export_files)
        self.image_zone.pick_requested.connect(self.pick_plate)
        self.image_zone.apply_lut_requested.connect(self.preview_lut_on_plate)
        self.image_zone.plate_dropped.connect(self.load_plate_from_path)

        self.ai_banner.settings_clicked.connect(self.open_settings)
        self.ai_status_chip.clicked.connect(self.open_settings)
        self.learning_panel.settings_clicked.connect(self.open_settings)

    def _is_path_b_session(self) -> bool:
        if self.session is None:
            return True
        return self.session.mode == AnalysisMode.AI_LEARNING

    def _is_lut_preview_available(self) -> bool:
        return (
            self.session is not None
            and self.session.lut_cube is not None
        )

    def _should_show_plate_section(self) -> bool:
        """路径 A 隐藏底片区；其余态（含空态）显示。"""
        return self.session is None or self.session.mode != AnalysisMode.PRECISE

    def _plate_guide_text(self) -> str:
        if self.session is None:
            return C.t("plate.idle_hint")
        if self.session.mode == AnalysisMode.PRECISE:
            return ""
        if not self._is_lut_preview_available():
            return C.t("plate.wait_lut")
        return C.t("plate.pick_panel_hint")

    def _sync_plate_toolbar_state(self) -> None:
        lut_ready = self._is_lut_preview_available()
        can_apply = lut_ready and self.plate_bgr is not None
        self.image_zone.set_upload_enabled(lut_ready)
        self.image_zone.set_apply_lut_enabled(can_apply)
        self.image_zone.set_plate_drop_enabled(lut_ready)

    def _adjust_content_splitter(self) -> None:
        sizes = (
            self._split_plate
            if self._should_show_plate_section()
            else self._split_normal
        )
        self._content_splitter.setSizes(sizes)

    def _reset_plate(self) -> None:
        self.plate_bgr = None
        self.plate_path = None
        self.plate_lut_bgr = None
        self.image_zone.set_plate_status(None)
        self.image_zone.set_upload_enabled(False)
        self.image_zone.set_apply_lut_enabled(False)
        self.image_zone.set_plate_drop_enabled(False)

    def _refresh_image_zone(self) -> None:
        self._adjust_content_splitter()
        if self.current_bgr is None:
            self.image_zone.show_empty()
        else:
            self.image_zone.set_reference(self.current_bgr)

        if not self._should_show_plate_section():
            self.image_zone.set_plate_section_visible(False)
            return

        guide = self._plate_guide_text()
        if self.plate_bgr is None:
            self.image_zone.show_plate_pick(guide=guide)
        else:
            self.image_zone.show_compare(self.plate_bgr, self.plate_lut_bgr)
        self._sync_plate_toolbar_state()

    def _sync_ui(self) -> None:
        cfg = load_ai_config()
        ai_ready = cfg.is_ready()

        self.ai_status_chip.update_state(ai_ready)
        self.ai_banner.set_visible(not ai_ready)

        if self._ai_analyzing:
            self.btn_ai.setEnabled(False)
            self.btn_export.setEnabled(False)
            self.action_export.setEnabled(False)
            return

        session = self.session
        if session is None:
            self.status_card.set_empty()
            self.learning_panel.show_welcome(ai_ready)
            self.btn_ai.setEnabled(False)
            self.btn_ai.setToolTip(
                C.t("ai.tooltip_no_image") if ai_ready else C.t("ai.tooltip_disabled")
            )
            self.btn_export.setEnabled(False)
            self.action_export.setEnabled(False)
            self._refresh_image_zone()
            return

        if session.mode == AnalysisMode.PRECISE:
            self.status_card.set_precise(session.metadata_message)
            self.learning_panel.show_session(session)
            self.btn_ai.setEnabled(False)
            self.btn_ai.setToolTip(C.t("ai.tooltip_path_a"))
            self.btn_export.setEnabled(True)
            self.action_export.setEnabled(True)
            self._refresh_image_zone()
            return

        if session.ai_report:
            self.status_card.set_ai_done()
            self.learning_panel.show_session(session)
            self.btn_ai.setEnabled(ai_ready)
            self.btn_ai.setToolTip("")
            self.btn_export.setEnabled(True)
            self.action_export.setEnabled(True)
        elif not ai_ready:
            self.status_card.set_ai_unconfigured()
            self.learning_panel.show_path_b_unconfigured()
            self.btn_ai.setEnabled(False)
            self.btn_ai.setToolTip(C.t("ai.tooltip_disabled"))
            self.btn_export.setEnabled(False)
            self.action_export.setEnabled(False)
        else:
            self.status_card.set_ai_pending()
            self.learning_panel.show_path_b_placeholder()
            self.btn_ai.setEnabled(True)
            self.btn_ai.setToolTip("")
            self.btn_export.setEnabled(False)
            self.action_export.setEnabled(False)

        self._refresh_image_zone()

    def dragEnterEvent(self, event) -> None:
        if not event.mimeData().hasUrls():
            return
        path = event.mimeData().urls()[0].toLocalFile()
        from gui.widgets import _is_image_path

        if _is_image_path(path):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        from gui.widgets import _is_image_path

        if not _is_image_path(path):
            return
        if (
            self._is_lut_preview_available()
            and self._should_show_plate_section()
            and self.current_bgr is not None
        ):
            self.load_plate_from_path(path)
        else:
            self.load_image(path)
        event.acceptProposedAction()

    def open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec():
            self._sync_ui()

    def open_image(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            C.t("toolbar.open"),
            "",
            "图像 (*.jpg *.jpeg *.png *.webp *.tif *.tiff);;所有文件 (*.*)",
        )
        if path:
            self.load_image(path)

    def load_image(self, path: str) -> None:
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            QMessageBox.warning(self, "错误", C.t("error.read_image", path=path))
            return

        self.current_path = path
        self.current_bgr = bgr
        self.session = None
        self._reset_plate()
        self._ai_analyzing = False
        self.learning_panel.clear()

        self.status_bar.showMessage(C.t("status.detecting"))
        self._meta_worker = MetadataWorker(path)
        self._meta_worker.finished.connect(self._on_metadata_done)
        self._meta_worker.error.connect(self._on_metadata_error)
        self._meta_worker.start()
        self._refresh_image_zone()

    def _on_metadata_done(self, session: ImageSession) -> None:
        self.session = session
        self._sync_ui()
        if session.mode == AnalysisMode.PRECISE:
            self.status_bar.showMessage(
                C.t(
                    "status.bar_precise",
                    filename=Path(session.image_path).name,
                    ms=session.scan_ms,
                )
            )
        else:
            self.status_bar.showMessage(
                C.t("status.bar_ai_pending", filename=Path(session.image_path).name)
            )

    def _on_metadata_error(self, msg: str) -> None:
        QMessageBox.critical(self, "错误", C.t("error.metadata", reason=msg))
        self.status_bar.showMessage(C.t("status.detect_failed"))

    def run_ai_analysis(self) -> None:
        if not self.current_path:
            return
        cfg = load_ai_config()
        if not cfg.is_ready():
            QMessageBox.information(self, "AI 未配置", C.t("error.ai_not_configured"))
            self.open_settings()
            return

        self._ai_analyzing = True
        self.status_card.set_ai_analyzing()
        self.btn_ai.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.action_export.setEnabled(False)
        self.status_bar.showMessage(C.t("status.ai_running"))
        self._ai_worker = AiAnalysisWorker(self.current_path)
        self._ai_worker.finished.connect(self._on_ai_done)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

    def _on_ai_done(self, session: ImageSession) -> None:
        self._ai_analyzing = False
        self.session = session
        self._reset_plate()
        self._sync_ui()
        self.status_bar.showMessage(
            C.t(
                "status.bar_ai_done",
                filename=Path(session.image_path).name,
                ms=session.scan_ms,
            )
        )

    def _on_ai_error(self, msg: str) -> None:
        self._ai_analyzing = False
        self._sync_ui()
        QMessageBox.critical(self, "错误", C.t("error.ai_failed", reason=msg))
        self.status_bar.showMessage(C.t("status.ai_failed"))

    def load_plate_from_path(self, path: str) -> None:
        if not self._is_lut_preview_available():
            return
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            QMessageBox.warning(self, "错误", C.t("error.read_plate"))
            return
        self.plate_path = path
        self.plate_bgr = bgr
        self.plate_lut_bgr = None
        self.image_zone.set_plate_status(path)
        self._sync_plate_toolbar_state()
        self._refresh_image_zone()

    def pick_plate(self) -> None:
        if not self._is_lut_preview_available():
            QMessageBox.information(self, "提示", C.t("plate.wait_lut"))
            return
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            C.t("plate.pick"),
            "",
            "图像 (*.jpg *.jpeg *.png *.webp);;所有文件 (*.*)",
        )
        if path:
            self.load_plate_from_path(path)

    def preview_lut_on_plate(self) -> None:
        if self.plate_bgr is None or self.session is None or self.session.lut_cube is None:
            return
        try:
            self.plate_lut_bgr = apply_lut(self.plate_bgr, self.session.lut_cube)
            self._refresh_image_zone()
            self.status_bar.showMessage(C.t("status.lut_preview_ok"))
        except Exception as exc:
            QMessageBox.warning(self, C.t("error.preview_failed"), str(exc))

    def export_files(self) -> None:
        if self.session is None:
            QMessageBox.information(self, "提示", C.t("info.export_need_session"))
            return
        if self.session.mode == AnalysisMode.AI_LEARNING and not self.session.ai_report:
            QMessageBox.information(self, "提示", C.t("info.export_need_ai"))
            return

        default_name = f"{Path(self.session.image_path).stem} Preset"
        dlg = ExportDialog(self.session, default_name, self)
        if not dlg.exec():
            return

        preset_name = dlg.name_edit.text().strip() or default_name
        written = []
        try:
            if dlg.export_xmp:
                gen = XMPGenerator(preset_name=preset_name)
                gen.save(self.session.parameters, dlg.xmp_path)
                written.append(dlg.xmp_path)
            if dlg.export_lut:
                lut = self.session.lut_cube
                if lut is None:
                    params = {
                        p.key: p.value
                        for p in self.session.parameters
                        if p.is_available
                    }
                    lut = build_lut_from_params(params)
                save_cube(lut, dlg.lut_path, title=preset_name)
                written.append(dlg.lut_path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return

        QMessageBox.information(
            self,
            "导出成功",
            C.t("info.export_ok", paths="\n".join(written)),
        )
        self.status_bar.showMessage(C.t("status.export_done"))

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            C.t("menu.about"),
            f"<h3>{C.t('about.title_app')}</h3>"
            f"<p>UI 版本：{SETTINGS.ui_version}</p>"
            f"{C.t('about.body')}"
        )


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(SETTINGS.window_title)
    _load_stylesheet(app)
    window = MainWindow()
    window.show()
    return app.exec()
