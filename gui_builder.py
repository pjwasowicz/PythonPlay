from tkinter import PhotoImage, font, ttk
import tkinter as tk

import customtkinter
from tkinterdnd2 import DND_FILES, TkinterDnD

import global_vars
import utils
from app_state import UIRefs


customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("blue")


class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


def _get_row_count(settings):
    column = settings["main_grid"]["fields"][0]
    return column.count("\n") + 1


def build_gui(app):
    ui = UIRefs()
    root = CTk()
    ui.root = root

    root.geometry("430x800")
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    icon = PhotoImage(file="./icons/icon.png")
    root.iconphoto(True, icon)
    root.title("Milonga")

    menu_bar = tk.Menu(root)
    if app.platform_system == "Darwin":
        app_menu = tk.Menu(menu_bar, name="apple")
        menu_bar.add_cascade(menu=app_menu)
    else:
        app_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=app_menu)

    app_menu.add_command(label="About Milonga", command=app.about)
    app_menu.add_command(label="Export playlist", command=app.export_playlist)
    app_menu.add_separator()
    app_menu.add_command(label="Quit", command=root.quit)
    root.config(menu=menu_bar)

    toolbar = customtkinter.CTkFrame(root)
    toolbar.pack(side="top", fill="both")

    toolbar_down = customtkinter.CTkFrame(root)
    toolbar_down.pack(side="top", fill="both")

    ui.slider = customtkinter.CTkSlider(master=root, from_=0, to=100, command=app.set_volume)
    ui.slider.pack(side="top", fill="x", padx=10, pady=5)

    global_vars.wave_canvas = customtkinter.CTkCanvas(master=root, width=800, height=50)
    global_vars.wave_canvas.pack(side="top", fill="x", padx=10, pady=5)
    global_vars.wave_canvas.bind("<Configure>", app.resize)

    ui.progressbar = customtkinter.CTkProgressBar(master=root)
    ui.progressbar.pack(side="top", fill="x", padx=10, pady=5)

    panel = customtkinter.CTkFrame(root)
    panel.pack(side="bottom", fill="x", padx=10, pady=10)

    ui.status_bar = customtkinter.CTkLabel(panel, text="", anchor="w", height=30)
    ui.status_bar.pack(side="left", fill="x", padx=0)

    ui.audio_device_dropdown = customtkinter.CTkOptionMenu(
        panel,
        values=app.get_devices(),
        command=app.set_audio_device,
        width=150,
    )
    ui.audio_device_dropdown.pack(side="right", padx=0)
    ui.audio_device_dropdown.bind("<Button-1>", app.update_device_list)

    play_icon = utils.load_and_resize_image(file="./icons/play.png")
    stop_icon = utils.load_and_resize_image(file="./icons/stop.png")
    delete_icon = utils.load_and_resize_image(file="./icons/delete.png")
    pause_icon = utils.load_and_resize_image(file="./icons/pause.png")
    next_icon = utils.load_and_resize_image(file="./icons/next.png")

    ui.start_button = customtkinter.CTkButton(toolbar, image=play_icon, command=app.on_start, text="Start")
    ui.start_button.image = play_icon
    ui.start_button.pack(side="left", padx=2, pady=2)

    ui.stop_button = customtkinter.CTkButton(toolbar, image=stop_icon, command=app.on_stop, text="Stop")
    ui.stop_button.image = stop_icon
    ui.stop_button.pack(side="left", padx=2, pady=2)

    ui.pause_button = customtkinter.CTkButton(toolbar, image=pause_icon, command=app.on_pause, text="Pause")
    ui.pause_button.image = pause_icon
    ui.pause_button.pack(side="left", padx=2, pady=2)

    ui.next_button = customtkinter.CTkButton(toolbar_down, image=next_icon, command=app.on_next, text="Next")
    ui.next_button.image = next_icon
    ui.next_button.pack(side="left", padx=2, pady=2)

    ui.delete_button = customtkinter.CTkButton(toolbar_down, image=delete_icon, command=app.on_delete, text="Delete")
    ui.delete_button.image = delete_icon
    ui.delete_button.pack(side="left", padx=2, pady=2)

    columns = app.state.settings["main_grid"]["fields"]
    bg_color = root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"])
    text_color = root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])

    treestyle = ttk.Style()
    treestyle.theme_use("default")

    font_size = 12
    font_name = "Arial"
    num_lines = _get_row_count(app.state.settings)
    my_font = font.Font(family=font_name, size=font_size)
    font_height = my_font.metrics("linespace") + 1

    treestyle.configure(
        "Treeview",
        background=bg_color,
        foreground=text_color,
        fieldbackground=bg_color,
        relief="flat",
        font=(font_name, font_size),
        rowheight=font_height * num_lines + 5,
    )
    treestyle.configure(
        "Treeview.Heading",
        foreground="white",
        relief="flat",
        font=(font_name, font_size),
    )

    root.bind("<<TreeviewSelect>>", lambda event: root.focus_set())

    ui.tree = ttk.Treeview(root, columns=columns, selectmode="none", show="headings")
    ui.tree.column(columns[-1], width=20)

    for index, header in enumerate(app.state.settings["main_grid"]["headers"]):
        ui.tree.heading(index, text=header)

    vsb = customtkinter.CTkScrollbar(root, command=ui.tree.yview)
    ui.tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    ui.tree.pack(side="left", fill="both", expand=True)

    ui.tree.tag_configure("play", background="yellow", foreground="blue")
    ui.tree.tag_configure("over", background="silver", foreground="white")
    ui.tree.tag_configure("cortina", foreground="red")
    ui.tree.tag_configure("vals", foreground="green")
    ui.tree.tag_configure("milonga", foreground="orange")
    ui.tree.tag_configure("default", background="#ffffff")

    ui.tree.bind("<ButtonPress-1>", app.b_down)
    ui.tree.bind("<ButtonRelease-1>", app.b_up, add="+")
    ui.tree.bind("<B1-Motion>", app.b_move, add="+")
    ui.tree.bind("<Shift-ButtonPress-1>", app.b_down_shift, add="+")
    ui.tree.bind("<Shift-ButtonRelease-1>", app.b_up_shift, add="+")
    ui.tree.bind("<Motion>", app.on_mouse_enter)
    ui.tree.bind("<Leave>", app.on_mouse_leave)
    ui.tree.bind("<Double-1>", app.on_double_click)

    ui.tree.drop_target_register(DND_FILES)
    ui.tree.dnd_bind("<<Drop>>", app.drop)
    ui.tree.dnd_bind("<<DropPosition>>", app.drop_position)

    return ui
