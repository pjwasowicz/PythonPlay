from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QComboBox, QCheckBox, QHBoxLayout, QPushButton

class AudioSettingsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None, devices=None, supports_hog_mode=False, available_themes=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = current_settings or {}
        self.devices = list(devices or [])
        self.supports_hog_mode = supports_hog_mode
        self.available_themes = available_themes or ["Light"]
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        grid = QGridLayout()

        grid.addWidget(QLabel("Color Theme"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.available_themes)
        current_theme = self.settings.get("color_theme", "Light")
        if current_theme in self.available_themes:
            self.theme_combo.setCurrentText(current_theme)
        grid.addWidget(self.theme_combo, 0, 1)

        grid.addWidget(QLabel("Output device"), 1, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(self.devices if self.devices else [""])
        current_device = self.settings.get("audio_device", "")
        if current_device in self.devices:
            self.device_combo.setCurrentText(current_device)
        grid.addWidget(self.device_combo, 1, 1)

        self.hog_check = QCheckBox("Enable hog mode")
        self.hog_check.setChecked(bool(self.settings.get("hog_mode", False)))
        self.hog_check.setEnabled(self.supports_hog_mode)
        grid.addWidget(self.hog_check, 2, 0, 1, 2)

        layout.addLayout(grid)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        buttons.addWidget(save_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        buttons.addWidget(close_button)

        layout.addLayout(buttons)

    def get_settings(self):
        return {
            "color_theme": self.theme_combo.currentText().strip(),
            "audio_device": self.device_combo.currentText().strip(),
            "hog_mode": self.hog_check.isChecked(),
        }
