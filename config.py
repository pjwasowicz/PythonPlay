import plistlib
import os
import re

DEBUG = False


pause_time = 1000
fade_time = 3000
target_rms = 20


default_m3u8_file_path = "default.m3u"
converted_files_file_name = "converted_files.json"

app_name = "Milonga"
library_name = "Library"
app_support_name = "Application Support"
settings_file = "milonga.plist"

current_initial_settings = dict(
                version = "1.1",
                main_grid=dict(
                    headers=["Song", ""],
                    fields=["{title}\n{album_performer}/{performer}\n{album}",
                            "{comment}"],
                ),
                volume=80,
            )


def get_rows_count_for_grid():
    settings = load_settings()
    column = settings['main_grid']['fields'][0]
    return column.count('\n')+1

def get_config_full_file_name():
    return os.path.join(get_application_support_directory(), settings_file)


def get_converted_files_full_file_name():
    return os.path.join(get_application_support_directory(), converted_files_file_name)


def get_default_playlist_full_file_name():
    return os.path.join(get_application_support_directory(), default_m3u8_file_path)


def get_application_support_directory():
    home = os.path.expanduser("~")
    dir_name = os.path.join(home, library_name, app_support_name, app_name)
    os.makedirs(dir_name, exist_ok=True)
    return dir_name


def save_settings(settings):
    fplist = get_config_full_file_name()
    with open(fplist, "wb") as fp:
        plistlib.dump(settings, fp)


def get_version_from_settings(settings):
    if 'version' in settings.keys():
        return settings['version']
    else:
        return "0.0"

def get_version():
    settings = load_settings(settings_file)
    return get_version_from_settings(settings)

def load_settings(settings_file=settings_file):
    fplist = os.path.join(get_application_support_directory(), settings_file)
    with open(fplist, "rb") as fp:
        settings = plistlib.load(fp)
    return settings




def initilize():
    config_file = get_config_full_file_name()
    if DEBUG:
        if os.path.exists(config_file):
            os.remove(config_file)

    if not os.path.exists(config_file):
        save_settings(current_initial_settings)

    settings = load_settings()
    v = get_version_from_settings(settings)
    print("Version: ", v)
    v_new = get_version_from_settings(current_initial_settings)

    if v_new != v:
        print("New version")
        save_settings(current_initial_settings)

initilize()
