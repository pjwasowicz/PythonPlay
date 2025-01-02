import m3u8
from pymediainfo import MediaInfo
import os

import player
from config import DEBUG
from player import converted_files

import urllib.parse

from urllib.parse import quote
def save_to_m3u8(files, output_path, save_external=False):
    with open(output_path, "w") as f:
        f.write("#EXTM3U\n")
        converted_files = player.get_converted_files()
        # Iteruj przez listę plików
        for file, _ in files:
            file_name = file

            if save_external:
                if file in converted_files.keys():
                    file_name = converted_files[file]

            normalized_path = os.path.normpath(file_name)

            unix_style_path = normalized_path.replace("\\", "/")

            encoded_path = quote(unix_style_path, safe=":/")


            url = f"file:///{encoded_path}"

            f.write(f"#EXTINF:-1,{url}\n")
            f.write(f"{url}\n")


def save_to_m3u8x(files, output_path):
    playlist = m3u8.M3U8()
    for file in files:
        segment = m3u8.Segment(uri=file)
        playlist.segments.append(segment)
    with open(output_path, "w") as f:
        f.write(playlist.dumps())

def save_m3u(files, output_path, save_external=False):
    with open(output_path, "w", encoding="utf-8") as f:
        for file in files:
            fname = file[0]

            if save_external:
                if fname in converted_files.keys():
                    fname = converted_files[file]

            f.write(f"{fname}\n")

def read_m3u(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        cleaned_lines = [line.strip() for line in lines]
    return cleaned_lines

def get_all_tags(file_path):
    try:
        media_info = MediaInfo.parse(file_path)
        tags = {}
        for track in media_info.tracks:
            # Zbieramy wszystkie dostępne tagi dla każdej ścieżki
            for key, value in track.to_data().items():
                tags[key] = value
        if "title" not in tags.keys():
            tags["title"] = tags["file_name"]
        return tags
    except Exception as e:
        print(f"Nie można odczytać tagów z pliku {file_path}: {e}")
        return {}


def get_audio_tags_from_m3u8(m3u8_file):
    if not os.path.exists(m3u8_file):
        return None

    songs = read_m3u(m3u8_file)

    tags_list = []

    for file_path in songs:
        normalized_path = os.path.normpath(file_path)

        if os.path.exists(normalized_path):
            tags = get_all_tags(normalized_path)
            tags_list.append({normalized_path: tags})
        else:
            print(f"Plik nie istnieje: {normalized_path}")

    return tags_list



def get_audio_tags_from_m3u8_x(m3u8_file):
    if not os.path.exists(m3u8_file):
        return None
    playlist = m3u8.load(m3u8_file)
    tags_list = []

    for segment in playlist.segments:
        file_path = segment.uri
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.path.dirname(m3u8_file), file_path)
        file_path = os.path.abspath(file_path)
        if os.path.exists(file_path):
            tags = get_all_tags(file_path)
            tags_list.append({file_path: tags})
        else:
            print(f"Plik nie istnieje: {file_path}")

    return tags_list