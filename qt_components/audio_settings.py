from PySide6.QtWidgets import QCheckBox, QComboBox, QPushButton

from qt_components.ui_builder import UI_DIR, load_ui


def _get(dialog, cls, name):
    widget = dialog.findChild(cls, name)
    if widget is None:
        raise RuntimeError(f"Missing widget '{name}' in UI")
    return widget


class AudioSettingsDialog:
    def __new__(cls, parent=None, current_settings=None, devices=None, supports_hog_mode=False, available_themes=None):
        dialog = load_ui(UI_DIR / "audio_settings_dialog.ui", parent)
        dialog.setWindowTitle("Settings")
        dialog.theme_combo = _get(dialog, QComboBox, "theme_combo")
        dialog.device_combo = _get(dialog, QComboBox, "device_combo")
        dialog.hog_check = _get(dialog, QCheckBox, "hog_check")
        dialog.save_button = _get(dialog, QPushButton, "save_button")
        dialog.close_button = _get(dialog, QPushButton, "close_button")

        dialog.settings = current_settings or {}
        dialog.devices = list(devices or [])
        dialog.supports_hog_mode = supports_hog_mode
        dialog.available_themes = available_themes or ["Light"]

        dialog.theme_combo.clear()
        dialog.theme_combo.addItems(dialog.available_themes)
        current_theme = dialog.settings.get("color_theme", "Light")
        if current_theme in dialog.available_themes:
            dialog.theme_combo.setCurrentText(current_theme)

        dialog.device_combo.clear()
        dialog.device_combo.addItems(dialog.devices if dialog.devices else [""])
        current_device = dialog.settings.get("audio_device", "")
        if current_device in dialog.devices:
            dialog.device_combo.setCurrentText(current_device)

        dialog.hog_check.setChecked(bool(dialog.settings.get("hog_mode", False)))
        dialog.hog_check.setEnabled(dialog.supports_hog_mode)

        dialog.save_button.clicked.connect(dialog.accept)
        dialog.close_button.clicked.connect(dialog.reject)

        def get_settings():
            return {
                "color_theme": dialog.theme_combo.currentText().strip(),
                "audio_device": dialog.device_combo.currentText().strip(),
                "hog_mode": dialog.hog_check.isChecked(),
            }

        dialog.get_settings = get_settings
        return dialog
