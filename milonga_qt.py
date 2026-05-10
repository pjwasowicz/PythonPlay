import os
import platform
import re
import sys
import uuid
from copy import deepcopy

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QGuiApplication, QPixmap, QShowEvent, QColor, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QTreeWidgetItem
)

import config
import global_vars
import lists
import player
from app_state import AppState
from runtime_setup import setup_application_environment

from qt_components.constants import EQ_BAND_ORDER, THEMES
from qt_components.waveform import WaveCanvasAdapter
from qt_components.audio_settings import AudioSettingsDialog
from qt_components.ui_builder import build_ui

try:
    import macos_audio
except Exception:
    macos_audio = None


class MilongaQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.platform_system = platform.system()
        self.state = AppState(settings=config.load_settings())
        self.eq_presets = deepcopy(self.state.settings.get("genre_equalizer", {}))
        self.current_eq_genre = "default"
        self.suppress_eq_updates = False
        self.hog_mode_device_name = None

        self.eq_enabled = None
        self.genre_combo = None
        self.eq_sliders = {}
        self.eq_value_labels = {}
        self.playlist_tree = None
        self.waveform_label = None
        self.eq_scroll = None
        self.eq_toggle_button = None
        self.eq_expanded = False
        self.progress_bar = None
        self.status_label = None
        self.volume_value_label = None
        self.settings_button = None
        self.volume_slider = None
        self.btn_play = None
        self.btn_stop = None
        self.btn_pause = None
        self.btn_next = None
        self.btn_delete = None
        self.central_layout = None
        self.controls_row = None
        self.eq_frame = None

        self.setWindowTitle("Milonga")
        self.setMinimumSize(400, 480)
        self._ensure_eq_presets()
        self.apply_theme(self.state.settings.get("color_theme", "Light"))

        player.load_converted_files()
        player.init_player()
        
        build_ui(self)
        self._build_menu()
        self.load_playlist()
        self.ensure_audio_settings()

        selected_device = self.state.settings.get("audio_device", "")
        if selected_device:
            self.set_audio_device(selected_device)
        player.set_volume(self.state.settings.get("volume", 80) / 100.0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui_state)
        self.timer.start(100)

        self.update_transport_buttons()
        self.load_eq_preset_into_ui(self.current_eq_genre)
        self._fit_to_available_screen(initial=True)
        global_vars.wave_canvas = WaveCanvasAdapter(self.waveform_label)
        self.apply_responsive_layout()

    def apply_theme(self, theme_name):
        if theme_name not in THEMES:
            theme_name = "Light"
        self.setStyleSheet(THEMES[theme_name])
        # Update colors on existing items if tree exists
        if self.playlist_tree is not None:
            for i in range(self.playlist_tree.topLevelItemCount()):
                item = self.playlist_tree.topLevelItem(i)
                song_id = item.data(0, Qt.UserRole)
                tags = self.state.songs.get(song_id, ({}, {}))[1]
                self._apply_genre_colors(item, tags)


    def _build_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        export_action = QAction("Export playlist", self)
        export_action.triggered.connect(self.export_playlist)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = menu_bar.addMenu("Help")
        about_action = QAction("About Milonga", self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

    def apply_responsive_layout(self):
        height = self.height()
        compact_height = height < 700
        very_compact_height = height < 550

        if very_compact_height:
            waveform_height = 0
            controls_height = 28
        elif compact_height:
            waveform_height = 30
            controls_height = 32
        else:
            waveform_height = 50
            controls_height = 32

        self.waveform_label.setVisible(waveform_height > 0)
        if waveform_height > 0:
            self.waveform_label.setMinimumHeight(waveform_height)
            self.waveform_label.setMaximumHeight(waveform_height)

        for btn in [self.btn_play, self.btn_stop, self.btn_pause, self.btn_next, self.btn_delete]:
            btn.setMinimumHeight(controls_height)
            btn.setMaximumHeight(controls_height)

    def _fit_to_available_screen(self, initial=False):
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        margin = 20
        max_width = available.width() - margin * 2
        max_height = available.height() - margin * 2

        target_width = 430
        target_height = 800

        target_width = min(target_width, max_width)
        target_height = min(target_height, max_height)

        if initial:
            self.resize(target_width, target_height)
            frame = self.frameGeometry()
            frame.moveCenter(available.center())
            self.move(frame.topLeft())

    def toggle_eq_panel(self):
        self.eq_expanded = not self.eq_expanded
        if self.eq_expanded:
            self.eq_frame.show()
        else:
            self.eq_frame.hide()
            
        if self.eq_toggle_button is not None:
            self.eq_toggle_button.setText("Hide" if self.eq_expanded else "EQ")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_responsive_layout()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._fit_to_available_screen()

    def _ensure_eq_presets(self):
        if "default" not in self.eq_presets:
            self.eq_presets["default"] = {"enabled": False, "bands": {}}
        for genre_name, preset in self.eq_presets.items():
            preset.setdefault("enabled", False)
            preset.setdefault("bands", {})
            for band in EQ_BAND_ORDER:
                preset["bands"].setdefault(band, 0)

    def ensure_audio_settings(self):
        available_devices = list(player.get_devices())
        configured_device = self.state.settings.get("audio_device", "")
        if configured_device in available_devices:
            return
        self.state.settings["audio_device"] = available_devices[0] if available_devices else ""
        config.save_settings(self.state.settings)

    def supports_hog_mode(self):
        return self.platform_system == "Darwin" and macos_audio is not None

    def is_hog_mode_enabled(self):
        return bool(self.state.settings.get("hog_mode", False))

    def release_hog_mode_if_needed(self):
        if not self.supports_hog_mode() or not self.hog_mode_device_name:
            return
        try:
            macos_audio.release_hog_mode(device_name=self.hog_mode_device_name)
        except Exception as error:
            print("Cannot release hog mode:", error)
        finally:
            self.hog_mode_device_name = None

    def apply_hog_mode(self, device_name):
        if not self.supports_hog_mode():
            return
        self.release_hog_mode_if_needed()
        if not self.is_hog_mode_enabled() or not device_name:
            return
        try:
            owner_pid = macos_audio.acquire_hog_mode(device_name=device_name)
            self.hog_mode_device_name = device_name
            print("Hog mode enabled:", device_name, "PID:", owner_pid)
        except Exception as e:
            print("Hog mode error:", e)

    def format_tree_values(self, tags):
        values = []
        for column in self.state.settings["main_grid"]["fields"]:
            keys = re.findall(r"\{(.*?)\}", column)
            formatted_values = {key: tags.get(key, "") for key in keys}
            values.append(column.format(**formatted_values))
        return values

    def _apply_genre_colors(self, item, tags):
        genre = (tags.get("genre", "") or "").lower()
        color = None
        if "milonga" in genre:
            color = QColor("#A65A18")
        elif "vals" in genre:
            color = QColor("#466B4A")
        elif "cortina" in genre:
            color = QColor("#A61E1E")
        
        if color:
            for i in range(self.playlist_tree.columnCount()):
                item.setForeground(i, QBrush(color))

    def add_song_to_playlist(self, file_path, tags, row=None):
        prepared_file = player.can_load_sound(file_path)
        if not prepared_file:
            return None

        song_id = str(uuid.uuid4())
        self.state.songs[song_id] = (prepared_file, tags)

        item = QTreeWidgetItem(self.format_tree_values(tags))
        item.setData(0, Qt.UserRole, song_id)
        # Disable dropping ON the item to force inserting between items (flat list behavior)
        item.setFlags(item.flags() & ~Qt.ItemIsDropEnabled)
        self._apply_genre_colors(item, tags)

        insert_row = self.playlist_tree.topLevelItemCount() if row is None else max(0, min(row, self.playlist_tree.topLevelItemCount()))
        self.playlist_tree.insertTopLevelItem(insert_row, item)
        return song_id

    def load_playlist(self):
        self.playlist_tree.clear()
        self.state.songs = {}
        songs_tags = lists.get_audio_tags_from_m3u8(config.get_default_playlist_full_file_name())
        if songs_tags:
            for entry in songs_tags:
                for path, tags in entry.items():
                    self.add_song_to_playlist(path, tags)
        self.update_transport_buttons()

    def get_playlist_order(self):
        order = []
        for index in range(self.playlist_tree.topLevelItemCount()):
            item = self.playlist_tree.topLevelItem(index)
            order.append(item.data(0, Qt.UserRole))
        return order

    def save_playlist(self):
        files_to_save = [self.state.songs[song_id] for song_id in self.get_playlist_order() if song_id in self.state.songs]
        lists.save_m3u(files_to_save, config.get_default_playlist_full_file_name())
        player.save_converted_files()

    def update_transport_buttons(self):
        has_rows = self.playlist_tree.topLevelItemCount() > 0
        busy = player.get_busy() or self.state.is_paused or self.state.pending_transport_action is not None
        
        self.btn_play.setEnabled(has_rows and not (player.get_busy() or self.state.is_paused))
        self.btn_stop.setEnabled(busy)
        self.btn_pause.setEnabled(busy)
        self.btn_next.setEnabled(busy and self._current_song_row() < self.playlist_tree.topLevelItemCount() - 1)
        self.btn_delete.setEnabled(has_rows and not player.get_busy())

    def _selected_row(self):
        item = self.playlist_tree.currentItem()
        if item is None:
            return None
        return self.playlist_tree.indexOfTopLevelItem(item)

    def _song_id_at_row(self, row):
        if row is None or row < 0 or row >= self.playlist_tree.topLevelItemCount():
            return None
        return self.playlist_tree.topLevelItem(row).data(0, Qt.UserRole)

    def _current_song_row(self):
        if self.state.current_song is None:
            return -1
        for index in range(self.playlist_tree.topLevelItemCount()):
            item = self.playlist_tree.topLevelItem(index)
            if item.data(0, Qt.UserRole) == self.state.current_song:
                return index
        return -1

    def _select_song(self, song_id):
        for index in range(self.playlist_tree.topLevelItemCount()):
            item = self.playlist_tree.topLevelItem(index)
            if item.data(0, Qt.UserRole) == song_id:
                self.playlist_tree.setCurrentItem(item)
                self.playlist_tree.scrollToItem(item)
                for i in range(self.playlist_tree.topLevelItemCount()):
                    it = self.playlist_tree.topLevelItem(i)
                    it.setBackground(0, Qt.BrushStyle.NoBrush)
                item.setBackground(0, QColor("#8f4f2a"))
                return

    def current_eq_settings(self):
        return {
            "enabled": self.eq_enabled.isChecked(),
            "bands": {band: self.eq_sliders[band].value() for band in EQ_BAND_ORDER},
        }

    def _ensure_genre_preset(self, genre_name):
        normalized = (genre_name or "default").strip().lower() or "default"
        if normalized not in self.eq_presets:
            default_preset = deepcopy(self.eq_presets.get("default", {"enabled": False, "bands": {}}))
            default_preset.setdefault("bands", {})
            for band in EQ_BAND_ORDER:
                default_preset["bands"].setdefault(band, 0)
            self.eq_presets[normalized] = default_preset
            self.genre_combo.blockSignals(True)
            self.genre_combo.clear()
            self.genre_combo.addItems(sorted(self.eq_presets.keys()))
            self.genre_combo.blockSignals(False)
        return normalized

    def load_eq_preset_into_ui(self, genre_name):
        normalized = self._ensure_genre_preset(genre_name)
        preset = self.eq_presets[normalized]
        self.current_eq_genre = normalized
        self.suppress_eq_updates = True
        self.genre_combo.setCurrentText(normalized)
        self.eq_enabled.setChecked(bool(preset.get("enabled", False)))
        for band in EQ_BAND_ORDER:
            value = int(round(float(preset.get("bands", {}).get(band, 0))))
            self.eq_sliders[band].setValue(value)
            self.eq_value_labels[band].setText(f"{value} dB")
        self.suppress_eq_updates = False

    def persist_current_eq_preset(self):
        genre_name = self._ensure_genre_preset(self.current_eq_genre)
        preset = self.eq_presets.setdefault(genre_name, {"enabled": False, "bands": {}})
        preset["enabled"] = self.eq_enabled.isChecked()
        preset.setdefault("bands", {})
        for band in EQ_BAND_ORDER:
            preset["bands"][band] = self.eq_sliders[band].value()
        self.state.settings["genre_equalizer"] = self.eq_presets
        config.save_settings(self.state.settings)

    def sync_eq_genre_with_song(self, song_id):
        tags = self.state.songs.get(song_id, ({}, {}))[1]
        song_genre = (tags.get("genre", "default") or "default").strip().lower()
        self.load_eq_preset_into_ui(song_genre)

    def set_volume(self, value):
        player.set_volume(value / 100.0)
        self.state.settings["volume"] = value
        if self.volume_value_label is not None:
            self.volume_value_label.setText(f"{int(value)}%")
        config.save_settings(self.state.settings)

    def play_row(self, row):
        song_id = self._song_id_at_row(row)
        if song_id is None:
            return

        self.state.pending_transport_action = None
        self.state.waiting_time = 0
        self.state.current_song = song_id
        self.sync_eq_genre_with_song(song_id)
        
        tags = self.state.songs[song_id][1]
        comment = tags.get("comment", "")
        high_frequency = player.extract_h_value(comment)

        player.play_from_file(
            self.state.songs[song_id][0],
            pos=0,
            normalize_volume=True,
            low_frequency=10,
            high_frequency=high_frequency,
            eq_settings=self.current_eq_settings(),
            song_id=song_id,
            files=self.state.songs,
        )

        self.state.is_playing = True
        self.state.is_paused = False
        self._select_song(song_id)
        self.update_transport_buttons()

    def on_play(self):
        row = self._selected_row()
        if row is None:
            row = 0 if self.playlist_tree.topLevelItemCount() else None
        if row is not None:
            self.play_row(row)

    def on_item_double_clicked(self, item, column):
        del column
        row = self.playlist_tree.indexOfTopLevelItem(item)
        self.play_row(row)

    def on_stop(self):
        if not (player.get_busy() or self.state.is_paused):
            return
        if self.state.pending_transport_action is not None:
            return
        self.state.pending_transport_action = "stop"
        player.fade_to("stop", 120)

    def on_pause(self):
        if self.state.is_paused:
            player.unpause()
            self.state.is_paused = False
            self.state.is_playing = True
            return

        if not player.get_busy() or self.state.pending_transport_action is not None:
            return
        self.state.pending_transport_action = "pause"
        player.fade_to("pause", config.fade_time)

    def on_next(self):
        if not self.state.is_playing or self.state.pending_transport_action is not None:
            return
        self.state.pending_transport_action = "next"
        player.fade_to("stop", config.fade_time)

    def on_delete(self):
        selected_items = self.playlist_tree.selectedItems()
        if not selected_items:
            return

        if player.get_busy():
             return

        removed_current_song = False
        for item in selected_items:
            song_id = item.data(0, Qt.UserRole)
            if song_id == self.state.current_song:
                removed_current_song = True
            self.state.songs.pop(song_id, None)
            index = self.playlist_tree.indexOfTopLevelItem(item)
            self.playlist_tree.takeTopLevelItem(index)

        if removed_current_song:
            player.stop()
            self.state.current_song = None
            self.state.is_playing = False
            self.state.is_paused = False

        self.save_playlist()
        self.update_transport_buttons()

    def on_playlist_reordered(self):
        self.save_playlist()
        self.update_transport_buttons()

    def handle_external_drop(self, file_paths, row):
        insert_row = row
        for path in file_paths:
            tags = lists.get_all_tags(path)
            if tags:
                self.add_song_to_playlist(path, tags, insert_row)
                if insert_row is not None:
                    insert_row += 1
        self.save_playlist()
        self.update_transport_buttons()

    def on_genre_changed(self, genre_name):
        if self.suppress_eq_updates:
            return
        self.persist_current_eq_preset()
        self.load_eq_preset_into_ui(genre_name)
        self._apply_live_eq_if_needed()

    def on_eq_controls_changed(self):
        for band in EQ_BAND_ORDER:
            self.eq_value_labels[band].setText(f"{self.eq_sliders[band].value()} dB")
        if self.suppress_eq_updates:
            return
        self.persist_current_eq_preset()
        self._apply_live_eq_if_needed()

    def _apply_live_eq_if_needed(self):
        if self.state.current_song is None:
            return
        if player.get_busy():
            player.update_live_eq(self.current_eq_settings())

    def set_eq_flat(self):
        self.suppress_eq_updates = True
        for band in EQ_BAND_ORDER:
            self.eq_sliders[band].setValue(0)
            self.eq_value_labels[band].setText("0 dB")
        self.suppress_eq_updates = False
        self.persist_current_eq_preset()
        self._apply_live_eq_if_needed()

    def update_loudness(self):
        self.state.is_converting = True
        try:
            for song_id in list(self.state.songs.keys()):
                if self.state.abort_loudness_scan or player.get_busy() or self.state.is_paused:
                    break
                data = self.state.songs.get(song_id)
                if data is None or len(data) != 2:
                    continue

                file_name = data[0]
                print("Calculating loudness and silence:", file_name)
                try:
                    loudness = player.get_loudness_from_file(file_name)
                    new_data = list(data)
                    new_data.append(loudness)
                    start_cut, end_cut = player.detect_silence_start_end_from_file(file_name, 200, -56)
                    new_data.append(start_cut)
                    new_data.append(end_cut)
                    self.state.songs[song_id] = tuple(new_data)
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")
        finally:
            self.state.is_converting = False
            if not (player.get_busy() or self.state.is_paused):
                self.state.abort_loudness_scan = False

    def update_ui_state(self):
        while not global_vars.wave_queue.empty():
            temp_filename = global_vars.wave_queue.get()
            pixmap = QPixmap(temp_filename)
            if not pixmap.isNull():
                self.waveform_label.setPixmap(
                    pixmap.scaled(
                        self.waveform_label.size(),
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation,
                    )
                )
            try:
                os.remove(temp_filename)
            except OSError:
                pass

        busy = player.get_busy()
        
        # Background loudness processing
        if (
            not self.state.is_converting
            and not busy
            and not self.state.is_paused
            and not self.state.abort_loudness_scan
        ):
            from threading import Thread
            Thread(target=self.update_loudness, daemon=True).start()

        if busy:
            pos = player.get_pos()
            duration = player.get_duration()
            if duration > 0:
                self.progress_bar.setValue(int((pos / duration) * 1000))

            song_id = self.state.current_song
            tags = self.state.songs.get(song_id, ({}, {}))[1] if song_id else {}
            title = tags.get("title", "Unknown")
            correction = player.get_loudness_corretion_db()
            
            status_text = f"{title} [{pos // 60000}:{(pos // 1000) % 60:02}] of [{duration // 60000}:{(duration // 1000) % 60:02}] [{correction:.1f} dB]"
            self.status_label.setText(status_text)
            self.status_label.setObjectName("statusLive")
        
        elif self.state.is_paused:
             self.status_label.setText("Paused")
             self.status_label.setObjectName("statusLive")
        
        else:
            self.progress_bar.setValue(0)
            self.status_label.setText("Idle")
            self.status_label.setObjectName("statusIdle")

        # Transport State Machine logic similar to MilongaApp.check_music
        if not busy and self.state.pending_transport_action == "pause":
            self.state.pending_transport_action = None
            self.state.is_paused = True
            self.state.is_playing = False

        if not busy and self.state.pending_transport_action == "stop":
            self.state.pending_transport_action = None
            self.state.is_playing = False
            self.state.is_paused = False
            self.waveform_label.clear()

        if not busy and self.state.pending_transport_action == "next":
            self.state.pending_transport_action = None
            current_row = self._current_song_row()
            if current_row >= 0 and current_row < self.playlist_tree.topLevelItemCount() - 1:
                self.play_row(current_row + 1)
            else:
                self.state.is_playing = False
                self.state.current_song = None

        if not (busy or self.state.is_paused) and self.state.is_playing and self.state.pending_transport_action is None:
            self.state.waiting_time += 100 # timer interval
            if self.state.waiting_time >= config.pause_time:
                self.state.waiting_time = 0
                current_row = self._current_song_row()
                if current_row >= 0 and current_row < self.playlist_tree.topLevelItemCount() - 1:
                    self.play_row(current_row + 1)
                else:
                    self.state.is_playing = False
                    self.state.current_song = None

        # Force stylesheet update for status label
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        self.update_transport_buttons()

    def open_settings(self):
        dialog = AudioSettingsDialog(
            self,
            current_settings=self.state.settings,
            devices=player.get_devices(),
            supports_hog_mode=self.supports_hog_mode(),
            available_themes=list(THEMES.keys())
        )
        if dialog.exec():
            new_settings = dialog.get_settings()
            previous_device = self.state.settings.get("audio_device", "")
            previous_hog_mode = self.state.settings.get("hog_mode", False)
            try:
                self.state.settings["audio_device"] = new_settings["audio_device"]
                self.state.settings["hog_mode"] = new_settings["hog_mode"]
                self.state.settings["color_theme"] = new_settings["color_theme"]
                config.save_settings(self.state.settings)
                
                self.apply_theme(new_settings["color_theme"])
                self.set_audio_device(new_settings["audio_device"])
            except Exception as error:
                self.state.settings["audio_device"] = previous_device
                self.state.settings["hog_mode"] = previous_hog_mode
                config.save_settings(self.state.settings)
                QMessageBox.critical(self, "Settings", f"Cannot save settings.\n{error}")

    def set_audio_device(self, selected_device):
        player.stop()
        self.state.is_playing = False
        self.state.is_paused = False
        self.release_hog_mode_if_needed()

        if selected_device:
            player.set_device(selected_device)
            self.apply_hog_mode(selected_device)

        player.set_volume(self.state.settings.get("volume", 80) / 100.0)

    def export_playlist(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export to m3u file", "", "Playlist (*.m3u)")
        if not file_path:
            return
        files_to_save = [self.state.songs[song_id] for song_id in self.get_playlist_order() if song_id in self.state.songs]
        lists.save_m3u(files_to_save, file_path, save_external=True)

    def about(self):
        QMessageBox.information(self, "About Milonga", f"Milonga DJ Soft\nVersion: {config.get_version()}")

    def closeEvent(self, event: QCloseEvent):
        if player.get_busy():
            reply = QMessageBox.question(
                self,
                "Close Milonga",
                "Playback is active. Stop playback and close the application?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return

        self.timer.stop()
        self.release_hog_mode_if_needed()
        player.stop()
        player.quit_device()
        player.delete_tmp_files()
        event.accept()

def main():
    setup_application_environment()
    app = QApplication(sys.argv)
    window = MilongaQt()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
