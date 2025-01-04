import os
import sys

user_home = os.path.expanduser('~')
file_path = os.path.join(user_home, 'milonga.log')

f =open(file_path, 'w')
sys.stdout = f



the_path = os.path.dirname(os.path.abspath(__file__))
path_to_remove = os.path.join("lib", "library.zip")
if the_path.endswith(path_to_remove):
    the_path = the_path[: -len(path_to_remove)]
print("App path:", the_path)

os.chdir(the_path)

current_directory = os.getcwd()
p = current_directory + "/ffmpeg/"
os.environ["PATH"] += os.pathsep + p

import subprocess
from functools import wraps
import platform

if platform.system() == 'Windows':
    __old_Popen = subprocess.Popen
    @wraps(__old_Popen)
    def new_Popen(*args, startupinfo=None, **kwargs):
        if startupinfo is None:
            startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        startupinfo.wShowWindow = subprocess.SW_HIDE
        return __old_Popen(*args, startupinfo=startupinfo, **kwargs)

    subprocess.Popen = new_Popen



import global_vars
import config
import lists
import utils
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from tkinterdnd2 import *
from tkinter import filedialog
import threading
import platform

import re
import uuid
import player
import tempfile
from config import DEBUG
import customtkinter
from CTkMessagebox import CTkMessagebox

customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("blue")

last_highlighted = None
is_dragging = False
last_y = None
current_song = None
is_playing = False
is_paused = False
dt = 100
slider = None
progressbar = None
status_bar = None
settings = None

start_button = None
stop_button = None
delete_button = None
pause_button = None
next_button = None

audio_device_dropdown = None


def about():
    CTkMessagebox(title="Info", message="Milonga DJ Soft - Paweł Wąsowicz")


def export_playlist():
    file_path = filedialog.asksaveasfilename(
        title="Export to m3u8 file", filetypes=[("Playlist file:", "*.m3u")]
    )

    if file_path:
        files = utils.get_files_from_tree(tree, songs)
        lists.save_m3u(files, file_path, save_external=True)


def on_closing():
    global is_playing
    if is_playing:
        CTkMessagebox(
            title="Warning",
            message="Cannot close application while is playing.",
            icon="warning",
        )
    else:
        player.quit_device()
        player.delete_tmp_files()
        root.destroy()


def distable_button(the_button):
    if the_button.cget("state") != "disabled":
        the_button.configure(state="disabled")


def enable_button(the_button):
    if the_button.cget("state") != "normal":
        the_button.configure(state="normal")


def setup_buttons():
    global start_button
    global stop_button
    global delete_button
    global pause_button
    global next_button

    row_count = len(tree.get_children())

    if row_count == 0:
        distable_button(start_button)
        distable_button(stop_button)
        distable_button(delete_button)
        distable_button(pause_button)
        distable_button(next_button)
    else:
        enable_button(delete_button)
        if is_paused:
            distable_button(start_button)
            distable_button(stop_button)
            enable_button(pause_button)
            distable_button(next_button)

        if is_playing and not is_paused:
            distable_button(start_button)
            enable_button(stop_button)
            enable_button(pause_button)
            enable_button(next_button)

        if not is_playing:
            enable_button(start_button)
            distable_button(stop_button)
            distable_button(pause_button)
            distable_button(next_button)
            enable_button(audio_device_dropdown)

        if is_playing:
            distable_button(audio_device_dropdown)


def bDown_Shift(event):
    tv = event.widget
    select = [tv.index(s) for s in tv.selection()]
    select.append(tv.index(tv.identify_row(event.y)))
    select.sort()
    for i in range(select[0], select[-1] + 1, 1):
        tv.selection_add(tv.get_children()[i])


def on_double_click(event):
    tree.selection_set([])


def bDown(event):
    global last_y
    tv = event.widget
    last_y = event.y
    if tv.identify_row(event.y) not in tv.selection():
        tv.selection_set(tv.identify_row(event.y))


def bUp(event):
    global is_dragging
    if is_dragging:
        tv = event.widget
        moveto = tv.index(tv.identify_row(event.y))
        for s in reversed(tv.selection()):
            tv.move(s, "", moveto)

        files = utils.get_files_from_tree(tree, songs)
        lists.save_m3u(files, config.get_default_playlist_full_file_name())
        player.save_converted_files()
        print("Saved")
        is_dragging = False


def bUp_Shift(event):
    pass


def select_mouse_row(item):
    global last_highlighted
    global is_playing
    if item != last_highlighted:
        if last_highlighted:
            select_genre(last_highlighted)
        if item:
            all_items = tree.get_children()
            if item not in all_items:
                return
            tree.item(item, tags=("over",))
        last_highlighted = item
        if is_playing:
            tree.item(current_song, tags=("play",))


def on_mouse_enter(event):
    global is_dragging

    global current_song
    tree = event.widget

    if is_dragging:
        if event.y < 20:
            tree.yview_scroll(-1, "units")
        elif event.y > tree.winfo_height() - 20:
            tree.yview_scroll(1, "units")

    item = tree.identify_row(event.y)
    if item is not None:
        select_mouse_row(item)


def on_mouse_leave(event):
    global is_playing
    clear_playing()
    if is_playing:
        all_items = tree.get_children()
        if current_song not in all_items:
            return
        tree.item(current_song, tags=("play",))


def bMove(event):
    global is_dragging
    is_dragging = True
    on_mouse_enter(event)
    tree = event.widget
    item = tree.identify_row(event.y)
    if item:
        tree.config(cursor="hand2")
    else:
        tree.config(cursor="")


def get_selected_song():
    if not tree.get_children():
        return None
    selected_item = tree.selection()
    if selected_item:
        iid = selected_item[0]
    else:
        iid = tree.get_children()[0]

    return iid


def get_next_song(current_iid):
    children = tree.get_children()
    if not children:
        return None
    if current_iid not in children:
        return None
    current_index = children.index(current_iid)
    if current_index == len(children) - 1:
        return None
    next_iid = children[current_index + 1]
    return next_iid


def select_genre(iid):
    if iid is not None:
        all_items = tree.get_children()
        if iid not in all_items:
            return

        tree.item(iid, tags=())
        tags = songs[iid][1]
        if "genre" in tags:
            genre = tags["genre"].lower()
            if "milonga" in genre:
                tree.item(iid, tags=("milonga",))
            if "vals" in genre:
                tree.item(iid, tags=("vals",))
            if "cortina" in genre:
                tree.item(iid, tags=("cortina",))


def clear_playing():
    for iid in tree.get_children():
        select_genre(iid)


def select_playing(the_song):
    clear_playing()
    all_items = tree.get_children()
    if the_song in all_items:
        tree.item(the_song, tags=("play",))


current_postion = 0


def on_next():
    player.fade()


def on_pause():
    global is_paused
    global current_song
    global is_playing
    global current_postion
    if is_paused:
        pos = current_postion + config.fade_time
        player.play_from_list(current_song, songs, pos=pos)
        select_playing(current_song)
        is_playing = True
        is_paused = False
    else:
        current_postion = player.get_pos()
        player.fade()
        is_paused = True


def on_delete():
    selected_items = tree.selection()

    if not selected_items:
        CTkMessagebox(title="None selected", message="Select rows.", icon="warning")
        return

    msg = CTkMessagebox(
        title="Confirmation",
        message=f"Delete {len(selected_items)} song(s)?",
        icon="question",
        option_1="No",
        option_2="Yes",
    )
    response = msg.get()

    if response == "Yes":
        converted_files = player.get_converted_files()
        for item in selected_items:
            tree.delete(item)
            file_name = songs[item][0]
            if file_name in converted_files.keys():
                print("Remove:", file_name)
                try:
                    os.remove(file_name)
                    player.remove_converted_file_from_list(file_name)
                except Exception() as e:
                    print(str(e))

        files = utils.get_files_from_tree(tree, songs)
        lists.save_m3u(files, config.get_default_playlist_full_file_name())
        player.save_converted_files()


def set_volume(val):
    global settings
    volume = float(val) / 100
    player.set_volume(volume)
    settings["volume"] = val
    config.save_settings(settings)


def on_start():
    global is_playing
    global current_song
    global waiting_time
    song = get_selected_song()
    player.reset_progress()
    progressbar.set(0)
    if song is not None:
        player.play_from_list(song, songs)
        select_playing(song)
        current_song = song
        is_playing = True


def on_stop():
    global is_playing
    global current_song

    msg = CTkMessagebox(
        title="Confirmation",
        message="Stop playing?",
        icon="question",
        option_1="No",
        option_2="Yes",
    )
    response = msg.get()

    if response == "Yes":
        player.fade()
        clear_playing()
        player.reset_progress()
        all_items = tree.get_children()
        if current_song in all_items:
            tree.selection_set(current_song)
        is_playing = False
        global_vars.wave_canvas.delete("all")


def make_drop(event):
    global current_song
    if event.data:
        p = r"\{(.*?)\}"
        files = re.findall(p, event.data)
        y = event.y_root - event.widget.winfo_rooty()
        tree = event.widget
        currnet_item = tree.identify_row(y)
        columns = settings["main_grid"]["fields"]
        selections = []

        start_pos = progressbar.get()

        fn = len(files)
        i = 0
        for file in reversed(files):
            i = i + 1
            po = (i) / fn
            progressbar.set(po)
            root.update_idletasks()
            root.after(100)
            root.update()
            tags = lists.get_all_tags(file)
            if tags["title"] is not None:
                new_file = player.can_load_sound(file)
                if new_file is not None:
                    iid = str(uuid.uuid4())
                    songs[iid] = (new_file, tags)
                    values = [tags.get(colum, "") for colum in columns]

                    index = tree.index(currnet_item)

                    if currnet_item == "":
                        n = len(tree.get_children())
                        index = n

                    tree.insert("", index, iid=iid, values=values)
                    currnet_item = iid
                    selections.append(iid)
                    print("File added: ", new_file)
                else:
                    print("Wrong file: ", new_file)

                if len(tree.get_children()) != len(selections):
                    tree.selection_set(selections)
        progressbar.set(start_pos)

    files = utils.get_files_from_tree(tree, songs)
    lists.save_m3u(files, config.get_default_playlist_full_file_name())
    player.save_converted_files()
    clear_playing()
    if current_song is not None:
        select_playing(current_song)
    return event.action


current_line = None


def drop_position(event):
    y = event.y_root - event.widget.winfo_rooty()
    tree = event.widget
    currnet_item = tree.identify_row(y)
    select_mouse_row(currnet_item)


def drop(event):
    global current_line

    def worker():
        make_drop(event)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


settings = config.load_settings()


def set_audio_device(event):
    global audio_device_dropdown
    global is_playing

    player.stop()
    clear_playing()
    player.reset_progress()
    selected_device = audio_device_dropdown.get()
    player.set_device(selected_device)
    val = settings["volume"]
    if current_song is not None:
        tree.selection_set(current_song)
    slider.set(val)
    is_playing = False
    volume = float(val) / 100
    player.set_volume(volume)


oimage = None


def resize(event):
    global oimage
    original_image = global_vars.canvas_image
    if original_image is not None:
        width = event.width
        height = event.height
        img = original_image.resize((width, height))
        canvas = event.widget
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            temp_filename = tmpfile.name
            img.save(temp_filename)

        oimage = tk.PhotoImage(file=temp_filename)
        canvas.create_image(0, 0, anchor="nw", image=oimage)
        os.remove(temp_filename)


class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


customtkinter.set_appearance_mode("system")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme(
    "blue"
)  # Themes: blue (default), dark-blue, green


def build_gui():
    global slider
    global progressbar
    global status_bar

    global start_button
    global stop_button
    global delete_button
    global pause_button
    global next_button
    global audio_device_dropdown

    root = CTk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    icon = PhotoImage(file="./icons/icon.png")
    root.iconphoto(True, icon)
    root.title("Milonga")

    menu_bar = tk.Menu(root)

    if platform.system() == "Darwin":  # macOS
        app_menu = tk.Menu(menu_bar, name="apple")
        menu_bar.add_cascade(menu=app_menu)
    else:
        app_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=app_menu)

    app_menu.add_command(label="About Milonga", command=about)
    app_menu.add_command(label="Export playlist", command=export_playlist)
    app_menu.add_separator()
    app_menu.add_command(label="Quit", command=root.quit)

    root.config(menu=menu_bar)
    toolbar = customtkinter.CTkFrame(root)
    toolbar.pack(side="top", fill="x")

    slider = customtkinter.CTkSlider(master=root, from_=0, to=100, command=set_volume)
    slider.pack(side="top", fill="x", padx=10, pady=5)

    global_vars.wave_canvas = customtkinter.CTkCanvas(master=root, width=800, height=50)
    global_vars.wave_canvas.pack(side="top", fill="x", padx=10, pady=5)
    global_vars.wave_canvas.bind("<Configure>", resize)

    progressbar = customtkinter.CTkProgressBar(master=root)
    progressbar.pack(side="top", fill="x", padx=10, pady=5)

    panel = customtkinter.CTkFrame(root)
    panel.pack(side="bottom", fill="x", padx=10, pady=10)

    status_bar = customtkinter.CTkLabel(panel, text="", anchor="w", height=30)
    status_bar.pack(side="left", fill="x", padx=0)

    device_list = player.get_devices()
    audio_device_dropdown = customtkinter.CTkOptionMenu(
        panel, values=device_list, command=set_audio_device
    )
    audio_device_dropdown.pack(side="right", padx=0)

    play_icon = utils.load_and_resize_image(file="./icons/play.png")
    stop_icon = utils.load_and_resize_image(file="./icons/stop.png")
    delete_icon = utils.load_and_resize_image(file="./icons/delete.png")
    pause_icon = utils.load_and_resize_image(file="./icons/pause.png")
    next_icon = utils.load_and_resize_image(file="./icons/next.png")

    start_button = customtkinter.CTkButton(
        toolbar, image=play_icon, command=on_start, text="Start"
    )
    start_button.image = play_icon
    start_button.pack(side="left", padx=2, pady=2)

    stop_button = customtkinter.CTkButton(
        toolbar, image=stop_icon, command=on_stop, text="Stop"
    )
    stop_button.image = stop_icon
    stop_button.pack(side="left", padx=2, pady=2)

    pause_button = customtkinter.CTkButton(
        toolbar, image=pause_icon, command=on_pause, text="Pause"
    )
    pause_button.image = pause_icon
    pause_button.pack(side="left", padx=2, pady=2)

    next_button = customtkinter.CTkButton(
        toolbar, image=next_icon, command=on_next, text="Next"
    )
    next_button.image = next_icon
    next_button.pack(side="left", padx=2, pady=2)

    delete_button = customtkinter.CTkButton(
        toolbar, image=delete_icon, command=on_delete, text="Delete"
    )
    delete_button.image = delete_icon
    delete_button.pack(side="left", padx=2, pady=2)
    columns = settings["main_grid"]["fields"]

    bg_color = root._apply_appearance_mode(
        customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"]
    )
    text_color = root._apply_appearance_mode(
        customtkinter.ThemeManager.theme["CTkLabel"]["text_color"]
    )

    treestyle = ttk.Style()
    treestyle.theme_use("default")
    treestyle.configure(
        "Treeview",
        background=bg_color,
        foreground=text_color,
        fieldbackground=bg_color,
        #borderwidth=1,
        relief = 'flat',
        font=("Arial", 12),
    )
    treestyle.configure(
        "Treeview.Heading",
        foreground="white",
        relief="flat",
        font=("Arial", 12),
    )

    root.bind("<<TreeviewSelect>>", lambda event: root.focus_set())

    tree = ttk.Treeview(root, columns=columns, selectmode="none", show="headings")

    for i, header in enumerate(settings["main_grid"]["headers"]):
        tree.heading(i, text=header)

    vsb = customtkinter.CTkScrollbar(root, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    tree.tag_configure("play", background="yellow", foreground="blue")
    tree.tag_configure("over", background="silver", foreground="white")
    tree.tag_configure("cortina", foreground="red")
    tree.tag_configure("vals", foreground="green")
    tree.tag_configure("milonga", foreground="yellow")

    tree.tag_configure("default", background="#ffffff")

    tree.bind("<ButtonPress-1>", bDown)
    tree.bind("<ButtonRelease-1>", bUp, add="+")
    tree.bind("<B1-Motion>", bMove, add="+")
    tree.bind("<Shift-ButtonPress-1>", bDown_Shift, add="+")
    tree.bind("<Shift-ButtonRelease-1>", bUp_Shift, add="+")
    tree.bind("<Motion>", on_mouse_enter)
    tree.bind("<Leave>", on_mouse_leave)
    tree.bind("<Double-1>", on_double_click)

    tree.drop_target_register(DND_FILES)
    tree.dnd_bind("<<Drop>>", drop)
    tree.dnd_bind("<<DropPosition>>", drop_position)

    return root, tree


def load_default_playlist(tree):
    songs = {}
    columns = settings["main_grid"]["fields"]
    tags = lists.get_audio_tags_from_m3u8(config.get_default_playlist_full_file_name())
    if tags is None:
        return songs

    for entry in tags:
        for file_path, file_tags in entry.items():
            values = [file_tags.get(colum_name, "") for colum_name in columns]
        iid = str(uuid.uuid4())
        tree.insert("", "end", iid=iid, values=values)

        songs[iid] = (file_path, file_tags)
    return songs


waiting_time = 0

line = None


def update_line():
    global line
    if line is not None:
        global_vars.wave_canvas.delete(line)

    pos = player.get_pos() + player.get_start_pos()
    duration = player.get_duration()

    if duration > 0:
        x_pos = (pos / duration) * global_vars.wave_canvas.winfo_width()
        line = global_vars.wave_canvas.create_line(
            x_pos, 0, x_pos, global_vars.wave_canvas.winfo_height(), fill="red", width=2
        )


is_converting = False


def update_loudness():
    global is_converting
    is_converting = True

    copy_cat = songs.copy()
    for id in copy_cat.keys():
        data = songs[id]
        if len(data) == 2:
            file = data[0]
            print("Calculating loudness and silence: ", file)
            vol = player.get_loudness_from_file(file)
            new_data = list(data)
            new_data.append(vol)
            start_cut, end_cut = player.detect_silence_start_end_from_file(
                file, 200, -56
            )
            new_data.append(start_cut)
            new_data.append(end_cut)
            songs[id] = tuple(new_data)
    is_converting = False


def check_music():
    global is_playing
    global current_song
    global waiting_time

    setup_buttons()

    def worker():
        update_loudness()

    if not is_converting:
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    if player.get_busy():
        update_line()
        title = songs[current_song][1]["title"]
        pos = player.get_pos()
        total = player.get_duration()
        correction = player.get_loudness_corretion()
        status_bar.configure(
            text="   {title}  [{minutes}:{seconds:02}] of [{minutes_total:00}:{seconds_total:02}]  [vol: {correction}%]".format(
                title=title,
                minutes=pos // 60000,
                seconds=(pos // 1000) % 60,
                minutes_total=int(total // 60000),
                seconds_total=int((total // 1000) % 60),
                correction=int(correction * 100),
            )
        )

    else:
        status_bar.configure(text="")
    if not (player.get_busy() or is_paused):
        if is_playing:

            waiting_time = waiting_time + dt
            if waiting_time < config.pause_time:
                pass
            else:
                waiting_time = 0
                next_song = get_next_song(current_song)
                if next_song is not None:
                    current_song = next_song
                    select_playing(current_song)
                    player.reset_progress()
                    player.play_from_list(current_song, songs)
                else:
                    is_playing = False
                    current_song = None
                    clear_playing()
                    print("End...")
                print(next_song)

    root.after(dt, check_music)


player.init_player()
root, tree = build_gui()
root.after(dt, check_music)
songs = load_default_playlist(tree)
player.load_converted_files()
clear_playing()
progressbar.set(0)
val = settings["volume"]
slider.set(val)
volume = float(val) / 100
player.set_volume(volume)
config.save_settings(settings)
selected_device = audio_device_dropdown.get()
player.set_device(selected_device)

if DEBUG:
    from utils import get_libraries

    get_libraries()

root.mainloop()
