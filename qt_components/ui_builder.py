from pathlib import Path

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QSlider, QProgressBar, QCheckBox, QComboBox, QFrame, QScrollArea

from qt_components.constants import EQ_BAND_ORDER
from qt_components.playlist import PlaylistTree


UI_DIR = Path(__file__).resolve().parent / "ui"


class UiLoader(QUiLoader):
    def __init__(self, base_instance=None):
        super().__init__(base_instance)
        self.base_instance = base_instance

    def createWidget(self, class_name, parent=None, name=""):
        if class_name == "PlaylistTree":
            widget = PlaylistTree(parent)
            widget.setObjectName(name)
            return widget
        return super().createWidget(class_name, parent, name)


def load_ui(ui_path, parent=None):
    loader = UiLoader(parent)
    ui_file = QFile(str(ui_path))
    if not ui_file.open(QIODevice.ReadOnly):
        raise FileNotFoundError(f"Cannot open UI file: {ui_path}")
    try:
        return loader.load(ui_file, parent)
    finally:
        ui_file.close()


def _get(window, cls, name):
    widget = window.findChild(cls, name)
    if widget is None:
        raise RuntimeError(f"Missing widget '{name}' in UI")
    return widget


def build_ui(main_window: QMainWindow):
    central_widget = load_ui(UI_DIR / "main_window.ui", main_window)
    main_window.setCentralWidget(central_widget)

    main_window.btn_play = _get(main_window, QPushButton, "btn_play")
    main_window.btn_stop = _get(main_window, QPushButton, "btn_stop")
    main_window.btn_pause = _get(main_window, QPushButton, "btn_pause")
    main_window.btn_next = _get(main_window, QPushButton, "btn_next")
    main_window.btn_delete = _get(main_window, QPushButton, "btn_delete")
    main_window.volume_slider = _get(main_window, QSlider, "volume_slider")
    main_window.volume_value_label = _get(main_window, QLabel, "volume_value_label")
    main_window.waveform_label = _get(main_window, QLabel, "waveform_label")
    main_window.progress_bar = _get(main_window, QProgressBar, "progress_bar")
    main_window.playlist_tree = _get(main_window, PlaylistTree, "playlist_tree")
    main_window.status_label = _get(main_window, QLabel, "status_label")
    main_window.eq_toggle_button = _get(main_window, QPushButton, "eq_toggle_button")
    main_window.settings_button = _get(main_window, QPushButton, "settings_button")
    main_window.eq_frame = _get(main_window, QFrame, "eq_frame")
    main_window.genre_combo = _get(main_window, QComboBox, "genre_combo")
    main_window.eq_enabled = _get(main_window, QCheckBox, "eq_enabled")
    main_window.eq_scroll = _get(main_window, QScrollArea, "eq_scroll")
    main_window.flat_button = _get(main_window, QPushButton, "flat_button")

    main_window.central_layout = central_widget.layout()
    main_window.controls_row = _get(main_window, QFrame, "toolbar_bottom_widget")
    main_window.waveform_label.setObjectName("waveform")
    main_window.status_label.setObjectName("statusIdle")

    volume = int(main_window.state.settings.get("volume", 80))
    main_window.volume_slider.setValue(volume)
    main_window.volume_value_label.setText(f"{volume}%")

    main_window.playlist_tree.setColumnCount(2)
    main_window.playlist_tree.setHeaderLabels(main_window.state.settings["main_grid"]["headers"])
    main_window.playlist_tree.itemDoubleClicked.connect(main_window.on_item_double_clicked)
    main_window.playlist_tree.filesDropped.connect(main_window.handle_external_drop)
    main_window.playlist_tree.orderChanged.connect(main_window.on_playlist_reordered)

    main_window.volume_slider.valueChanged.connect(main_window.set_volume)
    main_window.eq_toggle_button.clicked.connect(main_window.toggle_eq_panel)
    main_window.settings_button.clicked.connect(main_window.open_settings)
    main_window.flat_button.clicked.connect(main_window.set_eq_flat)

    main_window.genre_combo.addItems(sorted(main_window.eq_presets.keys()))
    main_window.genre_combo.currentTextChanged.connect(main_window.on_genre_changed)
    main_window.eq_enabled.stateChanged.connect(main_window.on_eq_controls_changed)

    main_window.eq_sliders = {}
    main_window.eq_value_labels = {}
    for band in EQ_BAND_ORDER:
        slider = _get(main_window, QSlider, f"slider_{band}")
        value_label = _get(main_window, QLabel, f"value_{band}")
        main_window.eq_sliders[band] = slider
        main_window.eq_value_labels[band] = value_label
        value_label.setObjectName("valuePill")
        slider.parentWidget().setObjectName("card")
        label = _get(main_window, QLabel, f"label_{band}")
        label.setObjectName("sectionMeta")
        slider.valueChanged.connect(main_window.on_eq_controls_changed)

    for button_name, icon_path in (
        ("btn_play", "icons/play.png"),
        ("btn_stop", "icons/stop.png"),
        ("btn_pause", "icons/pause.png"),
        ("btn_next", "icons/next.png"),
        ("btn_delete", "icons/delete.png"),
    ):
        button = getattr(main_window, button_name)
        if Path(icon_path).exists():
            button.setIcon(QIcon(icon_path))

    main_window.btn_play.clicked.connect(main_window.on_play)
    main_window.btn_stop.clicked.connect(main_window.on_stop)
    main_window.btn_pause.clicked.connect(main_window.on_pause)
    main_window.btn_next.clicked.connect(main_window.on_next)
    main_window.btn_delete.clicked.connect(main_window.on_delete)

    if Path("icons/icon.png").exists():
        main_window.setWindowIcon(QIcon("icons/icon.png"))
