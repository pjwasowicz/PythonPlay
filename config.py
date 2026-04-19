import plistlib
import os
import re
from copy import deepcopy

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
                version = "1.101",
                main_grid=dict(
                    headers=["Song", ""],
                    fields=["{title}\n{album_performer}/{performer}\n{album}",
                            "{comment}"],
                ),
                volume=80,
                color_theme="blue",
                audio_device="",
                hog_mode=False,
                genre_equalizer=dict(
                    default=dict(enabled=False, bands={"25": 0, "40": 0, "63": 0, "100": 0, "160": 0, "250": 0, "400": 0, "630": 0, "1000": 0, "1600": 0, "2500": 0, "4000": 0, "6300": 0, "10000": 0, "16000": 0}),
                    tango=dict(enabled=True, bands={"25": -4, "40": -4, "63": -3, "100": -2, "160": -2, "250": -1, "400": 0, "630": 0, "1000": 1, "1600": 1, "2500": 2, "4000": 2, "6300": 1, "10000": 0, "16000": -1}),
                    milonga=dict(enabled=True, bands={"25": -3, "40": -3, "63": -2, "100": -1, "160": -1, "250": 0, "400": 0, "630": 0, "1000": 1, "1600": 1, "2500": 2, "4000": 2, "6300": 1, "10000": 0, "16000": -1}),
                    vals=dict(enabled=True, bands={"25": -3, "40": -3, "63": -2, "100": -1, "160": -1, "250": 0, "400": 0, "630": 0, "1000": 1, "1600": 1, "2500": 1, "4000": 1, "6300": 0, "10000": 0, "16000": -1}),
                    cortina=dict(enabled=False, bands={"25": 0, "40": 0, "63": 0, "100": 0, "160": 0, "250": 0, "400": 0, "630": 0, "1000": 0, "1600": 0, "2500": 0, "4000": 0, "6300": 0, "10000": 0, "16000": 0}),
                ),
            )

legacy_genre_equalizer = dict(
    default=dict(enabled=False, bands={"25": 0, "40": 0, "63": 0, "100": 0, "160": 0, "250": 0, "400": 0, "630": 0, "1000": 0, "1600": 0, "2500": 0, "4000": 0, "6300": 0, "10000": 0, "16000": 0}),
    tango=dict(enabled=True, bands={"25": -4, "40": -4, "63": -3, "100": -2, "160": -2, "250": -1, "400": 0, "630": 0, "1000": 1, "1600": 1, "2500": 2, "4000": 2, "6300": 1, "10000": 0, "16000": -1}),
    milonga=dict(enabled=True, bands={"25": -3, "40": -3, "63": -2, "100": -1, "160": -1, "250": 0, "400": 0, "630": 0, "1000": 1, "1600": 1, "2500": 2, "4000": 2, "6300": 1, "10000": 0, "16000": -1}),
    vals=dict(enabled=True, bands={"25": -3, "40": -3, "63": -2, "100": -1, "160": -1, "250": 0, "400": 0, "630": 0, "1000": 1, "1600": 1, "2500": 1, "4000": 1, "6300": 0, "10000": 0, "16000": -1}),
    cortina=dict(enabled=False, bands={"25": 0, "40": 0, "63": 0, "100": 0, "160": 0, "250": 0, "400": 0, "630": 0, "1000": 0, "1600": 0, "2500": 0, "4000": 0, "6300": 0, "10000": 0, "16000": 0}),
)

enhanced_genre_equalizer = dict(
    default=dict(enabled=False, bands={"25": 0, "40": 0, "63": 0, "100": 0, "160": 0, "250": 0, "400": 0, "630": 0, "1000": 0, "1600": 0, "2500": 0, "4000": 0, "6300": 0, "10000": 0, "16000": 0}),
    tango=dict(enabled=True, bands={"25": -10, "40": -9, "63": -7, "100": -5, "160": -3, "250": -2, "400": 0, "630": 1, "1000": 2, "1600": 3, "2500": 4, "4000": 4, "6300": 2, "10000": -1, "16000": -5}),
    milonga=dict(enabled=True, bands={"25": -8, "40": -7, "63": -5, "100": -3, "160": -1, "250": 1, "400": 2, "630": 2, "1000": 3, "1600": 4, "2500": 5, "4000": 4, "6300": 2, "10000": -1, "16000": -4}),
    vals=dict(enabled=True, bands={"25": -7, "40": -6, "63": -4, "100": -2, "160": -1, "250": 0, "400": 1, "630": 1, "1000": 2, "1600": 2, "2500": 3, "4000": 2, "6300": 1, "10000": -1, "16000": -3}),
    cortina=dict(enabled=False, bands={"25": 0, "40": 0, "63": 0, "100": 0, "160": 0, "250": 0, "400": 0, "630": 0, "1000": 0, "1600": 0, "2500": 0, "4000": 0, "6300": 0, "10000": 0, "16000": 0}),
)

current_initial_settings["genre_equalizer"] = deepcopy(enhanced_genre_equalizer)


def merge_settings(defaults, current):
    merged = defaults.copy()
    for key, value in current.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged


def _same_equalizer_preset(current_preset, reference_preset):
    if bool(current_preset.get("enabled", False)) != bool(reference_preset.get("enabled", False)):
        return False

    current_bands = current_preset.get("bands", {})
    reference_bands = reference_preset.get("bands", {})
    for band, reference_value in reference_bands.items():
        if float(current_bands.get(band, 0)) != float(reference_value):
            return False
    return True


def migrate_genre_equalizer(settings):
    equalizers = settings.get("genre_equalizer", {})
    changed = False

    for genre_name, legacy_preset in legacy_genre_equalizer.items():
        current_preset = equalizers.get(genre_name)
        if current_preset and _same_equalizer_preset(current_preset, legacy_preset):
            equalizers[genre_name] = deepcopy(enhanced_genre_equalizer[genre_name])
            changed = True

    if changed:
        settings["genre_equalizer"] = equalizers

    return settings


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
    return get_version_from_settings(current_initial_settings)

def load_settings(settings_file=settings_file):
    fplist = os.path.join(get_application_support_directory(), settings_file)
    with open(fplist, "rb") as fp:
        settings = plistlib.load(fp)
    merged = merge_settings(current_initial_settings, settings)
    return migrate_genre_equalizer(merged)


def get_genre_equalizer_settings(genre):
    settings = load_settings()
    equalizers = settings.get("genre_equalizer", {})
    default_eq = equalizers.get("default", {"enabled": False, "bands": {"25": 0, "40": 0, "63": 0, "100": 0, "160": 0, "250": 0, "400": 0, "630": 0, "1000": 0, "1600": 0, "2500": 0, "4000": 0, "6300": 0, "10000": 0, "16000": 0}})
    normalized_genre = (genre or "").strip().lower()

    for key, eq_settings in equalizers.items():
        if key == "default":
            continue
        if key in normalized_genre:
            merged = {
                "enabled": eq_settings.get("enabled", default_eq.get("enabled", False)),
                "bands": default_eq.get("bands", {}).copy(),
            }
            merged["bands"].update(eq_settings.get("bands", {}))
            return merged

    return {
        "enabled": default_eq.get("enabled", False),
        "bands": default_eq.get("bands", {}).copy(),
    }


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
        save_settings(merge_settings(current_initial_settings, settings))
    else:
        save_settings(settings)
