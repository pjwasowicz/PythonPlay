import config
import lists
import utils
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from tkinterdnd2 import *


import re
import uuid
import player
from tkinter import messagebox
#from config import pause_time

from config import DEBUG

import customtkinter

customtkinter.set_appearance_mode("light")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")

last_highlighted = None
is_dragging = False
last_y = None
current_song = None
is_playing = False
is_paused  = False
dt = 100
slider = None
progressbar = None


def bDown_Shift(event):
    tv = event.widget
    select = [tv.index(s) for s in tv.selection()]
    select.append(tv.index(tv.identify_row(event.y)))
    select.sort()
    for i in range(select[0],select[-1]+1,1):
        tv.selection_add(tv.get_children()[i])

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
            tv.move(s, '', moveto)

        files = utils.get_files_from_tree(tree,songs)
        lists.save_to_m3u8(files,config.get_default_playlist_full_file_name())

        print('Saved')
        is_dragging = False
    #tree.selection_set(())

def bUp_Shift(event):
    pass

#values= None


def on_mouse_enter(event):

    global is_dragging
    global last_highlighted
    tree = event.widget

    if is_dragging:
        if event.y < 20:
            tree.yview_scroll(-1, "units")
        elif event.y > tree.winfo_height() - 20:
            tree.yview_scroll(1, "units")

    item = tree.identify_row(event.y)



    if item != last_highlighted:
        """
        # Usuń podświetlenie z poprzedniego wiersza
        if last_highlighted:
            tree.item(last_highlighted, tags=())

        # Ustaw podświetlenie na nowym wierszu
        if item:
            tree.item(item, tags=("green",))

        # Zaktualizuj ostatnio podświetlony wiersz
        """
        last_highlighted = item


def on_mouse_leave(event):
    tree = event.widget
    item = tree.identify_row(event.y)
    if item:
        tree.item(item, tags=())
    else:
        pass


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

def clear_playing():
    for iid in tree.get_children():
        tree.item(iid, tags=())
        tags = songs[iid][1]
        if "genre" in tags:
            genre = tags["genre"]
            if "milonga" in genre.lower():
                tree.item(iid, tags=("milonga",))
            if "vals" in genre.lower():
                tree.item(iid, tags=("vals",))
            if "cortina" in genre.lower():
                tree.item(iid, tags=("cortina",))



def select_playing(the_song):
    clear_playing()
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
        player.play_from_list(current_song,songs,pos=pos)
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
        messagebox.showwarning("Brak zaznaczenia", "Nie zaznaczono żadnych elementów do usunięcia.")
        return
    confirm = messagebox.askyesno("Potwierdzenie usunięcia",
                                  f"Czy na pewno chcesz usunąć {len(selected_items)} element(y)?")

    if confirm:
        for item in selected_items:
            tree.delete(item)
        files = utils.get_files_from_tree(tree,songs)
        lists.save_to_m3u8(files,config.get_default_playlist_full_file_name())

def set_volume(val):
    volume = float(val) / 100
    player.set_volume(volume)


def on_start():
    global is_playing
    global current_song
    global waiting_time
    song = get_selected_song()
    player.reset_progress()
    progressbar.set(0)
    if song is not None:
        player.play_from_list(song,songs)
        select_playing(song)
        current_song = song
        is_playing = True



def on_stop():
    global is_playing
    global current_song
    player.fade()
    clear_playing()
    player.reset_progress()
    tree.selection_set(current_song)
    is_playing = False

def drop(event):
    global current_song
    if event.data:
        p= r"\{(.*?)\}"
        files = re.findall(p, event.data)
        y = event.y_root - event.widget.winfo_rooty()
        tree = event.widget
        currnet_item = tree.identify_row(y)
        columns = settings['main_grid']['fields']
        selections = []
        for file in reversed(files):
            tags = lists.get_all_tags(file)
            if tags['title'] is not None:
                iid = str(uuid.uuid4())
                songs[iid] = (file,tags)
                values = [tags.get(colum, "") for colum in columns]
                index = tree.index(currnet_item)
                tree.insert('', index, iid=iid, values=values)
                currnet_item = iid
                selections.append(iid)
                print('File added: ',file)
            else:
                print('Wrong file: ',file)

            tree.selection_set(selections)
    files = utils.get_files_from_tree(tree,songs)
    lists.save_to_m3u8(files,config.get_default_playlist_full_file_name())
    clear_playing()
    if current_song is not None:
        select_playing(current_song)
    return event.action

settings = config.load_settings()



class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

customtkinter.set_appearance_mode("system")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

def build_gui():
    global slider
    global progressbar
    #root = tk.Tk()
    #root = customtkinter.CTk()
    root = CTk()
    #ot.withdraw()

    root.title("Milonga")

    # Pasek narzędzi
    #toolbar = tk.Frame(root, bg="#f0f0f0", bd=1, relief="raised")
    toolbar = customtkinter.CTkFrame(root)
    toolbar.pack(side="top", fill="x")

    #slider = ttk.Scale(root, from_=0, to=100, orient="horizontal")
    slider = customtkinter.CTkSlider(master=root, from_=0, to=100, command=set_volume)
    slider.pack(side="top", fill="x", padx=10, pady=5)

    progressbar = customtkinter.CTkProgressBar(master=root)
    progressbar.pack(side="top", fill="x", padx=10, pady=5)


    # Ikony do przycisków
    play_icon = utils.load_and_resize_image(file="play.png")
    stop_icon = utils.load_and_resize_image(file="stop.png")
    delete_icon = utils.load_and_resize_image(file="delete.png")
    pause_icon = utils.load_and_resize_image(file="pause.png")
    next_icon = utils.load_and_resize_image(file="next.png")


    # Przycisk Start
    start_button = customtkinter.CTkButton(toolbar, image=play_icon, command=on_start, text = "Start")
    start_button.image = play_icon  # Zachowanie referencji do obrazu
    start_button.pack(side="left", padx=2, pady=2)

    # Przycisk Stop
    stop_button = customtkinter.CTkButton(toolbar, image=stop_icon, command=on_stop, text = "Stop")
    stop_button.image = stop_icon  # Zachowanie referencji do obrazu
    stop_button.pack(side="left", padx=2, pady=2)

    pause_button = customtkinter.CTkButton(toolbar, image=pause_icon, command=on_pause, text = "Pause")
    pause_button.image = pause_icon  # Zachowanie referencji do obrazu
    pause_button.pack(side="left", padx=2, pady=2)

    next_button = customtkinter.CTkButton(toolbar, image=next_icon, command=on_next, text = "Next")
    next_button.image = next_icon  # Zachowanie referencji do obrazu
    next_button.pack(side="left", padx=2, pady=2)

    #Przycisk Delete
    delete_button = customtkinter.CTkButton(toolbar, image=delete_icon, command=on_delete, text = "Delete")
    delete_button.image = delete_icon  # Zachowanie referencji do obrazu
    delete_button.pack(side="left", padx=2, pady=2)
    # Ustawienia kolumn Treeview
    columns = settings['main_grid']['fields']

    ###Treeview Customisation (theme colors are selected)
    bg_color = root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"])
    text_color = root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
    #selected_color = root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    treestyle = ttk.Style()
    treestyle.theme_use('default')
    treestyle.configure("Treeview", background=bg_color, foreground=text_color,
                        fieldbackground=bg_color, borderwidth=0,font=("Arial", 14),

                        )
    treestyle.configure("Treeview.Heading",
                    #background="#2c2f33",  # Tło nagłówka
                    foreground="white",    # Kolor tekstu nagłówka
                    #font=("Arial", 16, "bold"),  # Czcionka nagłówka
                    relief="flat",font=("Arial", 14))         # Styl obramowania (płaskie)

    #treestyle.map('Treeview', background=[('selected', bg_color)], foreground=[('selected', selected_color)])
    root.bind("<<TreeviewSelect>>", lambda event: root.focus_set())

    tree = ttk.Treeview(root, columns=columns, selectmode='none', show='headings')



    for i, header in enumerate(settings['main_grid']['headers']):
        tree.heading(i, text=header)

    vsb = ttk.Scrollbar(root, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)


    # Konfiguracja tagów
    tree.tag_configure("play", background="#ccffcc", foreground="blue")

    tree.tag_configure("cortina", foreground="red")
    tree.tag_configure("vals",foreground="green")
    tree.tag_configure("milonga", foreground="yellow")

    tree.tag_configure("default", background="#ffffff")

    # Obsługa zdarzeń myszy
    tree.bind("<ButtonPress-1>", bDown)
    tree.bind("<ButtonRelease-1>", bUp, add='+')
    tree.bind("<B1-Motion>", bMove, add='+')
    tree.bind("<Shift-ButtonPress-1>", bDown_Shift, add='+')
    tree.bind("<Shift-ButtonRelease-1>", bUp_Shift, add='+')
    tree.bind("<Motion>", on_mouse_enter)
    tree.bind("<Leave>", on_mouse_leave)

    tree.drop_target_register(DND_FILES)
    tree.dnd_bind('<<Drop>>', drop)

    return root, tree




def load_default_playlist(tree):
    songs = {}
    columns = settings['main_grid']['fields']
    tags = lists.get_audio_tags_from_m3u8(config.get_default_playlist_full_file_name())
    if tags is None:
        return songs

    for entry in tags:
        for file_path, file_tags in entry.items():
            values = [file_tags.get(colum_name, "") for colum_name in columns]
        iid=str(uuid.uuid4())
        tree.insert('', 'end', iid=iid, values = values)

        songs[iid] = (file_path,file_tags)
    return songs


waiting_time = 0

def check_music():
    global is_playing
    global current_song
    global waiting_time

    if player.get_busy():
        progressbar.set(player.get_progress())

    #print(player.get_busy(),is_paused)
    if not (player.get_busy() or is_paused):
        if is_playing:

            waiting_time = waiting_time + dt
            if waiting_time < config.pause_time:
                #print('Czekam...')
                pass
            else:
                waiting_time = 0
                next_song = get_next_song(current_song)
                if next_song is not None:
                    current_song = next_song
                    select_playing(current_song)
                    player.reset_progress()
                    player.play_from_list(current_song,songs)
                else:
                    is_playing = False
                    current_song = None
                    clear_playing()
                    print("End...")
                print(next_song)

    root.after(dt, check_music)

player.init_player()

root,tree = build_gui()
root.after(100, check_music)

songs = load_default_playlist(tree)
clear_playing()

if DEBUG:
    from utils import get_libraries
    get_libraries()

root.mainloop()

