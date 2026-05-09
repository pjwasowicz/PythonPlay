from tkinter import PhotoImage, font, ttk
import tkinter as tk

import customtkinter
from tkinterdnd2 import DND_FILES, TkinterDnD

import global_vars
import utils
from app_state import UIRefs


customtkinter.set_appearance_mode("system")


EQ_PANEL_COLLAPSED_HEIGHT = 60
EQ_PANEL_EXPANDED_HEIGHT = 236
EQ_CANVAS_HEIGHT = 150


class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


def _get_row_count(settings):
    column = settings["main_grid"]["fields"][0]
    return column.count("\n") + 1


def build_gui(app, root=None):
    if not hasattr(app, "eq_staged_equalizers") or not hasattr(app, "initialize_eq_state"):
        raise AttributeError("MilongaApp is missing EQ state initialization")
    if not getattr(app, "eq_staged_equalizers", None):
        app.initialize_eq_state()

    customtkinter.set_default_color_theme(app.get_color_theme())
    ui = UIRefs()
    root = root or CTk()
    ui.root = root

    root.geometry("430x800")
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    icon = PhotoImage(file="./icons/icon.png")
    root.iconphoto(True, icon)
    root.title("Milonga")
    ui.root_icon = icon

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

    eq_panel = customtkinter.CTkFrame(root, height=EQ_PANEL_COLLAPSED_HEIGHT)
    eq_panel.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
    eq_panel.pack_propagate(False)
    ui.eq_panel = eq_panel

    panel = customtkinter.CTkFrame(root)
    panel.pack(side="bottom", fill="x", padx=10, pady=10)

    ui.status_bar = customtkinter.CTkLabel(panel, text="", anchor="w", height=30)
    ui.status_bar.pack(side="left", fill="x", padx=0)

    ui.audio_settings_button = customtkinter.CTkButton(
        panel,
        text="Settings",
        width=90,
        command=app.open_audio_settings_window,
    )
    ui.audio_settings_button.pack(side="right", padx=0)

    eq_header = customtkinter.CTkFrame(eq_panel, height=40)
    eq_header.pack(side="top", fill="x", padx=8, pady=(8, 4))
    eq_header.pack_propagate(False)

    eq_title = customtkinter.CTkLabel(eq_header, text="Genre EQ", anchor="w")
    eq_title.pack(side="left", padx=(0, 8))

    genre_names = list(app.eq_staged_equalizers.keys())
    ui.eq_genre_var = tk.StringVar(value=app.current_eq_genre if app.current_eq_genre in genre_names else genre_names[0])
    eq_genre_menu = customtkinter.CTkOptionMenu(
        eq_header,
        values=genre_names,
        variable=ui.eq_genre_var,
        width=100,
        command=app.on_eq_genre_change,
    )
    eq_genre_menu.pack(side="left", padx=(0, 8))

    ui.eq_enabled_var = tk.BooleanVar(value=False)
    eq_enabled_switch = customtkinter.CTkSwitch(
        eq_header,
        text="Enable",
        variable=ui.eq_enabled_var,
        onvalue=True,
        offvalue=False,
    )
    eq_enabled_switch.pack(side="left", padx=(0, 8))

    ui.eq_toggle_button = customtkinter.CTkButton(
        eq_header,
        text="▸",
        width=28,
        command=app.toggle_eq_panel,
    )
    ui.eq_toggle_button.pack(side="right", padx=(8, 0))

    eq_flat_button = customtkinter.CTkButton(
        eq_header,
        text="Flat",
        width=68,
        command=app.set_eq_flat,
    )
    eq_flat_button.pack(side="right")

    eq_body = customtkinter.CTkFrame(eq_panel, fg_color="transparent")
    ui.eq_body = eq_body

    eq_canvas = tk.Canvas(eq_body, height=EQ_CANVAS_HEIGHT, highlightthickness=0, borderwidth=0)
    eq_scrollbar = customtkinter.CTkScrollbar(eq_body, orientation="horizontal", command=eq_canvas.xview)
    eq_canvas.configure(xscrollcommand=eq_scrollbar.set)
    eq_canvas.pack(side="top", fill="x", padx=6, pady=(0, 2))
    eq_scrollbar.pack(side="top", fill="x", padx=6, pady=(0, 6))

    eq_inner = tk.Frame(eq_canvas)
    eq_canvas_window = eq_canvas.create_window((0, 0), window=eq_inner, anchor="nw")

    def _refresh_eq_scrollregion(event):
        eq_canvas.configure(scrollregion=eq_canvas.bbox("all"))

    def _resize_eq_window(event):
        canvas_width = max(event.width, eq_inner.winfo_reqwidth())
        eq_canvas.itemconfigure(eq_canvas_window, width=canvas_width)

    eq_inner.bind("<Configure>", _refresh_eq_scrollregion)
    eq_canvas.bind("<Configure>", _resize_eq_window)

    ui.eq_band_vars = {}
    ui.eq_band_labels = {}
    for frequency in app.EQ_BAND_ORDER:
        column = tk.Frame(eq_inner, padx=2)
        column.pack(side="left", fill="y")
        tk.Label(column, text=app.EQ_BAND_DISPLAY[frequency]).pack()
        value_label = tk.Label(column, text="0 dB")
        value_label.pack(pady=(2, 4))
        band_var = tk.DoubleVar(value=0.0)
        slider = customtkinter.CTkSlider(
            column,
            from_=-12,
            to=12,
            number_of_steps=24,
            variable=band_var,
            orientation="vertical",
            height=96,
            width=16,
        )
        slider.pack()
        ui.eq_band_vars[frequency] = band_var
        ui.eq_band_labels[frequency] = value_label

    for band_var in ui.eq_band_vars.values():
        band_var.trace_add("write", lambda *args: app.on_eq_band_change())
    ui.eq_enabled_var.trace_add("write", lambda *args: app.on_eq_enabled_change())
    app.load_eq_preset(ui.eq_genre_var.get())
    app.update_eq_panel_visibility()

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
    theme_palette = app.get_treeview_palette()
    bg_color = root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"])
    text_color = root._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
    if theme_palette is not None:
        bg_color = theme_palette["background"]
        text_color = theme_palette["foreground"]

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
        fieldbackground=theme_palette["fieldbackground"] if theme_palette is not None else bg_color,
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

    ui.tree = ttk.Treeview(root, columns=columns, selectmode="extended", show="")
    ui.tree.column(columns[-1], width=20)

    vsb = customtkinter.CTkScrollbar(root, command=ui.tree.yview)
    ui.tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    ui.tree.pack(side="left", fill="both", expand=True)

    if theme_palette is None:
        ui.tree.tag_configure("play", background="yellow", foreground="blue")
        ui.tree.tag_configure("over", background="silver", foreground="white")
        ui.tree.tag_configure("cortina", foreground="red")
        ui.tree.tag_configure("vals", foreground="green")
        ui.tree.tag_configure("milonga", foreground="orange")
        ui.tree.tag_configure("default", background="#ffffff")
    else:
        ui.tree.tag_configure("play", background=theme_palette["play_bg"], foreground=theme_palette["play_fg"])
        ui.tree.tag_configure("over", background=theme_palette["over_bg"], foreground=theme_palette["over_fg"])
        ui.tree.tag_configure("cortina", foreground=theme_palette["cortina_fg"])
        ui.tree.tag_configure("vals", foreground=theme_palette["vals_fg"])
        ui.tree.tag_configure("milonga", foreground=theme_palette["milonga_fg"])
        ui.tree.tag_configure("default", background=theme_palette["default_bg"])

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
