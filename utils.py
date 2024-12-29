from tkinter import *
from PIL import Image, ImageTk
import subprocess

def convert_to_mp3_with_tags(input_file, output_file):

    ffmpeg_command = [
        'ffmpeg',
        '-i', input_file,
        output_file
    ]

    subprocess.run(ffmpeg_command, check=True)


def get_files_from_tree(tree,songs):
    files = []
    for item_id in tree.get_children():
        files.append(songs[item_id])
    return files


def load_and_resize_image(file, size=(32,32)):
    image = Image.open(file)  # Załaduj obraz
    image_resized = image.resize(size)  # Przeskaluj obraz
    return ImageTk.PhotoImage(image_resized)

import os
def get_libraries():
# Uruchomienie lsof i filtrowanie bibliotek z /Users/pawel
    output = os.popen("lsof | grep dylib | grep '/Users/pawel'").read()

    # Wyodrębnienie unikalnych katalogów
    directories = set()
    for line in output.splitlines():
        # Załóż, że ścieżka jest ostatnią kolumną
        path = line.split()[-1]
        directory = os.path.dirname(path)
        directories.add(directory)

    # Wyświetlenie unikalnych katalogów
    #print("Katalogi z bibliotekami dylib:")
    res = []
    for directory in sorted(directories):
        directory = os.path.relpath(directory, "")
        res.append(directory)
    res=str(res)
    res = "resources_dirs = {res}".format(res=res)

    with open("libs.py", "w") as file:
        file.write(res)
    print(res)

