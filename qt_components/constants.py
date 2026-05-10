EQ_BAND_ORDER = ["63", "160", "400", "1000", "2500", "6300", "10000", "16000", "20000"]
EQ_BAND_DISPLAY = {
    "63": "63",
    "160": "160",
    "400": "400",
    "1000": "1k",
    "2500": "2.5k",
    "6300": "6.3k",
    "10000": "10k",
    "16000": "16k",
    "20000": "20k",
}

THEME_TANGO = """
QMainWindow { background: #14110f; }
QWidget { color: #f7efe7; font-family: "Avenir Next", "Helvetica Neue", sans-serif; font-size: 12px; }
QMenuBar { background: #14110f; color: #e9d6c2; border: none; padding: 6px 10px; }
QMenuBar::item { background: transparent; padding: 6px 10px; border-radius: 8px; }
QMenuBar::item:selected { background: #2c241f; }
QMenu { background: #201a17; color: #f7efe7; border: 1px solid #43342b; padding: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 6px; }
QMenu::item:selected { background: #8f4f2a; }
QPushButton { background: #2c241f; color: #f7efe7; border: 1px solid #342a25; border-radius: 6px; padding: 4px 8px; font-weight: 600; }
QPushButton:hover { background: #3a2d26; border-color: #6e4b39; }
QPushButton:pressed { background: #8f4f2a; border-color: #b9713d; }
QPushButton:disabled { background: #1a1614; color: #78675c; border-color: #2d2520; }
QFrame#card { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #241d1a, stop:1 #1a1614); border: 1px solid #2b231f; border-radius: 10px; }
QLabel#sectionTitle { color: #fff4eb; font-size: 13px; font-weight: 700; }
QLabel#sectionMeta { color: #c4a896; font-size: 10px; }
QLabel#valuePill { background: #201916; border: 1px solid #3a2e29; border-radius: 7px; padding: 2px 6px; color: #f1cfbb; font-weight: 600; }
QLabel#statusLive { color: #ffd9c2; font-weight: 600; }
QLabel#statusIdle { color: #bca390; }
QLabel#waveform { background: #151210; border: 1px solid #2e2622; border-radius: 4px; }
QProgressBar { background: #1f1916; border: 1px solid #362c27; border-radius: 5px; min-height: 10px; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b45a33, stop:1 #d59a54); border-radius: 5px; }
QTreeWidget { background: #171311; alternate-background-color: #1c1714; border: 1px solid #312823; border-radius: 8px; padding: 0px; outline: none; }
QHeaderView::section { background: transparent; color: #d3b09a; border: none; padding: 4px 4px 6px 4px; font-size: 11px; font-weight: 700; }
QTreeWidget::item { border-radius: 6px; padding: 0px; }
QTreeWidget::item:selected { background: #8f4f2a; color: #fff7f1; }
QTreeWidget::item:hover { background: #2d2420; }
QTreeView::drop-indicator { background-color: #ff6b35; height: 2px; }
QComboBox { background: #1c1715; border: 1px solid #3a2f29; border-radius: 6px; padding: 3px 6px; min-width: 120px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #201a17; border: 1px solid #43342b; selection-background-color: #8f4f2a; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 9px; border: 1px solid #85604b; background: #1a1512; }
QCheckBox::indicator:checked { background: #d57d49; border-color: #f0b07c; }
QSlider::groove:vertical { background: #1e1815; width: 8px; border-radius: 4px; }
QSlider::sub-page:vertical { background: #cf8652; border-radius: 4px; }
QSlider::handle:vertical { background: #fff2e9; border: 1px solid #d59a54; height: 14px; margin: -4px -6px; border-radius: 7px; }
QSlider::groove:horizontal { background: #1e1815; height: 8px; border-radius: 4px; }
QSlider::sub-page:horizontal { background: #cf8652; border-radius: 4px; }
QSlider::handle:horizontal { background: #fff2e9; border: 1px solid #d59a54; width: 14px; margin: -6px -4px; border-radius: 7px; }
QScrollArea { background: transparent; border: none; }
QScrollBar:horizontal { background: #1d1815; height: 10px; border-radius: 5px; }
QScrollBar::handle:horizontal { background: #6a4a38; border-radius: 5px; min-width: 24px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

THEME_LIGHT = """
QMainWindow { background: #f3f3f3; }
QWidget { color: #111111; font-family: "Avenir Next", "Helvetica Neue", sans-serif; font-size: 12px; }
QMenuBar { background: #f3f3f3; color: #111111; border: none; padding: 6px 10px; }
QMenuBar::item { background: transparent; padding: 6px 10px; border-radius: 8px; }
QMenuBar::item:selected { background: #e0e0e0; }
QMenu { background: #ffffff; color: #111111; border: 1px solid #cccccc; padding: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 6px; }
QMenu::item:selected { background: #0078d7; color: #ffffff; }
QPushButton { background: #ffffff; color: #111111; border: 1px solid #c0c0c0; border-radius: 6px; padding: 4px 8px; font-weight: 600; }
QPushButton:hover { background: #f0f0f0; border-color: #0078d7; }
QPushButton:pressed { background: #e0e0e0; border-color: #005499; }
QPushButton:disabled { background: #e5e5e5; color: #a0a0a0; border-color: #d0d0d0; }
QFrame#card { background: #ffffff; border: 1px solid #d5d5d5; border-radius: 10px; }
QLabel#sectionTitle { color: #111111; font-size: 13px; font-weight: 700; }
QLabel#sectionMeta { color: #666666; font-size: 10px; }
QLabel#valuePill { background: #f0f0f0; border: 1px solid #d0d0d0; border-radius: 7px; padding: 2px 6px; color: #333333; font-weight: 600; }
QLabel#statusLive { color: #0078d7; font-weight: 600; }
QLabel#statusIdle { color: #666666; }
QLabel#waveform { background: #ffffff; border: 1px solid #cccccc; border-radius: 4px; }
QProgressBar { background: #e0e0e0; border: 1px solid #cccccc; border-radius: 5px; min-height: 10px; }
QProgressBar::chunk { background: #0078d7; border-radius: 5px; }
QTreeWidget { background: #ffffff; alternate-background-color: #f9f9f9; border: 1px solid #cccccc; border-radius: 8px; padding: 0px; outline: none; }
QHeaderView::section { background: transparent; color: #333333; border: none; border-bottom: 1px solid #d0d0d0; padding: 4px 4px 6px 4px; font-size: 11px; font-weight: 700; }
QTreeWidget::item { border-radius: 6px; padding: 0px; }
QTreeWidget::item:selected { background: #0078d7; color: #ffffff; }
QTreeWidget::item:hover { background: #f0f0f0; color: #000000; }
QTreeView::drop-indicator { background-color: #0078d7; height: 2px; }
QComboBox { background: #ffffff; border: 1px solid #cccccc; border-radius: 6px; padding: 3px 6px; min-width: 120px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #ffffff; border: 1px solid #cccccc; selection-background-color: #0078d7; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 9px; border: 1px solid #aaaaaa; background: #ffffff; }
QCheckBox::indicator:checked { background: #0078d7; border-color: #005499; }
QSlider::groove:vertical { background: #e0e0e0; width: 8px; border-radius: 4px; }
QSlider::sub-page:vertical { background: #0078d7; border-radius: 4px; }
QSlider::handle:vertical { background: #ffffff; border: 1px solid #005499; height: 14px; margin: -4px -6px; border-radius: 7px; }
QSlider::groove:horizontal { background: #e0e0e0; height: 8px; border-radius: 4px; }
QSlider::sub-page:horizontal { background: #0078d7; border-radius: 4px; }
QSlider::handle:horizontal { background: #ffffff; border: 1px solid #005499; width: 14px; margin: -6px -4px; border-radius: 7px; }
QScrollArea { background: transparent; border: none; }
QScrollBar:horizontal { background: #e0e0e0; height: 10px; border-radius: 5px; }
QScrollBar::handle:horizontal { background: #a0a0a0; border-radius: 5px; min-width: 24px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

THEME_DARK = """
QMainWindow { background: #1e1e1e; }
QWidget { color: #e0e0e0; font-family: "Avenir Next", "Helvetica Neue", sans-serif; font-size: 12px; }
QMenuBar { background: #1e1e1e; color: #e0e0e0; border: none; padding: 6px 10px; }
QMenuBar::item { background: transparent; padding: 6px 10px; border-radius: 8px; }
QMenuBar::item:selected { background: #333333; }
QMenu { background: #252526; color: #e0e0e0; border: 1px solid #454545; padding: 6px; }
QMenu::item { padding: 8px 20px; border-radius: 6px; }
QMenu::item:selected { background: #094771; }
QPushButton { background: #333333; color: #e0e0e0; border: 1px solid #454545; border-radius: 6px; padding: 4px 8px; font-weight: 600; }
QPushButton:hover { background: #3e3e42; border-color: #007fd4; }
QPushButton:pressed { background: #094771; border-color: #005a9e; }
QPushButton:disabled { background: #252526; color: #707070; border-color: #333333; }
QFrame#card { background: #252526; border: 1px solid #333333; border-radius: 10px; }
QLabel#sectionTitle { color: #ffffff; font-size: 13px; font-weight: 700; }
QLabel#sectionMeta { color: #aaaaaa; font-size: 10px; }
QLabel#valuePill { background: #333333; border: 1px solid #454545; border-radius: 7px; padding: 2px 6px; color: #cccccc; font-weight: 600; }
QLabel#statusLive { color: #4fc1ff; font-weight: 600; }
QLabel#statusIdle { color: #aaaaaa; }
QLabel#waveform { background: #1e1e1e; border: 1px solid #333333; border-radius: 4px; }
QProgressBar { background: #333333; border: 1px solid #454545; border-radius: 5px; min-height: 10px; }
QProgressBar::chunk { background: #007fd4; border-radius: 5px; }
QTreeWidget { background: #1e1e1e; alternate-background-color: #252526; border: 1px solid #333333; border-radius: 8px; padding: 0px; outline: none; }
QHeaderView::section { background: transparent; color: #aaaaaa; border: none; border-bottom: 1px solid #454545; padding: 4px 4px 6px 4px; font-size: 11px; font-weight: 700; }
QTreeWidget::item { border-radius: 6px; padding: 0px; }
QTreeWidget::item:selected { background: #094771; color: #ffffff; }
QTreeWidget::item:hover { background: #2a2d2e; }
QTreeView::drop-indicator { background-color: #007fd4; height: 2px; }
QComboBox { background: #252526; border: 1px solid #454545; border-radius: 6px; padding: 3px 6px; min-width: 120px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #252526; border: 1px solid #454545; selection-background-color: #094771; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 9px; border: 1px solid #555555; background: #1e1e1e; }
QCheckBox::indicator:checked { background: #007fd4; border-color: #007fd4; }
QSlider::groove:vertical { background: #333333; width: 8px; border-radius: 4px; }
QSlider::sub-page:vertical { background: #094771; border-radius: 4px; }
QSlider::handle:vertical { background: #cccccc; border: 1px solid #007fd4; height: 14px; margin: -4px -6px; border-radius: 7px; }
QSlider::groove:horizontal { background: #333333; height: 8px; border-radius: 4px; }
QSlider::sub-page:horizontal { background: #094771; border-radius: 4px; }
QSlider::handle:horizontal { background: #cccccc; border: 1px solid #007fd4; width: 14px; margin: -6px -4px; border-radius: 7px; }
QScrollArea { background: transparent; border: none; }
QScrollBar:horizontal { background: #333333; height: 10px; border-radius: 5px; }
QScrollBar::handle:horizontal { background: #555555; border-radius: 5px; min-width: 24px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""

THEMES = {
    "Light": THEME_LIGHT,
    "Dark": THEME_DARK,
    "Tango": THEME_TANGO
}

