import os
import platform
import re
import tempfile
import threading
import tkinter as tk
import uuid
from tkinter import filedialog

import customtkinter
import config
import global_vars
import lists
import player
import utils
from app_state import AppState
from custom_message_box import custom_messagebox_panel
from gui_builder import build_gui

try:
    import macos_audio
except Exception:
    macos_audio = None


class MilongaApp:
    AVAILABLE_COLOR_THEMES = ("blue", "green", "dark-blue", "tango")

    def __init__(self):
        self.dt = 100
        self.line = None
        self.oimage = None
        self.platform_system = platform.system()
        self.state = AppState(settings=config.load_settings())
        self.ui = None
        self.hog_mode_device_name = None

    def run(self):
        player.load_converted_files()
        player.init_player()
        self.ui = build_gui(self)
        self.ui.root.after(self.dt, self.check_music)
        self.state.songs = self.load_default_playlist()
        self.render_playlist()
        self.clear_playing()
        self.ui.progressbar.set(0)
        volume = self.state.settings["volume"]
        self.ui.slider.set(volume)
        normalized_volume = float(volume) / 100
        self.ensure_audio_settings()

        selected_device = self.state.settings.get("audio_device", "")
        if selected_device:
            player.set_device(selected_device)
        player.set_volume(normalized_volume)
        self.apply_hog_mode(selected_device)
        config.save_settings(self.state.settings)

        self.ui.root.mainloop()

    def get_devices(self):
        return player.get_devices()

    def get_color_theme(self):
        theme = self.state.settings.get("color_theme", "blue")
        if theme not in self.AVAILABLE_COLOR_THEMES:
            return "blue"
        if theme == "tango":
            return os.path.join(os.path.dirname(__file__), "themes", "tango.json")
        return theme

    def get_treeview_palette(self):
        theme = self.state.settings.get("color_theme", "blue")
        if theme == "tango":
            return {
                "background": "#E7D5BE",
                "foreground": "#2D1B16",
                "fieldbackground": "#E7D5BE",
                "play_bg": "#F3C969",
                "play_fg": "#5A120E",
                "over_bg": "#C97B63",
                "over_fg": "#FFF7ED",
                "cortina_fg": "#A61E1E",
                "vals_fg": "#466B4A",
                "milonga_fg": "#A65A18",
                "default_bg": "#E7D5BE",
            }
        return None

    def render_playlist(self, order=None, selection=None):
        tree = self.ui.tree
        tree.delete(*tree.get_children())

        if order is None:
            order = list(self.state.songs.keys())

        for iid in order:
            if iid not in self.state.songs:
                continue
            _, file_tags = self.state.songs[iid][:2]
            tree.insert("", "end", iid=iid, values=self.format_tree_values(file_tags))

        if selection:
            valid_selection = [iid for iid in selection if iid in tree.get_children()]
            if valid_selection:
                tree.selection_set(valid_selection)

    def apply_theme_live(self):
        root = self.ui.root
        current_order = list(self.ui.tree.get_children())
        current_selection = list(self.ui.tree.selection())
        progress_value = self.ui.progressbar.get()
        volume = self.state.settings["volume"]

        if self.ui.audio_settings_window is not None and self.ui.audio_settings_window.winfo_exists():
            self.ui.audio_settings_window.destroy()
            self.ui.audio_settings_window = None

        root.config(menu=tk.Menu(root))
        for child in root.winfo_children():
            child.destroy()

        self.ui = build_gui(self, root=root)
        self.render_playlist(order=current_order, selection=current_selection)
        self.clear_playing()
        if self.state.current_song is not None:
            self.select_playing(self.state.current_song)
        self.ui.progressbar.set(progress_value)
        self.ui.slider.set(volume)
        self.setup_buttons()

    def ensure_audio_settings(self):
        available_devices = list(self.get_devices())
        configured_device = self.state.settings.get("audio_device", "")
        if configured_device in available_devices:
            return
        if available_devices:
            self.state.settings["audio_device"] = available_devices[0]
        else:
            self.state.settings["audio_device"] = ""

    def supports_hog_mode(self):
        return self.platform_system == "Darwin" and macos_audio is not None

    def is_hog_mode_enabled(self):
        return bool(self.state.settings.get("hog_mode", False))

    def release_hog_mode_if_needed(self):
        if not self.supports_hog_mode():
            return
        if not self.hog_mode_device_name:
            return
        try:
            macos_audio.release_hog_mode(device_name=self.hog_mode_device_name)
            print("Released hog mode:", self.hog_mode_device_name)
        except Exception as e:
            print("Cannot release hog mode:", self.hog_mode_device_name, e)
        finally:
            self.hog_mode_device_name = None

    def save_settings(self):
        config.save_settings(self.state.settings)

    def apply_hog_mode(self, device_name):
        if not self.supports_hog_mode():
            return

        self.release_hog_mode_if_needed()
        if not self.is_hog_mode_enabled():
            return

        if not device_name:
            return

        try:
            owner_pid = macos_audio.acquire_hog_mode(device_name=device_name)
            self.hog_mode_device_name = device_name
            print("Hog mode enabled:", device_name, "PID:", owner_pid)
        except Exception as e:
            self.state.settings["hog_mode"] = False
            self.save_settings()
            custom_messagebox_panel(
                parent=self.ui.tree,
                message=f"Cannot enable hog mode.\n{e}",
            )

    def format_tree_values(self, tags):
        values = []
        for column in self.state.settings["main_grid"]["fields"]:
            keys = re.findall(r"\{(.*?)\}", column)
            formatted_values = {}
            for key in keys:
                formatted_values[key] = tags.get(key, "")
            values.append(column.format(**formatted_values))
        return values

    def about(self):
        custom_messagebox_panel(
            parent=self.ui.tree,
            message=f"Milonga DJ Soft - Paweł Wąsowicz\nVersion: {config.get_version()}",
        )

    def export_playlist(self):
        file_path = filedialog.asksaveasfilename(
            title="Export to m3u file", filetypes=[("Playlist file:", "*.m3u")]
        )
        if file_path:
            files = utils.get_files_from_tree(self.ui.tree, self.state.songs)
            lists.save_m3u(files, file_path, save_external=True)

    def on_closing(self):
        if self.state.is_playing:
            custom_messagebox_panel(parent=self.ui.tree, message="Cannot close application while is playing.")
            return
        if self.ui.audio_settings_window is not None and self.ui.audio_settings_window.winfo_exists():
            self.ui.audio_settings_window = None
            self.ui.audio_settings_window.destroy()
        self.release_hog_mode_if_needed()
        player.quit_device()
        player.delete_tmp_files()
        self.ui.root.destroy()

    def disable_button(self, button):
        if button.cget("state") != "disabled":
            button.configure(state="disabled")

    def enable_button(self, button):
        if button.cget("state") != "normal":
            button.configure(state="normal")

    def setup_buttons(self):
        row_count = len(self.ui.tree.get_children())
        if row_count == 0:
            self.disable_button(self.ui.start_button)
            self.disable_button(self.ui.stop_button)
            self.disable_button(self.ui.delete_button)
            self.disable_button(self.ui.pause_button)
            self.disable_button(self.ui.next_button)
            return

        self.enable_button(self.ui.delete_button)
        if self.state.is_paused:
            self.disable_button(self.ui.start_button)
            self.disable_button(self.ui.stop_button)
            self.enable_button(self.ui.pause_button)
            self.disable_button(self.ui.next_button)

        if self.state.is_playing and not self.state.is_paused:
            self.disable_button(self.ui.start_button)
            self.enable_button(self.ui.stop_button)
            self.enable_button(self.ui.pause_button)
            self.enable_button(self.ui.next_button)
            self.disable_button(self.ui.audio_settings_button)

        if not self.state.is_playing:
            self.enable_button(self.ui.start_button)
            self.disable_button(self.ui.stop_button)
            self.disable_button(self.ui.pause_button)
            self.disable_button(self.ui.next_button)
            self.enable_button(self.ui.audio_settings_button)

    def open_audio_settings_window(self):
        if self.ui.audio_settings_window is not None and self.ui.audio_settings_window.winfo_exists():
            self.ui.audio_settings_window.focus()
            return

        window = tk.Toplevel(self.ui.root)
        window.title("Settings")
        window.geometry("1280x620")
        window.resizable(False, False)
        window.transient(self.ui.root)
        self.ui.audio_settings_window = window

        frame = tk.Frame(window, padx=16, pady=16)
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(1, weight=1)

        tk.Label(frame, text="Color theme").grid(row=0, column=0, sticky="w")
        theme_var = tk.StringVar(value=self.get_color_theme())
        theme_dropdown = customtkinter.CTkOptionMenu(
            frame,
            values=list(self.AVAILABLE_COLOR_THEMES),
            variable=theme_var,
            width=240,
        )
        theme_dropdown.grid(row=0, column=1, sticky="ew", padx=(12, 0))

        tk.Label(frame, text="Output device").grid(row=1, column=0, sticky="w", pady=(14, 0))
        self.ensure_audio_settings()
        device_values = list(self.get_devices())
        device_var = tk.StringVar(value=self.state.settings.get("audio_device", ""))
        device_dropdown = customtkinter.CTkOptionMenu(
            frame,
            values=device_values if device_values else [""],
            variable=device_var,
            width=240,
        )
        device_dropdown.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=(14, 0))

        hog_var = tk.BooleanVar(value=self.is_hog_mode_enabled())
        hog_switch = customtkinter.CTkSwitch(
            frame,
            text="Enable hog mode",
            variable=hog_var,
            onvalue=True,
            offvalue=False,
        )
        hog_switch.grid(row=2, column=0, columnspan=2, sticky="w", pady=(16, 0))
        if not self.supports_hog_mode():
            hog_switch.configure(state="disabled")

        tk.Label(frame, text="Genre EQ", font=("Arial", 13, "bold")).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(22, 8)
        )

        equalizer_settings = self.state.settings.get("genre_equalizer", {})
        genre_names = list(equalizer_settings.keys())
        selected_genre_var = tk.StringVar(value=genre_names[0] if genre_names else "default")
        tk.Label(frame, text="Preset genre").grid(row=4, column=0, sticky="w")
        genre_dropdown = customtkinter.CTkOptionMenu(
            frame,
            values=genre_names if genre_names else ["default"],
            variable=selected_genre_var,
            width=240,
        )
        genre_dropdown.grid(row=4, column=1, sticky="ew", padx=(12, 0))

        eq_enabled_var = tk.BooleanVar(value=False)
        eq_enabled_switch = customtkinter.CTkSwitch(
            frame,
            text="Enable equalizer for this genre",
            variable=eq_enabled_var,
            onvalue=True,
            offvalue=False,
        )
        eq_enabled_switch.grid(row=5, column=0, columnspan=3, sticky="w", pady=(14, 0))

        band_frame = tk.Frame(frame)
        band_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        eq_band_vars = {}
        eq_band_labels = {}
        band_order = ["25", "40", "63", "100", "160", "250", "400", "630", "1000", "1600", "2500", "4000", "6300", "10000", "16000"]
        band_display = {
            "25": "25",
            "40": "40",
            "63": "63",
            "100": "100",
            "160": "160",
            "250": "250",
            "400": "400",
            "630": "630",
            "1000": "1k",
            "1600": "1.6k",
            "2500": "2.5k",
            "4000": "4k",
            "6300": "6.3k",
            "10000": "10k",
            "16000": "16k",
        }
        for index, frequency in enumerate(band_order):
            column = tk.Frame(band_frame, padx=4)
            column.pack(side="left", fill="y", expand=True)
            tk.Label(column, text=band_display[frequency]).pack()
            value_label = tk.Label(column, text="0 dB")
            value_label.pack(pady=(4, 8))
            band_var = tk.DoubleVar(value=0.0)
            slider = customtkinter.CTkSlider(
                column,
                from_=-12,
                to=12,
                number_of_steps=24,
                variable=band_var,
                orientation="vertical",
                height=160,
            )
            slider.pack()
            eq_band_vars[frequency] = band_var
            eq_band_labels[frequency] = value_label

        button_row = tk.Frame(frame)
        button_row.grid(row=7, column=0, columnspan=3, sticky="e", pady=(48, 12))

        staged_equalizers = {}
        for genre_name, eq_settings in equalizer_settings.items():
            staged_equalizers[genre_name] = {
                "enabled": bool(eq_settings.get("enabled", False)),
                "bands": {band: float(eq_settings.get("bands", {}).get(band, 0)) for band in band_order},
            }

        current_eq_genre = {"name": selected_genre_var.get()}

        def update_band_labels():
            for frequency, value_label in eq_band_labels.items():
                value_label.configure(text=f"{int(round(eq_band_vars[frequency].get()))} dB")

        def store_current_eq_preset():
            genre_name = current_eq_genre["name"]
            if genre_name not in staged_equalizers:
                return
            staged_equalizers[genre_name] = {
                "enabled": bool(eq_enabled_var.get()),
                "bands": {frequency: int(round(eq_band_vars[frequency].get())) for frequency in band_order},
            }

        def load_eq_preset(genre_name):
            preset = staged_equalizers.get(
                genre_name,
                {"enabled": False, "bands": {band: 0 for band in band_order}},
            )
            eq_enabled_var.set(bool(preset.get("enabled", False)))
            for frequency in band_order:
                eq_band_vars[frequency].set(float(preset.get("bands", {}).get(frequency, 0)))
            update_band_labels()
            current_eq_genre["name"] = genre_name

        def on_eq_genre_change(selected_genre):
            store_current_eq_preset()
            load_eq_preset(selected_genre)

        genre_dropdown.configure(command=on_eq_genre_change)
        load_eq_preset(selected_genre_var.get())

        for frequency, band_var in eq_band_vars.items():
            band_var.trace_add("write", lambda *args: update_band_labels())

        def close_window():
            self.ui.audio_settings_window = None
            if window.winfo_exists():
                window.destroy()

        def save_audio_settings():
            selected_device = device_var.get().strip()
            selected_theme = theme_var.get().strip()
            theme_changed = selected_theme != self.get_color_theme()
            store_current_eq_preset()

            self.state.settings["color_theme"] = selected_theme
            self.state.settings["audio_device"] = selected_device
            self.state.settings["hog_mode"] = bool(hog_var.get())
            self.state.settings["genre_equalizer"] = staged_equalizers
            self.save_settings()
            self.set_audio_device(selected_device=selected_device)
            if theme_changed:
                self.apply_theme_live()
            close_window()

        save_button = customtkinter.CTkButton(
            button_row,
            text="Save",
            width=80,
            command=save_audio_settings,
        )
        save_button.pack(side="left", padx=(0, 8))

        close_button = customtkinter.CTkButton(
            button_row,
            text="Close",
            width=80,
            command=close_window,
        )
        close_button.pack(side="left")

        window.protocol("WM_DELETE_WINDOW", close_window)

    def b_down_shift(self, event):
        tree = event.widget
        selected_indexes = [tree.index(item) for item in tree.selection()]
        selected_indexes.append(tree.index(tree.identify_row(event.y)))
        selected_indexes.sort()
        for index in range(selected_indexes[0], selected_indexes[-1] + 1):
            tree.selection_add(tree.get_children()[index])

    def on_double_click(self, event):
        self.ui.tree.selection_set([])

    def b_down(self, event):
        tree = event.widget
        self.state.last_y = event.y
        item = tree.identify_row(event.y)
        if not item:
            return
        if item not in tree.selection():
            tree.selection_set(item)
        self.state.drag_items = tuple(tree.selection())
        self.state.is_dragging = False
        self.state.drop_target_index = None
        self.clear_drop_indicator()

    def b_up(self, event):
        if not self.state.is_dragging or not self.state.drag_items:
            self.state.drag_items = ()
            self.clear_drop_indicator()
            return

        target_index = self.get_drop_target_index(event.y)
        drag_items = [item for item in self.state.drag_items if item in self.ui.tree.get_children()]
        if drag_items:
            self.move_items_to_index(drag_items, target_index)
            self.persist_playlist_order()
            self.ui.tree.selection_set(drag_items)

        self.state.is_dragging = False
        self.state.drag_items = ()
        self.state.drop_target_index = None
        self.clear_drop_indicator()

    def b_up_shift(self, event):
        return None

    def select_mouse_row(self, item):
        if item == self.state.last_highlighted:
            return

        if self.state.last_highlighted:
            self.select_genre(self.state.last_highlighted)

        if item:
            all_items = self.ui.tree.get_children()
            if item not in all_items:
                return
            self.ui.tree.item(item, tags=("over",))

        self.state.last_highlighted = item
        if self.state.is_playing and self.state.current_song:
            self.ui.tree.item(self.state.current_song, tags=("play",))

    def on_mouse_enter(self, event):
        tree = event.widget
        if self.state.is_dragging:
            if event.y < 20:
                tree.yview_scroll(-1, "units")
            elif event.y > tree.winfo_height() - 20:
                tree.yview_scroll(1, "units")
            self.show_drop_indicator(event.y)

        self.select_mouse_row(tree.identify_row(event.y))

    def on_mouse_leave(self, event):
        self.clear_drop_indicator()
        self.clear_playing()
        if self.state.is_playing:
            all_items = self.ui.tree.get_children()
            if self.state.current_song not in all_items:
                return
            self.ui.tree.item(self.state.current_song, tags=("play",))

    def b_move(self, event):
        if not self.state.drag_items:
            return
        if self.state.last_y is not None and abs(event.y - self.state.last_y) < 4:
            return
        self.state.is_dragging = True
        self.on_mouse_enter(event)
        tree = event.widget
        item = tree.identify_row(event.y)
        tree.config(cursor="hand2" if item else "")

    def get_drop_target_index(self, y):
        children = self.ui.tree.get_children()
        if not children:
            return 0

        item = self.ui.tree.identify_row(y)
        if not item:
            return len(children)

        bbox = self.ui.tree.bbox(item)
        if not bbox:
            return self.ui.tree.index(item)

        item_index = self.ui.tree.index(item)
        midpoint = bbox[1] + (bbox[3] / 2)
        if y < midpoint:
            return item_index
        return item_index + 1

    def clear_drop_indicator(self):
        if self.state.drop_indicator_id is not None:
            self.state.drop_indicator_id.place_forget()
            self.state.drop_indicator_id.destroy()
            self.state.drop_indicator_id = None

    def show_drop_indicator(self, y):
        tree = self.ui.tree
        children = tree.get_children()
        if not children:
            self.clear_drop_indicator()
            return

        target_index = self.get_drop_target_index(y)
        self.state.drop_target_index = target_index

        if target_index >= len(children):
            target_item = children[-1]
            bbox = tree.bbox(target_item)
            if not bbox:
                self.clear_drop_indicator()
                return
            line_y = bbox[1] + bbox[3]
        else:
            target_item = children[target_index]
            bbox = tree.bbox(target_item)
            if not bbox:
                self.clear_drop_indicator()
                return
            line_y = bbox[1]

        x1 = 2
        width = max(tree.winfo_width() - 4, 2)
        self.clear_drop_indicator()
        indicator = tk.Frame(tree, bg="#ff6b35", height=3)
        indicator.place(x=x1, y=line_y - 1, width=width)
        self.state.drop_indicator_id = indicator

    def move_items_to_index(self, items, target_index):
        children = list(self.ui.tree.get_children())
        moving_set = set(items)
        remaining = [item for item in children if item not in moving_set]
        target_index = max(0, min(target_index, len(remaining)))
        new_order = remaining[:target_index] + list(items) + remaining[target_index:]
        for index, item in enumerate(new_order):
            self.ui.tree.move(item, "", index)

    def persist_playlist_order(self):
        files = utils.get_files_from_tree(self.ui.tree, self.state.songs)
        lists.save_m3u(files, config.get_default_playlist_full_file_name())
        player.save_converted_files()
        print("Saved")

    def get_selected_song(self):
        if not self.ui.tree.get_children():
            return None
        selected_item = self.ui.tree.selection()
        if selected_item:
            return selected_item[0]
        return self.ui.tree.get_children()[0]

    def get_next_song(self, current_iid):
        children = self.ui.tree.get_children()
        if not children or current_iid not in children:
            return None
        current_index = children.index(current_iid)
        if current_index == len(children) - 1:
            return None
        return children[current_index + 1]

    def select_genre(self, iid):
        if iid is None:
            return
        all_items = self.ui.tree.get_children()
        if iid not in all_items:
            return

        self.ui.tree.item(iid, tags=())
        tags = self.state.songs[iid][1]
        genre = tags.get("genre", "").lower()
        if "milonga" in genre:
            self.ui.tree.item(iid, tags=("milonga",))
        if "vals" in genre:
            self.ui.tree.item(iid, tags=("vals",))
        if "cortina" in genre:
            self.ui.tree.item(iid, tags=("cortina",))

    def clear_playing(self):
        for iid in self.ui.tree.get_children():
            self.select_genre(iid)

    def select_playing(self, song_id):
        self.clear_playing()
        all_items = self.ui.tree.get_children()
        if song_id in all_items:
            self.ui.tree.item(song_id, tags=("play",))

    def on_next(self):
        player.fade()

    def on_pause(self):
        if self.state.is_paused:
            pos = self.state.current_position + config.fade_time
            player.play_from_list(self.state.current_song, self.state.songs, pos=pos)
            self.select_playing(self.state.current_song)
            self.state.is_playing = True
            self.state.is_paused = False
            return

        self.state.current_position = player.get_pos()
        player.fade()
        self.state.is_paused = True

    def on_delete(self):
        selected_items = self.ui.tree.selection()
        if not selected_items:
            custom_messagebox_panel(parent=self.ui.tree, message="Select rows.")
            return

        result = custom_messagebox_panel(
            parent=self.ui.tree,
            message=f"Delete {len(selected_items)} song(s)?",
            show_cancel=True,
        )
        if not result:
            return

        converted_files = player.get_converted_files()
        for item in selected_items:
            file_name = self.state.songs[item][0]
            self.ui.tree.delete(item)
            self.state.songs.pop(item, None)
            if file_name in converted_files:
                print("Remove:", file_name)
                try:
                    os.remove(file_name)
                    player.remove_converted_file_from_list(file_name)
                except Exception as e:
                    print(str(e))

        files = utils.get_files_from_tree(self.ui.tree, self.state.songs)
        lists.save_m3u(files, config.get_default_playlist_full_file_name())
        player.save_converted_files()

    def set_volume(self, value):
        volume = float(value) / 100
        player.set_volume(volume)
        self.state.settings["volume"] = value
        self.save_settings()

    def on_start(self):
        song = self.get_selected_song()
        player.reset_progress()
        self.ui.progressbar.set(0)
        if song is None:
            return
        player.play_from_list(song, self.state.songs)
        self.select_playing(song)
        self.state.current_song = song
        self.state.is_playing = True

    def on_stop(self):
        result = custom_messagebox_panel(
            parent=self.ui.tree,
            message="Stop playing?",
            show_cancel=True,
        )
        if not result:
            return

        player.fade()
        self.clear_playing()
        player.reset_progress()
        if self.state.current_song in self.ui.tree.get_children():
            self.ui.tree.selection_set(self.state.current_song)
        self.state.is_playing = False
        global_vars.wave_canvas.delete("all")

    def make_drop(self, event):
        if not event.data:
            return event.action

        file_paths = re.findall(r"\{(.*?)\}", event.data)
        y = event.y_root - event.widget.winfo_rooty()
        current_item = event.widget.identify_row(y)
        start_pos = self.ui.progressbar.get()

        total_files = len(file_paths)
        for index, file_path in enumerate(reversed(file_paths), start=1):
            self.ui.progressbar.set(index / total_files)
            self.ui.root.update_idletasks()
            self.ui.root.after(100)
            self.ui.root.update()

            tags = lists.get_all_tags(file_path)
            if tags.get("title") is None:
                continue

            new_file = player.can_load_sound(file_path)
            if new_file is None:
                print("Wrong file: ", new_file)
                continue

            iid = str(uuid.uuid4())
            self.state.songs[iid] = (new_file, tags)

            tree_index = self.ui.tree.index(current_item)
            if current_item == "":
                tree_index = len(self.ui.tree.get_children())

            self.ui.tree.insert("", tree_index, iid=iid, values=self.format_tree_values(tags))
            current_item = iid
            print("File added: ", new_file)

        self.ui.progressbar.set(start_pos)
        files = utils.get_files_from_tree(self.ui.tree, self.state.songs)
        lists.save_m3u(files, config.get_default_playlist_full_file_name())
        player.save_converted_files()
        self.clear_playing()
        if self.state.current_song is not None:
            self.select_playing(self.state.current_song)
        return event.action

    def drop_position(self, event):
        y = event.y_root - event.widget.winfo_rooty()
        self.select_mouse_row(event.widget.identify_row(y))

    def drop(self, event):
        return self.make_drop(event)

    def set_audio_device(self, event=None, selected_device=None):
        player.stop()
        self.clear_playing()
        player.reset_progress()
        if selected_device is None:
            selected_device = self.state.settings.get("audio_device", "")
        previous_device = self.state.settings.get("audio_device", "")
        previous_hog_mode = self.state.settings.get("hog_mode", False)
        self.release_hog_mode_if_needed()

        try:
            self.state.settings["audio_device"] = selected_device
            if selected_device:
                player.set_device(selected_device)
                self.apply_hog_mode(selected_device)

            volume = self.state.settings["volume"]
            if self.state.current_song is not None:
                self.ui.tree.selection_set(self.state.current_song)
            self.ui.slider.set(volume)
            self.state.is_playing = False
            player.set_volume(float(volume) / 100)
            self.save_settings()
        except Exception as e:
            self.state.settings["audio_device"] = previous_device
            self.state.settings["hog_mode"] = previous_hog_mode
            self.save_settings()
            if previous_device:
                try:
                    player.set_device(previous_device)
                    self.apply_hog_mode(previous_device)
                    player.set_volume(float(self.state.settings["volume"]) / 100)
                except Exception as restore_error:
                    print("Cannot restore previous audio device:", restore_error)
            custom_messagebox_panel(
                parent=self.ui.tree,
                message=f"Cannot set audio device.\n{e}",
            )

    def resize(self, event):
        original_image = global_vars.canvas_image
        if original_image is None:
            return

        image = original_image.resize((event.width, event.height))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            temp_filename = tmpfile.name
            image.save(temp_filename)

        self.oimage = tk.PhotoImage(file=temp_filename)
        event.widget.create_image(0, 0, anchor="nw", image=self.oimage)
        os.remove(temp_filename)

    def update_device_list(self, event):
        return None

    def load_default_playlist(self):
        songs = {}
        tags = lists.get_audio_tags_from_m3u8(config.get_default_playlist_full_file_name())
        if tags is None:
            return songs

        for entry in tags:
            for file_path, file_tags in entry.items():
                iid = str(uuid.uuid4())
                songs[iid] = (file_path, file_tags)
        return songs

    def update_line(self):
        if self.line is not None:
            global_vars.wave_canvas.delete(self.line)

        pos = player.get_pos() + player.get_start_pos()
        duration = player.get_duration()
        if duration <= 0:
            return

        x_pos = (pos / duration) * global_vars.wave_canvas.winfo_width()
        self.line = global_vars.wave_canvas.create_line(
            x_pos,
            0,
            x_pos,
            global_vars.wave_canvas.winfo_height(),
            fill="red",
            width=2,
        )

    def update_loudness(self):
        self.state.is_converting = True
        try:
            for song_id in list(self.state.songs.keys()):
                data = self.state.songs.get(song_id)
                if data is None or len(data) != 2:
                    continue

                file_name = data[0]
                print("Calculating loudness and silence: ", file_name)
                loudness = player.get_loudness_from_file(file_name)
                new_data = list(data)
                new_data.append(loudness)
                start_cut, end_cut = player.detect_silence_start_end_from_file(file_name, 200, -56)
                new_data.append(start_cut)
                new_data.append(end_cut)
                self.state.songs[song_id] = tuple(new_data)
        finally:
            self.state.is_converting = False

    def draw_wave(self, temp_filename):
        self.oimage = tk.PhotoImage(file=temp_filename)
        global_vars.image_id = global_vars.wave_canvas.create_image(0, 0, anchor="nw", image=self.oimage)
        os.remove(temp_filename)

    def check_music(self):
        self.setup_buttons()

        if global_vars.wave_queue.qsize() > 0:
            self.draw_wave(global_vars.wave_queue.get(block=False))

        if not self.state.is_converting:
            self.state.is_converting = True
            thread = threading.Thread(target=self.update_loudness, daemon=True)
            thread.start()

        if player.get_busy() and self.state.current_song in self.state.songs:
            self.update_line()
            title = self.state.songs[self.state.current_song][1]["title"]
            pos = player.get_pos()
            total = player.get_duration()
            correction = player.get_loudness_corretion_db()
            if len(title) > 20:
                title = title[:17] + "..."

            self.ui.status_bar.configure(
                text=(
                    f"{title}  [{pos // 60000}:{(pos // 1000) % 60:02}] "
                    f"of [{int(total // 60000):00}:{int((total // 1000) % 60):02}] "
                    f"[{correction:.1f} dB]"
                )
            )
        else:
            self.ui.status_bar.configure(text="")

        if not (player.get_busy() or self.state.is_paused) and self.state.is_playing:
            self.state.waiting_time += self.dt
            if self.state.waiting_time >= config.pause_time:
                self.state.waiting_time = 0
                next_song = self.get_next_song(self.state.current_song)
                if next_song is not None:
                    self.state.current_song = next_song
                    self.select_playing(self.state.current_song)
                    player.reset_progress()
                    player.play_from_list(self.state.current_song, self.state.songs)
                else:
                    self.state.is_playing = False
                    self.state.current_song = None
                    self.clear_playing()
                    print("End...")
                print(next_song)

        self.ui.root.after(self.dt, self.check_music)
