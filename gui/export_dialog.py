"""导出对话框 — 用户自选保存路径与格式。"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui import copy as C
from core.inference_result import AnalysisMode, ImageSession


class ExportDialog(QDialog):
    def __init__(self, session: ImageSession, preset_name: str, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle(C.t("export.title"))
        self.setMinimumWidth(520)

        self.xmp_path = ""
        self.lut_path = ""
        self.export_xmp = False
        self.export_lut = False

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(preset_name)
        form.addRow(C.t("export.preset_name"), self.name_edit)

        self.xmp_check = QCheckBox(C.t("export.xmp_check"))
        self.xmp_check.setChecked(True)

        self.lut_check = QCheckBox(C.t("export.lut_check"))
        self.lut_check.setChecked(False)

        self.xmp_path_edit = QLineEdit()
        self.xmp_path_edit.setPlaceholderText("点击浏览选择 .xmp 保存路径")
        xmp_row = QHBoxLayout()
        xmp_row.addWidget(self.xmp_path_edit)
        btn_xmp = QPushButton("浏览…")
        btn_xmp.clicked.connect(self._browse_xmp)
        xmp_row.addWidget(btn_xmp)

        self.lut_path_edit = QLineEdit()
        self.lut_path_edit.setPlaceholderText("点击浏览选择 .cube 保存路径")
        lut_row = QHBoxLayout()
        lut_row.addWidget(self.lut_path_edit)
        btn_lut = QPushButton("浏览…")
        btn_lut.clicked.connect(self._browse_lut)
        lut_row.addWidget(btn_lut)

        self.lut_path_widget = QWidget()
        lut_path_layout = QFormLayout(self.lut_path_widget)
        lut_path_layout.setContentsMargins(0, 0, 0, 0)
        lut_path_layout.addRow("LUT 保存路径", lut_row)

        form.addRow("", self.xmp_check)
        form.addRow("XMP 保存路径", xmp_row)
        form.addRow("", self.lut_check)
        form.addRow(self.lut_path_widget)
        layout.addLayout(form)

        hint = QLabel(C.t("export.lut_hint"))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        stem = Path(session.image_path).stem
        default_dir = Path(session.image_path).parent
        self.xmp_path_edit.setText(str(default_dir / f"{stem} Preset.xmp"))
        self.lut_path_edit.setText(str(default_dir / f"{stem} Style.cube"))

        is_precise = session.mode == AnalysisMode.PRECISE
        if not is_precise and session.lut_cube is None:
            self.lut_check.setEnabled(False)

        self.lut_path_widget.setVisible(self.lut_check.isChecked())
        self.lut_check.toggled.connect(self._on_lut_toggled)

    def _on_lut_toggled(self, checked: bool) -> None:
        self.lut_path_widget.setVisible(checked)

    def _browse_xmp(self) -> None:
        name = self.name_edit.text().strip() or "Preset"
        path, _ = QFileDialog.getSaveFileName(self, "选择 XMP 保存路径", f"{name}.xmp", "XMP (*.xmp)")
        if path:
            self.xmp_path_edit.setText(path)

    def _browse_lut(self) -> None:
        name = self.name_edit.text().strip() or "Style"
        path, _ = QFileDialog.getSaveFileName(
            self, "选择 LUT 保存路径", f"{name}.cube", "LUT (*.cube)"
        )
        if path:
            self.lut_path_edit.setText(path)

    def _accept(self) -> None:
        self.export_xmp = self.xmp_check.isChecked()
        self.export_lut = self.lut_check.isChecked() and self.lut_check.isEnabled()
        self.xmp_path = self.xmp_path_edit.text().strip()
        self.lut_path = self.lut_path_edit.text().strip()

        if self.export_xmp and not self.xmp_path:
            QMessageBox.warning(self, "导出", "请选择 XMP 保存路径。")
            return
        if self.export_lut and not self.lut_path:
            QMessageBox.warning(self, "导出", "请选择 LUT 保存路径。")
            return
        if not self.export_xmp and not self.export_lut:
            QMessageBox.warning(self, "导出", "请至少选择一种导出格式。")
            return
        self.accept()
