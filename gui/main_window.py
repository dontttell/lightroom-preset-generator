"""
主窗口
------
布局：
  ┌─────────────────────────────────────────────────────────┐
  │ 菜单栏：文件 | 分析 | 帮助                                  │
  ├─────────────────────────────────────────────────────────┤
  │ 工具栏：[打开] [分析] [导出XMP] [预览效果] | 预设名称输入框    │
  ├──────────────────────┬──────────────────────────────────┤
  │  原图预览             │  参数推测结果列表                  │
  │                      │  ─────────────────                │
  │  模拟预览（可选）      │  缺失参数提示区                    │
  ├──────────────────────┴──────────────────────────────────┤
  │ 状态栏：路径 | 分析耗时 | 提示                              │
  └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from config.settings import SETTINGS
from core.inference_result import AnalysisReport
from core.pipeline import AnalysisPipeline
from generators.xmp_generator import XMPGenerator
from gui.widgets import ImagePreviewLabel, ParameterListWidget
from preview.preset_simulator import simulate_preset


class AnalyzeWorker(QThread):
    """后台线程执行分析，避免阻塞 GUI。"""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, pipeline: AnalysisPipeline, image_path: str):
        super().__init__()
        self.pipeline = pipeline
        self.image_path = image_path

    def run(self) -> None:
        try:
            report = self.pipeline.analyze_file(self.image_path)
            self.finished.emit(report)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(SETTINGS.window_title)
        self.setMinimumSize(SETTINGS.window_min_width, SETTINGS.window_min_height)

        self.pipeline = AnalysisPipeline()
        self.current_path: Optional[str] = None
        self.current_bgr: Optional[np.ndarray] = None
        self.current_report: Optional[AnalysisReport] = None
        self._worker: Optional[AnalyzeWorker] = None

        self.setAcceptDrops(True)
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._connect_signals()

    # ── UI 构建 ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # 工具栏下方：预设名称 + 模块快捷开关提示
        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("预设名称:"))
        self.preset_name_edit = QLineEdit("Generated Preset")
        self.preset_name_edit.setPlaceholderText("导出 XMP 时使用的预设名")
        meta_row.addWidget(self.preset_name_edit, stretch=1)
        root.addLayout(meta_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：双图预览
        preview_box = QGroupBox("图像预览")
        preview_layout = QVBoxLayout(preview_box)
        self.original_preview = ImagePreviewLabel("拖入或点击「打开图片」")
        self.original_preview.setAcceptDrops(True)
        self.simulated_preview = ImagePreviewLabel("分析后点击「预览效果」")
        preview_layout.addWidget(QLabel("原图"))
        preview_layout.addWidget(self.original_preview, stretch=1)
        preview_layout.addWidget(QLabel("模拟效果（近似预览）"))
        preview_layout.addWidget(self.simulated_preview, stretch=1)
        splitter.addWidget(preview_box)

        # 右侧：参数 + 缺失提示
        result_box = QGroupBox("推测参数")
        result_layout = QVBoxLayout(result_box)
        self.param_list = ParameterListWidget()
        result_layout.addWidget(self.param_list, stretch=2)

        missing_box = QGroupBox("缺失 / 未推测参数提示")
        missing_layout = QVBoxLayout(missing_box)
        self.missing_text = QTextEdit()
        self.missing_text.setReadOnly(True)
        self.missing_text.setMaximumHeight(120)
        self.missing_text.setPlaceholderText("分析完成后，未能推测的参数将显示在此")
        missing_layout.addWidget(self.missing_text)
        result_layout.addWidget(missing_box, stretch=1)

        stats_box = QGroupBox("分析统计 (Debug)")
        stats_layout = QVBoxLayout(stats_box)
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        stats_layout.addWidget(self.stats_text)
        result_layout.addWidget(stats_box)

        splitter.addWidget(result_box)
        splitter.setSizes([580, 420])
        root.addWidget(splitter, stretch=1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 — 请打开 JPG 图片")

        self.setStyleSheet(
            """
            QMainWindow { background: #f5f5f5; }
            QGroupBox { font-weight: bold; margin-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { padding: 6px 14px; }
            QToolBar { spacing: 6px; padding: 4px; }
            """
        )

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")
        self.action_open = QAction("打开图片(&O)...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addAction(self.action_open)

        self.action_export = QAction("导出 XMP(&E)...", self)
        self.action_export.setShortcut("Ctrl+S")
        self.action_export.setEnabled(False)
        file_menu.addAction(self.action_export)

        file_menu.addSeparator()
        self.action_quit = QAction("退出(&Q)", self)
        self.action_quit.setShortcut(QKeySequence.StandardKey.Quit)
        file_menu.addAction(self.action_quit)

        analyze_menu = menubar.addMenu("分析(&A)")
        self.action_analyze = QAction("开始分析(&R)", self)
        self.action_analyze.setShortcut("F5")
        self.action_analyze.setEnabled(False)
        analyze_menu.addAction(self.action_analyze)

        self.action_preview = QAction("预览效果(&P)", self)
        self.action_preview.setShortcut("F6")
        self.action_preview.setEnabled(False)
        analyze_menu.addAction(self.action_preview)

        help_menu = menubar.addMenu("帮助(&H)")
        self.action_about = QAction("关于(&A)", self)
        help_menu.addAction(self.action_about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("主工具栏")
        tb.setMovable(False)
        self.addToolBar(tb)

        self.btn_open = QPushButton("打开图片")
        self.btn_analyze = QPushButton("开始分析")
        self.btn_analyze.setEnabled(False)
        self.btn_preview = QPushButton("预览效果")
        self.btn_preview.setEnabled(False)
        self.btn_export = QPushButton("导出 XMP")
        self.btn_export.setEnabled(False)

        tb.addWidget(self.btn_open)
        tb.addWidget(self.btn_analyze)
        tb.addWidget(self.btn_preview)
        tb.addSeparator()
        tb.addWidget(self.btn_export)

    def _connect_signals(self) -> None:
        self.action_open.triggered.connect(self.open_image)
        self.action_export.triggered.connect(self.export_xmp)
        self.action_quit.triggered.connect(self.close)
        self.action_analyze.triggered.connect(self.run_analysis)
        self.action_preview.triggered.connect(self.run_preview)
        self.action_about.triggered.connect(self.show_about)

        self.btn_open.clicked.connect(self.open_image)
        self.btn_analyze.clicked.connect(self.run_analysis)
        self.btn_preview.clicked.connect(self.run_preview)
        self.btn_export.clicked.connect(self.export_xmp)

    # ── 拖放支持 ─────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                self.load_image(path)

    # ── 业务逻辑 ─────────────────────────────────────────────

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图像文件 (*.jpg *.jpeg *.png *.webp);;所有文件 (*.*)",
        )
        if path:
            self.load_image(path)

    def load_image(self, path: str) -> None:
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            QMessageBox.warning(self, "错误", f"无法读取图像:\n{path}")
            return

        self.current_path = path
        self.current_bgr = bgr
        self.current_report = None
        self.original_preview.set_image_bgr(bgr)
        self.simulated_preview.clear_image("分析后点击「预览效果」")
        self.param_list.clear()
        self.missing_text.clear()
        self.stats_text.clear()

        name_stem = Path(path).stem
        self.preset_name_edit.setText(f"{name_stem} Preset")

        self.btn_analyze.setEnabled(True)
        self.action_analyze.setEnabled(True)
        self.btn_preview.setEnabled(False)
        self.action_preview.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.action_export.setEnabled(False)

        self.status_bar.showMessage(f"已加载: {path}")

    def run_analysis(self) -> None:
        if not self.current_path:
            return

        self.btn_analyze.setEnabled(False)
        self.action_analyze.setEnabled(False)
        self.status_bar.showMessage("分析中...")

        self._worker = AnalyzeWorker(self.pipeline, self.current_path)
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_done(self, report: AnalysisReport) -> None:
        self.current_report = report
        self.param_list.set_parameters(report.parameters)

        flat = AnalysisPipeline.flatten_for_xmp(report)
        missing_lines = XMPGenerator.missing_summary(flat)
        if missing_lines:
            self.missing_text.setPlainText("\n".join(missing_lines))
        else:
            self.missing_text.setPlainText("所有参数均已成功推测。")

        stats = report.image_stats
        stats_lines = [
            f"分析耗时: {report.analysis_ms:.1f} ms",
            f"下采样尺寸: {stats.get('downsampled_shape')}",
            f"平均亮度: {stats.get('mean_luminance', 0):.3f}",
            f"亮度标准差: {stats.get('std_luminance', 0):.3f}",
            f"平均饱和度: {stats.get('mean_saturation', 0):.3f}",
        ]
        self.stats_text.setPlainText("\n".join(stats_lines))

        self.btn_analyze.setEnabled(True)
        self.action_analyze.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.action_preview.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.action_export.setEnabled(True)

        ok_count = sum(1 for p in report.parameters if p.is_available)
        total = len(report.parameters)
        self.status_bar.showMessage(
            f"分析完成 — {ok_count}/{total} 模块成功，耗时 {report.analysis_ms:.0f} ms"
        )

    def _on_analysis_error(self, msg: str) -> None:
        self.btn_analyze.setEnabled(True)
        self.action_analyze.setEnabled(True)
        QMessageBox.critical(self, "分析失败", msg)
        self.status_bar.showMessage("分析失败")

    def run_preview(self) -> None:
        if self.current_bgr is None or self.current_report is None:
            return

        flat = AnalysisPipeline.flatten_for_xmp(self.current_report)
        params = {p.key: p.value for p in flat if p.is_available}
        simulated = simulate_preset(self.current_bgr, params)
        self.simulated_preview.set_image_bgr(simulated)
        self.status_bar.showMessage(
            f"预览已更新 — 应用了 {len(params)} 个参数（OpenCV 近似，与 LR 有差异）"
        )

    def export_xmp(self) -> None:
        if self.current_report is None:
            QMessageBox.information(self, "提示", "请先完成分析。")
            return

        default_name = self.preset_name_edit.text().strip() or "Generated Preset"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 XMP 预设",
            f"{default_name}.xmp",
            "Lightroom 预设 (*.xmp);;所有文件 (*.*)",
        )
        if not path:
            return

        flat = AnalysisPipeline.flatten_for_xmp(self.current_report)
        gen = XMPGenerator(preset_name=default_name)
        try:
            gen.save(flat, path)
        except OSError as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return

        QMessageBox.information(
            self,
            "导出成功",
            f"预设已保存至:\n{path}\n\n"
            "可将 .xmp 文件复制到 Lightroom 预设目录，"
            "或通过 Lightroom「导入预设」功能导入。",
        )
        self.status_bar.showMessage(f"已导出: {path}")

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "关于",
            "<h3>Lightroom 预设生成器</h3>"
            "<p>从 JPG 图像启发式推测 Lightroom 全局调整参数，并导出 Adobe XMP 预设。</p>"
            "<p><b>注意：</b>结果为近似推测，无法还原局部调整、HSL 分通道、曲线控制点等复杂设置。</p>"
            "<p>模块开关见 <code>config/settings.py</code></p>",
        )


def run_app() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(SETTINGS.window_title)
    window = MainWindow()
    window.show()
    return app.exec()
