from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QProgressBar,
    QFrame,
    QComboBox,
    QCheckBox,
    QScrollArea
)
import os
from qt_components.playlist import PlaylistTree
from qt_components.constants import EQ_BAND_ORDER, EQ_BAND_DISPLAY

def build_ui(main_window):
    central_widget = QWidget()
    main_window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)
    main_window.central_layout = layout

    # Top toolbar
    toolbar_top_widget = QWidget()
    toolbar_top = QHBoxLayout(toolbar_top_widget)
    toolbar_top.setContentsMargins(0, 0, 0, 0)
    toolbar_top.setSpacing(6)

    main_window.btn_play = QPushButton("Play")
    main_window.btn_stop = QPushButton("Stop")
    main_window.btn_pause = QPushButton("Pause")

    icon_map = {
        main_window.btn_play: "icons/play.png",
        main_window.btn_stop: "icons/stop.png",
        main_window.btn_pause: "icons/pause.png",
    }
    for button, icon_path in icon_map.items():
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        button.setMinimumHeight(32)
        toolbar_top.addWidget(button)
    toolbar_top.addStretch(1)
    layout.addWidget(toolbar_top_widget)

    # Bottom toolbar
    toolbar_bottom_widget = QWidget()
    toolbar_bottom = QHBoxLayout(toolbar_bottom_widget)
    toolbar_bottom.setContentsMargins(0, 0, 0, 0)
    toolbar_bottom.setSpacing(6)

    main_window.btn_next = QPushButton("Next")
    main_window.btn_delete = QPushButton("Delete")
    for button, icon_path in (
        (main_window.btn_next, "icons/next.png"),
        (main_window.btn_delete, "icons/delete.png"),
    ):
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
        button.setMinimumHeight(32)
        toolbar_bottom.addWidget(button)
    toolbar_bottom.addStretch(1)
    layout.addWidget(toolbar_bottom_widget)
    main_window.controls_row = toolbar_bottom_widget

    # Volume & Info
    volume_info_layout = QHBoxLayout()
    main_window.volume_slider = QSlider(Qt.Horizontal)
    main_window.volume_slider.setRange(0, 100)
    main_window.volume_slider.setValue(int(main_window.state.settings.get("volume", 80)))
    main_window.volume_slider.valueChanged.connect(main_window.set_volume)
    volume_info_layout.addWidget(main_window.volume_slider, 1)

    main_window.volume_value_label = QLabel(f"{int(main_window.state.settings.get('volume', 80))}%")
    main_window.volume_value_label.setFixedWidth(40)
    main_window.volume_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    volume_info_layout.addWidget(main_window.volume_value_label)
    layout.addLayout(volume_info_layout)

    # Waveform
    main_window.waveform_label = QLabel("")
    main_window.waveform_label.setAlignment(Qt.AlignCenter)
    main_window.waveform_label.setMinimumHeight(50)
    main_window.waveform_label.setObjectName("waveform")
    layout.addWidget(main_window.waveform_label)

    # Progress
    main_window.progress_bar = QProgressBar()
    main_window.progress_bar.setRange(0, 1000)
    main_window.progress_bar.setTextVisible(False)
    main_window.progress_bar.setFixedHeight(6)
    layout.addWidget(main_window.progress_bar)

    # Playlist
    main_window.playlist_tree = PlaylistTree()
    main_window.playlist_tree.setColumnCount(2)
    main_window.playlist_tree.setHeaderLabels(main_window.state.settings["main_grid"]["headers"])
    main_window.playlist_tree.itemDoubleClicked.connect(main_window.on_item_double_clicked)
    main_window.playlist_tree.filesDropped.connect(main_window.handle_external_drop)
    main_window.playlist_tree.orderChanged.connect(main_window.on_playlist_reordered)
    layout.addWidget(main_window.playlist_tree, 1)

    # Status and bottom buttons
    bottom_panel = QWidget()
    bottom_layout = QHBoxLayout(bottom_panel)
    bottom_layout.setContentsMargins(0, 0, 0, 0)
    bottom_layout.setSpacing(8)

    main_window.status_label = QLabel("Idle")
    main_window.status_label.setObjectName("statusIdle")
    bottom_layout.addWidget(main_window.status_label, 1)

    main_window.eq_toggle_button = QPushButton("EQ")
    main_window.eq_toggle_button.setFixedWidth(50)
    main_window.eq_toggle_button.clicked.connect(main_window.toggle_eq_panel)
    bottom_layout.addWidget(main_window.eq_toggle_button)

    main_window.settings_button = QPushButton("Settings")
    main_window.settings_button.setFixedWidth(80)
    main_window.settings_button.clicked.connect(main_window.open_settings)
    bottom_layout.addWidget(main_window.settings_button)

    layout.addWidget(bottom_panel)

    # EQ Frame
    main_window.eq_frame = QFrame()
    eq_layout = QVBoxLayout(main_window.eq_frame)
    eq_layout.setContentsMargins(8, 8, 8, 8)
    eq_layout.setSpacing(6)

    eq_header = QHBoxLayout()
    eq_title = QLabel("Genre EQ")
    eq_title.setObjectName("sectionTitle")
    eq_header.addWidget(eq_title)

    main_window.genre_combo = QComboBox()
    main_window.genre_combo.addItems(sorted(main_window.eq_presets.keys()))
    main_window.genre_combo.currentTextChanged.connect(main_window.on_genre_changed)
    eq_header.addWidget(main_window.genre_combo)

    main_window.eq_enabled = QCheckBox("Enable")
    main_window.eq_enabled.stateChanged.connect(main_window.on_eq_controls_changed)
    eq_header.addWidget(main_window.eq_enabled)

    eq_header.addStretch(1)

    flat_button = QPushButton("Flat")
    flat_button.clicked.connect(main_window.set_eq_flat)
    eq_header.addWidget(flat_button)

    eq_layout.addLayout(eq_header)

    main_window.eq_scroll = QScrollArea()
    main_window.eq_scroll.setWidgetResizable(True)
    main_window.eq_scroll.setFrameShape(QFrame.NoFrame)
    eq_content = QWidget()
    eq_content_layout = QHBoxLayout(eq_content)
    eq_content_layout.setContentsMargins(4, 4, 4, 4)
    eq_content_layout.setSpacing(6)

    for band in EQ_BAND_ORDER:
        band_card = QFrame()
        band_card.setObjectName("card")
        band_layout = QVBoxLayout()
        band_layout.setSpacing(4)
        band_layout.setContentsMargins(6, 6, 6, 6)
        band_card.setLayout(band_layout)

        label = QLabel(EQ_BAND_DISPLAY[band])
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("sectionMeta")
        band_layout.addWidget(label)

        value_label = QLabel("0 dB")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("valuePill")
        band_layout.addWidget(value_label)
        main_window.eq_value_labels[band] = value_label

        slider = QSlider(Qt.Vertical)
        slider.setRange(-12, 12)
        slider.setValue(0)
        slider.setTickInterval(1)
        slider.valueChanged.connect(main_window.on_eq_controls_changed)
        slider.setMinimumHeight(80)
        band_layout.addWidget(slider)
        main_window.eq_sliders[band] = slider

        eq_content_layout.addWidget(band_card)

    eq_content_layout.addStretch(1)
    main_window.eq_scroll.setWidget(eq_content)
    eq_layout.addWidget(main_window.eq_scroll)

    # Add EQ frame to main layout and hide it initially
    layout.addWidget(main_window.eq_frame)
    main_window.eq_frame.hide()

    main_window.btn_play.clicked.connect(main_window.on_play)
    main_window.btn_stop.clicked.connect(main_window.on_stop)
    main_window.btn_pause.clicked.connect(main_window.on_pause)
    main_window.btn_next.clicked.connect(main_window.on_next)
    main_window.btn_delete.clicked.connect(main_window.on_delete)

    if os.path.exists("icons/icon.png"):
        main_window.setWindowIcon(QIcon("icons/icon.png"))
