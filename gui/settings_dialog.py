"""AI 服务设置对话框。"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
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
from config.provider_presets import PRESET_CUSTOM, get_preset, list_presets


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(C.t("settings.title"))
        self.setMinimumWidth(520)
        self._cfg = load_ai_config()
        self._applying_preset = False
        self._build_ui()
        self._load_from_config()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.preset_combo = QComboBox()
        for preset in list_presets():
            self.preset_combo.addItem(preset.label, preset.id)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText(C.t("settings.api_key_placeholder"))

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText(C.t("settings.base_url_placeholder"))

        self.model_label = QLabel()
        self.model_edit = QLineEdit()

        form.addRow(C.t("settings.provider"), self.preset_combo)
        form.addRow("API Key", self.api_key_edit)
        form.addRow("API Base URL", self.base_url_edit)
        form.addRow(self.model_label, self.model_edit)
        layout.addLayout(form)

        self.preset_hint = QLabel()
        self.preset_hint.setWordWrap(True)
        self.preset_hint.setObjectName("settingsPresetHint")
        layout.addWidget(self.preset_hint)

        hint = QLabel(C.t("settings.privacy"))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.test_btn = QPushButton(C.t("settings.test_connection"))
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_from_config(self) -> None:
        preset_id = self._cfg.resolved_provider_preset()
        idx = self.preset_combo.findData(preset_id)
        self._applying_preset = True
        self.preset_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._applying_preset = False

        self.api_key_edit.setText(self._cfg.api_key)
        self.base_url_edit.setText(self._cfg.base_url or self._current_preset().default_base_url)
        self.model_edit.setText(self._cfg.model)
        self._apply_preset_ui(self._current_preset(), fill_url=False)

    def _current_preset(self):
        preset_id = self.preset_combo.currentData()
        return get_preset(str(preset_id)) or PRESET_CUSTOM

    def _on_preset_changed(self) -> None:
        if self._applying_preset:
            return
        self._apply_preset_ui(self._current_preset(), fill_url=True)

    def _apply_preset_ui(self, preset, *, fill_url: bool) -> None:
        self.model_label.setText(preset.model_field_label)
        self.model_edit.setPlaceholderText(preset.model_placeholder)
        self.preset_hint.setText(preset.hint)

        if fill_url:
            self.base_url_edit.setText(preset.default_base_url)
        elif not self.base_url_edit.text().strip() and preset.default_base_url:
            self.base_url_edit.setText(preset.default_base_url)

        is_custom = preset.id == PRESET_CUSTOM.id
        self.base_url_edit.setReadOnly(not is_custom and bool(preset.default_base_url))
        if not is_custom and preset.default_base_url:
            self.base_url_edit.setToolTip("由服务商预设自动填充；如需修改请选择「自定义」。")
        else:
            self.base_url_edit.setToolTip("")

    def _collect(self) -> AiConfig:
        preset_id = str(self.preset_combo.currentData() or "openai")
        preset = get_preset(preset_id)
        base_url = self.base_url_edit.text().strip()
        if preset and preset.id != PRESET_CUSTOM.id and base_url == preset.default_base_url:
            # 与预设一致时可留空，由 resolved_base_url 解析
            base_url = ""

        return AiConfig(
            provider="openai_compatible",
            provider_preset=preset_id,
            api_key=self.api_key_edit.text().strip(),
            base_url=base_url,
            model=self.model_edit.text().strip(),
            language=self._cfg.language,
            prompt_file=self._cfg.prompt_file,
            lut_min_confidence=self._cfg.lut_min_confidence,
            xmp_min_confidence=self._cfg.xmp_min_confidence,
            use_json_mode=self._cfg.use_json_mode,
            max_retries=self._cfg.max_retries,
        )

    def _save(self) -> None:
        cfg = self._collect()
        if cfg.resolved_provider_preset() == PRESET_CUSTOM.id and not cfg.base_url.strip():
            QMessageBox.warning(self, C.t("settings.title"), C.t("settings.error_custom_url"))
            return
        save_ai_config(cfg)
        self._cfg = cfg
        self.accept()

    def _test_connection(self) -> None:
        cfg = self._collect()
        if not cfg.is_ready():
            QMessageBox.warning(self, C.t("settings.test_connection"), C.t("settings.error_missing_fields"))
            return
        if cfg.resolved_provider_preset() == PRESET_CUSTOM.id and not cfg.resolved_base_url():
            QMessageBox.warning(self, C.t("settings.test_connection"), C.t("settings.error_custom_url"))
            return
        try:
            msg = create_analyzer(cfg).test_connection()
            QMessageBox.information(self, C.t("settings.test_connection"), msg)
        except Exception as exc:
            extra = ""
            if cfg.resolved_provider_preset() == "volcengine":
                extra = "\n\n" + C.t("settings.volcengine_test_hint")
            QMessageBox.critical(self, C.t("settings.test_connection_failed"), f"{exc}{extra}")
