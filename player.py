import pygame
import pyloudnorm as pyln
import config
import os
import utils
import uuid
import json
import numpy as np
from scipy.signal import butter, lfilter
import tempfile
import wave
import time
import re
import threading
from io import BytesIO
import global_vars
import tkinter as tk
import matplotlib
import pygame._sdl2.audio as sdl2_audio
import matplotlib.pyplot as plt
from PIL import Image


matplotlib.use("Agg")



tmp_files = []

current_duration = 0
loudnes_correction = 0

start_pos = 0

allowed_files = [".mp3", ".ogg", ".aif", ".aiff", ".m4a", ".flac"]

converted_files = {}

current_volume = 0.0



loudnes_table = {}


def delete_tmp_files():
    global tmp_files
    for file in tmp_files:
        os.remove(file)
        print("Deleted file:", file)
    tmp_files = []


def remove_converted_file_from_list(name):
    global converted_files
    del converted_files[name]


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
        else:
            new_sound_file = str(uuid.uuid4()) + ".mp3"
            new_file = os.path.join(
                config.get_application_support_directory(), new_sound_file
            )
            utils.convert_to_mp3_with_tags(file_path, new_file)
            converted_files[new_file] = file_path
            return new_file
    except Exception as e:
        print("Cannot load: ", file_path, e)
        return None


def quit_device():
    pygame.mixer.quit()


def set_device(selected_device):
    pygame.mixer.quit()
    pygame.mixer.init(devicename=selected_device)
    print("Device set:", selected_device)


def get_devices(capture_devices: bool = False):
    devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
    return devices


def pcm_to_float(pcm_data, bit_depth=16):
    max_value = float(2 ** (bit_depth - 1))
    return pcm_data.astype(np.float32) / max_value


def get_loudness(data, rate):
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(pcm_to_float(data))
    return loudness


def set_volume(volume):
    global current_volume
    current_volume = volume
    v = volume * get_loudness_corretion()
    if v > 1:
        v = 1
    pygame.mixer.music.set_volume(v)


def pause():
    pygame.mixer.music.pause()


def unpause():
    pygame.mixer.unpause()


def init_player():
    pygame.mixer.init()


def reset_progress():
    global current_duration
    global start_pos
    current_duration = 0
    start_pos = 0


def get_loudness_corretion():
    return loudnes_correction


def get_progress():
    global current_duration
    global start_pos
    if current_duration > 0:
        pos = get_pos()
        return (pos + start_pos) / (current_duration * 1000)
    else:
        return 0


def get_pos():
    return pygame.mixer_music.get_pos()


def get_start_pos():
    return start_pos


def get_duration():
    return current_duration * 1000


def fade():
    pygame.mixer.music.fadeout(config.fade_time)


def stop():
    pygame.mixer.music.stop()


def decode_mp3_to_pcm(input_mp3_path):
    from pydub import AudioSegment

    audio = AudioSegment.from_file(input_mp3_path)
    audio = audio.set_frame_rate(44100).set_channels(2)
    return audio


def db_to_amplitude(db):
    return 10 ** (db / 20)


def apply_band_filter(data, sample_rate, low_frequency=10, high_frequency=20000):
    nyquist = 0.5 * sample_rate
    low_cutoff = low_frequency / nyquist
    high_cutoff = high_frequency / nyquist
    b, a = butter(5, [low_cutoff, high_cutoff], btype="band", analog=False)
    filtered_data = lfilter(b, a, data)
    return filtered_data


def low_pass_filter(data, sample_rate, cutoff_freq):
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(5, normal_cutoff, btype="low", analog=False)
    filtered_data = lfilter(b, a, data)
    return filtered_data


oimage = None


def make_wave(pcm_data, sample_rate):
    global oimage
    global_canvas = global_vars.wave_canvas
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
    loudness = get_loudness(pcm_data, sample_rate)
    return loudness


def detect_silence_start_end_from_file(file, min_silence_len, silence_tresh):
    audio_segment = decode_mp3_to_pcm(file)
    return utils.detect_silence_start_end(audio_segment, min_silence_len, silence_tresh)


def play_from_file(
    file,
    pos=0,
    normalize_volume=True,
    low_frequency=10,
    high_frequency=20000,
    song_id=None,
    files=None,
):
    global tmp_files
    global current_volume
    global loudnes_correction
    global current_duration
    global start_pos

    start_time = time.time()

    num_channels = 2
    sample_width = 2

    audio_segment = decode_mp3_to_pcm(file)

    data = files[song_id]
    if len(data) > 2:
        start_cut = data[3]
        end_cut = data[4]

    else:
        print("Extra cut for file:", file)
        start_cut, end_cut = utils.detect_silence_start_end(audio_segment, 200, -56)
    print("Cut: ", start_cut, end_cut)

    audio_segment = audio_segment[start_cut:end_cut]

    sample_rate = audio_segment.frame_rate
    pcm_data = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)

    def worker():
        make_wave(pcm_data, sample_rate)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    left_channel = pcm_data[0::2]
    right_channel = pcm_data[1::2]

    filtered_left = low_pass_filter(left_channel, sample_rate, high_frequency)
    filtered_right = low_pass_filter(right_channel, sample_rate, high_frequency)

    filtered_audio = np.empty(
        (filtered_left.size + filtered_right.size,), dtype=np.int16
    )

    filtered_audio[0::2] = filtered_left
    filtered_audio[1::2] = filtered_right

    if normalize_volume:

        data = files[song_id]
        if len(data) > 2:
            l = data[2]
        else:
            print("Extra loudness for file:", file)
            l = get_loudness(pcm_data, sample_rate)

        target_lufs = -20
        difference = target_lufs - l

        scaling_factor = 10 ** (difference / 20.0)

        new_volume = scaling_factor * current_volume
        if new_volume > 1:
            new_volume = 1

        loudnes_correction = scaling_factor

        print("Volume:", current_volume, new_volume, scaling_factor, l)

        pygame.mixer.music.set_volume(new_volume)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file_path = temp_file.name

        with wave.open(temp_file, "wb") as output_wav:
            output_wav.setnchannels(num_channels)  # Stereo
            output_wav.setsampwidth(sample_width)  # 16-bitowe dane
            output_wav.setframerate(sample_rate)
            trim_audio = filtered_audio.tobytes()
            output_wav.writeframes(trim_audio)

    audio_length_in_bytes = len(trim_audio)
    duration_seconds = audio_length_in_bytes / (
        sample_rate * num_channels * sample_width
    )

    pygame.mixer.music.load(temp_file_path)
    end_time = time.time()

    delete_tmp_files()
    tmp_files.append(temp_file_path)

    current_duration = duration_seconds
    start_pos = start_pos + pos
    pos = pos / 1000

    fade_time = 0
    if pos > 0:
        fade_time = config.fade_time
    pygame.mixer.music.play(fade_ms=fade_time, start=pos)

    print(f"Encoding time: {end_time - start_time:.4f} s")

    return duration_seconds


def extract_h_value(input_string, default_value=20000):
    match = re.search(r"h:(\d+)", input_string.lower())
    if match:
        return int(match.group(1))
    else:
        return default_value


def play_from_list(song_id, songs, pos=0):
    if song_id is not None:
        file = songs[song_id][0]
        tags = songs[song_id][1]
        comment = ""
        if "comment" in tags.keys():
            comment = tags["comment"]

        high_frequency = extract_h_value(comment)
        print("High frequency: ", high_frequency)

        try:
            play_from_file(
                file,
                pos=pos,
                normalize_volume=True,
                low_frequency=10,
                high_frequency=high_frequency,
                song_id=song_id,
                files=songs,
            )
        except Exception as e:
            print("Error: ", str(e))
        print("Playing: ", song_id, file)


def get_busy():
    return pygame.mixer.music.get_busy()
