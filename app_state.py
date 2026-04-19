from dataclasses import dataclass, field
from typing import Any


@dataclass
class UIRefs:
    root: Any = None
    tree: Any = None
    slider: Any = None
    progressbar: Any = None
    status_bar: Any = None
    start_button: Any = None
    stop_button: Any = None
    delete_button: Any = None
    pause_button: Any = None
    next_button: Any = None
    audio_device_dropdown: Any = None


@dataclass
class AppState:
    settings: dict = field(default_factory=dict)
    songs: dict = field(default_factory=dict)
    last_highlighted: Any = None
    is_dragging: bool = False
    last_y: Any = None
    current_song: Any = None
    is_playing: bool = False
    is_paused: bool = False
    current_position: int = 0
    waiting_time: int = 0
    is_converting: bool = False
