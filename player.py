import json
import math
import os
import re
import tempfile
import threading
import time
import uuid
import wave
from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pygame
import pygame._sdl2.audio as sdl2_audio
import pyloudnorm as pyln
from PIL import Image
from scipy.signal import butter, lfilter

import config
import global_vars
import utils


matplotlib.use("Agg")


tmp_files = []

current_duration = 0
loudnes_correction = 1.0

start_pos = 0

allowed_files = [".mp3", ".ogg", ".aif", ".aiff", ".m4a", ".flac"]

converted_files = {}

current_volume = 0.0
_live_playback_context = None


def is_initialized():
    return pygame.mixer.get_init() is not None


def delete_tmp_files():
    global tmp_files
    for file in tmp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print("Deleted file:", file)
        except OSError as e:
            print("Cannot delete tmp file:", file, e)
    tmp_files = []


def remove_converted_file_from_list(name):
    global converted_files
    converted_files.pop(name, None)


def load_converted_files():
    global converted_files
    file_name = config.get_converted_files_full_file_name()
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            converted_files = json.load(file)


def get_converted_files():
    return converted_files


def save_converted_files():
    file_name = config.get_converted_files_full_file_name()
    with open(file_name, "w") as file:
        json.dump(converted_files, file, indent=4)


def can_load_sound(file_path):
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()
        if extension in allowed_files:
            return file_path
        new_sound_file = str(uuid.uuid4()) + ".mp3"
        new_file = os.path.join(config.get_application_support_directory(), new_sound_file)
        utils.convert_to_mp3_with_tags(file_path, new_file)
        converted_files[new_file] = file_path
        return new_file
    except Exception as e:
        print("Cannot load: ", file_path, e)
        return None


def quit_device():
    if is_initialized():
        pygame.mixer.quit()


def set_device(selected_device):
    if is_initialized():
        pygame.mixer.quit()
    pygame.mixer.init(devicename=selected_device)
    pygame.mixer.music.set_volume(current_volume)
    print("Device set:", selected_device)


def get_devices(capture_devices: bool = False):
    return tuple(sdl2_audio.get_audio_device_names(capture_devices))


def pcm_to_float(pcm_data, bit_depth=16):
    max_value = float(2 ** (bit_depth - 1))
    return pcm_data.astype(np.float32) / max_value


def get_loudness(data, rate):
    meter = pyln.Meter(rate)
    return meter.integrated_loudness(pcm_to_float(data))


def set_volume(volume):
    global current_volume
    current_volume = volume
    v = volume * get_loudness_corretion()
    if v > 1:
        v = 1
    if is_initialized():
        pygame.mixer.music.set_volume(v)


def pause():
    if is_initialized():
        pygame.mixer.music.pause()


def unpause():
    if is_initialized():
        pygame.mixer.unpause()


def init_player():
    if not is_initialized():
        pygame.mixer.init()


def reset_progress():
    global current_duration, start_pos
    current_duration = 0
    start_pos = 0


def get_loudness_corretion():
    return loudnes_correction


def get_loudness_corretion_db():
    if loudnes_correction <= 0:
        return -100
    return 20 * math.log10(loudnes_correction)


def get_progress():
    global current_duration, start_pos
    if current_duration > 0:
        pos = get_pos()
        return (pos + start_pos) / (current_duration * 1000)
    return 0


def get_pos():
    return pygame.mixer.music.get_pos()


def get_start_pos():
    return start_pos


def get_duration():
    return current_duration * 1000


def fade():
    if is_initialized():
        pygame.mixer.music.fadeout(config.fade_time)


def stop():
    if is_initialized():
        pygame.mixer.music.stop()


def decode_mp3_to_pcm(input_mp3_path):
    from pydub import AudioSegment

    return AudioSegment.from_file(input_mp3_path).set_frame_rate(44100).set_channels(2)


def low_pass_filter(data, sample_rate, cutoff_freq):
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(5, normal_cutoff, btype="low", analog=False)
    return lfilter(b, a, data)


def peaking_eq_filter(data, sample_rate, center_freq, gain_db, q=1.0):
    if abs(gain_db) < 0.01:
        return data

    nyquist = sample_rate / 2
    clamped_freq = max(20.0, min(float(center_freq), nyquist - 1))
    omega = 2 * math.pi * clamped_freq / sample_rate
    alpha = math.sin(omega) / (2 * q)
    amplitude = math.pow(10, gain_db / 40.0)
    cos_omega = math.cos(omega)

    b0 = 1 + alpha * amplitude
    b1 = -2 * cos_omega
    b2 = 1 - alpha * amplitude
    a0 = 1 + alpha / amplitude
    a1 = -2 * cos_omega
    a2 = 1 - alpha / amplitude

    b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
    a = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)
    return lfilter(b, a, data)


def apply_graphic_equalizer(data, sample_rate, eq_settings):
    if not eq_settings or not eq_settings.get("enabled", False):
        return data

    bands = eq_settings.get("bands", {})
    if not bands:
        return data

    ordered_bands = sorted((float(freq), float(gain)) for freq, gain in bands.items())
    equalized = data.astype(np.float64)

    for index, (center_freq, gain_db) in enumerate(ordered_bands):
        lower_freq = ordered_bands[index - 1][0] if index > 0 else center_freq / 2
        upper_freq = ordered_bands[index + 1][0] if index < len(ordered_bands) - 1 else center_freq * 2
        bandwidth = max(1.0, upper_freq - lower_freq)
        q = max(0.35, center_freq / bandwidth)
        equalized = peaking_eq_filter(equalized, sample_rate, center_freq, gain_db, q=q)

    peak = np.max(np.abs(equalized)) if len(equalized) else 0
    if peak > 32767:
        equalized = equalized * (32767.0 / peak)

    return np.clip(equalized, -32768, 32767).astype(np.int16)


def make_wave(pcm_data, sample_rate):
    global_canvas = global_vars.wave_canvas
    if global_canvas is None:
        return

    plt.figure(figsize=(15, 5))
    step = 10
    times = np.linspace(0, len(pcm_data) / sample_rate, num=len(pcm_data))[::step]
    pcm_data_reduced = pcm_data[::step]

    plt.plot(times, pcm_data_reduced)
    plt.axis("off")
    plt.subplots_adjust(left=0, right=1)
    plt.xlim(times[0], times[-1])
    plt.ylim(-33000, 33000)
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img = Image.open(buf)

    canvas_width = global_canvas.winfo_width()
    canvas_height = global_canvas.winfo_height()
    img = img.resize((canvas_width, canvas_height))
    global_vars.canvas_image = img

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        temp_filename = tmpfile.name
        img.save(temp_filename)

    buf.close()
    plt.clf()
    plt.close()
    global_vars.wave_queue.put(temp_filename)


def get_loudness_from_file(file):
    audio_segment = decode_mp3_to_pcm(file)
    sample_rate = audio_segment.frame_rate
    pcm_data = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
    return get_loudness(pcm_data, sample_rate)


def detect_silence_start_end_from_file(file, min_silence_len, silence_tresh):
    audio_segment = decode_mp3_to_pcm(file)
    return utils.detect_silence_start_end(audio_segment, min_silence_len, silence_tresh)


def play_from_file(
    file,
    pos=0,
    normalize_volume=True,
    low_frequency=10,
    high_frequency=20000,
    eq_settings=None,
    song_id=None,
    files=None,
    update_wave=True,
):
    global tmp_files, current_volume, loudnes_correction, current_duration, start_pos, _live_playback_context

    start_time = time.time()

    num_channels = 2
    sample_width = 2

    audio_segment = decode_mp3_to_pcm(file)
    data = files[song_id]
    if len(data) > 4:
        start_cut = data[3]
        end_cut = data[4]
    else:
        print("Extra cut for file:", file)
        start_cut, end_cut = utils.detect_silence_start_end(audio_segment, 200, -56)
    print("Cut: ", start_cut, end_cut)

    audio_segment = audio_segment[start_cut:end_cut]

    sample_rate = audio_segment.frame_rate
    pcm_data = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)

    if update_wave:
        thread = threading.Thread(target=lambda: make_wave(pcm_data, sample_rate), daemon=True)
        thread.start()

    left_channel = pcm_data[0::2]
    right_channel = pcm_data[1::2]

    filtered_left = low_pass_filter(left_channel, sample_rate, high_frequency)
    filtered_right = low_pass_filter(right_channel, sample_rate, high_frequency)

    filtered_left = apply_graphic_equalizer(filtered_left, sample_rate, eq_settings)
    filtered_right = apply_graphic_equalizer(filtered_right, sample_rate, eq_settings)

    filtered_audio = np.empty((filtered_left.size + filtered_right.size,), dtype=np.int16)
    filtered_audio[0::2] = filtered_left
    filtered_audio[1::2] = filtered_right

    if normalize_volume:
        if len(data) > 2:
            loudness = data[2]
        else:
            print("Extra loudness for file:", file)
            loudness = get_loudness(pcm_data, sample_rate)

        target_lufs = -20
        difference = target_lufs - loudness
        scaling_factor = 10 ** (difference / 20.0)

        new_volume = scaling_factor * current_volume
        if new_volume > 1:
            new_volume = 1

        loudnes_correction = scaling_factor
        print("Volume:", current_volume, new_volume, scaling_factor, loudness)
        pygame.mixer.music.set_volume(new_volume)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file_path = temp_file.name
        with wave.open(temp_file, "wb") as output_wav:
            output_wav.setnchannels(num_channels)
            output_wav.setsampwidth(sample_width)
            output_wav.setframerate(sample_rate)
            trim_audio = filtered_audio.tobytes()
            output_wav.writeframes(trim_audio)

    audio_length_in_bytes = len(trim_audio)
    duration_seconds = audio_length_in_bytes / (sample_rate * num_channels * sample_width)

    pygame.mixer.music.load(temp_file_path)
    end_time = time.time()

    delete_tmp_files()
    tmp_files.append(temp_file_path)

    current_duration = duration_seconds
    start_pos = pos
    pos = pos / 1000

    fade_time = config.fade_time if pos > 0 else 0
    pygame.mixer.music.play(fade_ms=fade_time, start=pos)

    _live_playback_context = {
        "file": file,
        "song_id": song_id,
        "files": files,
        "normalize_volume": normalize_volume,
        "low_frequency": low_frequency,
        "high_frequency": high_frequency,
        "eq_settings": eq_settings,
    }

    print(f"Encoding time: {end_time - start_time:.4f} s")
    return duration_seconds


def extract_h_value(input_string, default_value=20000):
    match = re.search(r"h:(\d+)", input_string.lower())
    if match:
        return int(match.group(1))
    return default_value


def play_from_list(song_id, songs, pos=0):
    if song_id is not None:
        file = songs[song_id][0]
        tags = songs[song_id][1]
        genre = tags.get("genre", "")
        comment = tags.get("comment", "")

        high_frequency = extract_h_value(comment)
        eq_settings = config.get_genre_equalizer_settings(genre)
        print("High frequency: ", high_frequency)
        print("Genre EQ:", genre, eq_settings)

        try:
            play_from_file(
                file,
                pos=pos,
                normalize_volume=True,
                low_frequency=10,
                high_frequency=high_frequency,
                eq_settings=eq_settings,
                song_id=song_id,
                files=songs,
            )
        except Exception as e:
            print("Error: ", str(e))
        print("Playing: ", song_id, file)


def update_live_eq(eq_settings):
    global _live_playback_context

    if not _live_playback_context or not get_busy():
        return

    pos = max(0, get_pos() + get_start_pos())
    context = dict(_live_playback_context)
    context["eq_settings"] = eq_settings
    _live_playback_context = context

    play_from_file(
        context["file"],
        pos=pos,
        normalize_volume=context["normalize_volume"],
        low_frequency=context["low_frequency"],
        high_frequency=context["high_frequency"],
        eq_settings=context["eq_settings"],
        song_id=context["song_id"],
        files=context["files"],
        update_wave=False,
    )


def get_busy():
    if not is_initialized():
        return False
    return pygame.mixer.music.get_busy()
