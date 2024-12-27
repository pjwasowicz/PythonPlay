import tkinter as tk
from tkinter import messagebox

rows = 5  # Początkowa liczba wierszy
columns = 2  # Siatka ma 2 kolumny

def open_config_window():
    global rows
    global columns

    config_window = tk.Toplevel(root)
    config_window.title("Siatka konfiguracyjna")

    # Frame, który będzie trzymał siatkę i pasek przewijania
    canvas = tk.Canvas(config_window)
    scroll_y = tk.Scrollbar(config_window, orient="vertical", command=canvas.yview)
    scroll_x = tk.Scrollbar(config_window, orient="horizontal", command=canvas.xview)
    scrollable_frame = tk.Frame(canvas)

    # Konfiguracja paska przewijania
    canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.grid(row=1, column=1, sticky="ns")
    scroll_x.grid(row=2, column=0, sticky="ew")
    canvas.grid(row=1, column=0, sticky="nsew")
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Funkcja tworząca dynamiczną siatkę z Entry
    grid_entries = []
    def create_grid():
        """Tworzy siatkę w ramce scrollowalnej."""
        for row in range(rows):
            row_entries = []
            for col in range(columns):
                entry = tk.Entry(scrollable_frame)
                entry.grid(row=row, column=col, padx=5, pady=5)
                row_entries.append(entry)
            grid_entries.append(row_entries)

    # Funkcja dodająca nowy wiersz do siatki
    def add_row():
        global rows
        rows += 1
        row_entries = []
        for col in range(columns):
            entry = tk.Entry(scrollable_frame)
            entry.grid(row=rows - 1, column=col, padx=5, pady=5)
            row_entries.append(entry)
        grid_entries.append(row_entries)
        canvas.config(scrollregion=canvas.bbox("all"))

    # Funkcja dodająca nową kolumnę do siatki
    def add_column():
        global columns
        columns += 1
        for row in range(rows):
            entry = tk.Entry(scrollable_frame)
            entry.grid(row=row, column=columns - 1, padx=5, pady=5)
            grid_entries[row].append(entry)
        canvas.config(scrollregion=canvas.bbox("all"))

    # Funkcja zapisująca dane z siatki
    def save_config():
        data = []
        for row in grid_entries:
            row_data = [entry.get() for entry in row]
            data.append(row_data)
        print("Wprowadzone dane:")
        for row in data:
            print(row)
        messagebox.showinfo("Zapisano", "Dane zostały zapisane!")

    # Funkcja anulująca
    def cancel_config():
        config_window.destroy()

    # Przyciski nad siatką
    button_frame = tk.Frame(config_window)
    button_frame.grid(row=0, column=0, columnspan=2, pady=10)

    add_row_button = tk.Button(button_frame, text="Dodaj wiersz", command=add_row)
    add_row_button.grid(row=0, column=0, padx=5)

    add_column_button = tk.Button(button_frame, text="Dodaj kolumnę", command=add_column)
    add_column_button.grid(row=0, column=1, padx=5)

    save_button = tk.Button(config_window, text="Zapisz", command=save_config)
    save_button.grid(row=3, column=0, columnspan=2, pady=10)

    cancel_button = tk.Button(config_window, text="Anuluj", command=cancel_config)
    cancel_button.grid(row=rows + 2, column=0, columnspan=2, pady=10)

    # Tworzymy początkową siatkę
    create_grid()

    # Ustawiamy region przewijania
    canvas.config(scrollregion=canvas.bbox("all"))

def create_menu():
    """Tworzy menu w głównym oknie aplikacji."""
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    config_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Menu", menu=config_menu)
    config_menu.add_command(label="Konfiguracja", command=open_config_window)
    config_menu.add_separator()
    config_menu.add_command(label="Exit", command=root.quit)

# Główne okno aplikacji
root = tk.Tk()
root.title("Main Window")

# Tworzenie menu
create_menu()

# Uruchomienie aplikacji
root.mainloop()
