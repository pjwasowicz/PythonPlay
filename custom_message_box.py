import customtkinter as ctk

is_active = False
def custom_messagebox_panel(parent, message, show_cancel = False):
    global is_active

    if is_active:
        return
    is_active = True

    can_close = False
    result = None
    panel = ctk.CTkFrame(parent, fg_color="darkgray", corner_radius=0, height=150)
    panel.pack(fill="x", side="top")

    message_label = ctk.CTkLabel(panel, text=message, font=("Arial", 14), text_color="white")
    message_label.pack(pady=(10, 0))
    def on_ok():
        nonlocal can_close
        nonlocal result
        result = True
        panel.pack_forget()
        can_close = True


    def on_cancel():
        nonlocal result
        nonlocal can_close
        result = False
        panel.pack_forget()
        can_close = True


    button_frame = ctk.CTkFrame(panel, fg_color="transparent")
    button_frame.pack(pady=(10, 10))

    ok_button = ctk.CTkButton(button_frame, text="OK", command=on_ok)
    ok_button.grid(row=0, column=0, padx=10)

    if show_cancel:
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=on_cancel)
        cancel_button.grid(row=0, column=1, padx=10)


    parent.grab_set()

    while not can_close:
        parent.update_idletasks()
        parent.after(100)
        parent.update()

    parent.grab_release()
    is_active = False
    return result


