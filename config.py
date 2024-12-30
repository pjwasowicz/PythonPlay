import plistlib
import os

from player import converted_files

DEBUG = False

pause_time = 3000
fade_time = 3000
target_rms = 20


default_m3u8_file_path = "default.m3u8"
converted_files_file_name = "converted_files.json"

app_name = 'Milonga'
library_name = "Library"
app_support_name = "Application Support"
settings_file = "milonga.plist"

def get_config_full_file_name():
    return os.path.join(get_application_support_directory(), settings_file)

def get_converted_files_full_file_name():
    return os.path.join(get_application_support_directory(), converted_files_file_name)

def get_default_playlist_full_file_name():
    return os.path.join(get_application_support_directory(), default_m3u8_file_path)

def get_application_support_directory():
    home = os.path.expanduser("~")
    dir_name =  os.path.join(home, library_name,app_support_name , app_name)
    os.makedirs(dir_name, exist_ok=True)
    return dir_name

def save_settings(settings):
    fplist = get_config_full_file_name()
    with open(fplist, 'wb') as fp:
        plistlib.dump(settings, fp)

def load_settings(settings_file=settings_file):
    fplist = os.path.join(get_application_support_directory(), settings_file)
    with open(fplist, 'rb') as fp:
        settings = plistlib.load(fp)
    return settings

def initilize():
    config_file = get_config_full_file_name()
    ####Do celów testowych config zakłada się za każadym razem
    if DEBUG:
        if os.path.exists(config_file):
            os.remove(config_file)

    if not os.path.exists(config_file):
        settings = dict(
            main_grid = dict(
                headers = ["Name","Artits","Performer","Album","Comment"],
                fields =  ["title","album_performer","performer","album","comment"]
            ),
            volume = 80
        )
        save_settings(settings)



initilize()

