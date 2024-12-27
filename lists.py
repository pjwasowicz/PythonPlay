import m3u8
from pymediainfo import MediaInfo
import os
from config import DEBUG

def save_to_m3u8(files, output_path):
    with open(output_path, 'w') as f:
        # Zapisz nagłówek M3U8
        f.write("#EXTM3U\n")

        # Iteruj przez listę plików
        for file, _ in files:

            # Możesz dodać dodatkowe informacje przed plikiem, jak np. czas trwania
            # Zapisz każdy plik w formacie M3U8
            f.write(f"#EXTINF:-1,{file}\n")
            f.write(f"{file}\n")

def save_to_m3u8_x(files, output_path):
    playlist = m3u8.M3U8()
    for file in files:
        segment = m3u8.Segment(uri=file)
        playlist.segments.append(segment)
    with open(output_path, 'w') as f:
        f.write(playlist.dumps())



def get_all_tags(file_path):
    """Zwraca wszystkie dostępne tagi dla pliku audio."""
    print(file_path)
    try:
        media_info = MediaInfo.parse(file_path)
        tags = {}
        for track in media_info.tracks:
            # Zbieramy wszystkie dostępne tagi dla każdej ścieżki
            for key, value in track.to_data().items():
                tags[key] = value
                #if DEBUG:
                #    print(key,value)
        return tags
    except Exception as e:
        print(f"Nie można odczytać tagów z pliku {file_path}: {e}")
        return {}

def get_audio_tags_from_m3u8(m3u8_file):
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




