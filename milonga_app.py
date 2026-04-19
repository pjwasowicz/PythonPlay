import os
import platform
import re
import tempfile
import threading
import tkinter as tk
import uuid
from tkinter import filedialog

import config
import global_vars
import lists
import player
import utils
from app_state import AppState
from custom_message_box import custom_messagebox_panel
from gui_builder import build_gui


class MilongaApp:
    def __init__(self):
        self.dt = 100
        self.line = None
        self.oimage = None
        self.platform_system = platform.system()
        self.state = AppState(settings=config.load_settings())
        self.ui = None

    def run(self):
        player.load_converted_files()
        player.init_player()
        self.ui = build_gui(self)
        self.ui.root.after(self.dt, self.check_music)
        self.state.songs = self.load_default_playlist()
        self.clear_playing()
        self.ui.progressbar.set(0)
        volume = self.state.settings["volume"]
        self.ui.slider.set(volume)
        config.save_settings(self.state.settings)
        normalized_volume = float(volume) / 100

        selected_device = self.ui.audio_device_dropdown.get()
        if selected_device:
            player.set_device(selected_device)
        player.set_volume(normalized_volume)

        self.ui.root.mainloop()

    def get_devices(self):
        return player.get_devices()

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

        if not self.state.is_playing:
            self.enable_button(self.ui.start_button)
            self.disable_button(self.ui.stop_button)
            self.disable_button(self.ui.pause_button)
            self.disable_button(self.ui.next_button)
            self.enable_button(self.ui.audio_device_dropdown)

        if self.state.is_playing:
            self.disable_button(self.ui.audio_device_dropdown)

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
        if tree.identify_row(event.y) not in tree.selection():
            tree.selection_set(tree.identify_row(event.y))

    def b_up(self, event):
        if not self.state.is_dragging:
            return

        tree = event.widget
        move_to = tree.index(tree.identify_row(event.y))
        for item in reversed(tree.selection()):
            tree.move(item, "", move_to)

        files = utils.get_files_from_tree(self.ui.tree, self.state.songs)
        lists.save_m3u(files, config.get_default_playlist_full_file_name())
        player.save_converted_files()
        print("Saved")
        self.state.is_dragging = False

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

        self.select_mouse_row(tree.identify_row(event.y))

    def on_mouse_leave(self, event):
        self.clear_playing()
        if self.state.is_playing:
            all_items = self.ui.tree.get_children()
            if self.state.current_song not in all_items:
                return
            self.ui.tree.item(self.state.current_song, tags=("play",))

    def b_move(self, event):
        self.state.is_dragging = True
        self.on_mouse_enter(event)
        tree = event.widget
        item = tree.identify_row(event.y)
        tree.config(cursor="hand2" if item else "")

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
        config.save_settings(self.state.settings)

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

    def set_audio_device(self, event=None):
        player.stop()
        self.clear_playing()
        player.reset_progress()
        selected_device = self.ui.audio_device_dropdown.get()
        player.set_device(selected_device)
        volume = self.state.settings["volume"]
        if self.state.current_song is not None:
            self.ui.tree.selection_set(self.state.current_song)
        self.ui.slider.set(volume)
        self.state.is_playing = False
        player.set_volume(float(volume) / 100)

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
        self.ui.audio_device_dropdown.configure(values=player.get_devices())

    def load_default_playlist(self):
        songs = {}
        tags = lists.get_audio_tags_from_m3u8(config.get_default_playlist_full_file_name())
        if tags is None:
            return songs

        for entry in tags:
            for file_path, file_tags in entry.items():
                iid = str(uuid.uuid4())
                self.ui.tree.insert("", "end", iid=iid, values=self.format_tree_values(file_tags))
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
