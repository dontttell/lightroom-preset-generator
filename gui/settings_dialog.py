"""AI 服务设置对话框。"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from gui import copy as C
from ai.factory import create_analyzer
from config.ai_config import AiConfig, load_ai_config, save_ai_config


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(C.t("settings.title"))
        self.setMinimumWidth(480)
        self._cfg = load_ai_config()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("留空则尝试读取环境变量 OPENAI_API_KEY")
        self.api_key_edit.setText(self._cfg.api_key)

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("OpenAI 兼容接口地址，可留空使用默认")
        self.base_url_edit.setText(self._cfg.base_url)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("例如 gpt-4o-mini（需自行填写）")
        self.model_edit.setText(self._cfg.model)

        form.addRow("API Key", self.api_key_edit)
        form.addRow("API Base URL", self.base_url_edit)
        form.addRow("模型名称", self.model_edit)
        layout.addLayout(form)

        hint = QLabel(C.t("settings.privacy"))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _collect(self) -> AiConfig:
        return AiConfig(
            provider="openai_compatible",
            api_key=self.api_key_edit.text().strip(),
            base_url=self.base_url_edit.text().strip(),
            model=self.model_edit.text().strip(),
            language=self._cfg.language,
            prompt_file=self._cfg.prompt_file,
        )

    def _save(self) -> None:
        cfg = self._collect()
        save_ai_config(cfg)
        self._cfg = cfg
        self.accept()

    def _test_connection(self) -> None:
        cfg = self._collect()
        if not cfg.is_ready():
            QMessageBox.warning(self, "测试连接", "请先填写 API Key 与模型名称。")
            return
        try:
            msg = create_analyzer(cfg).test_connection()
            QMessageBox.information(self, "测试连接", msg)
        except Exception as exc:
            QMessageBox.critical(self, "测试连接失败", str(exc))
