import json
import math
import os
import re
import tempfile
import threading
import time
import uuid
from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pyloudnorm as pyln
import sounddevice as sd
from pedalboard import LowpassFilter, PeakFilter, Pedalboard
from PIL import Image

import config
import global_vars
import utils


matplotlib.use("Agg")


tmp_files = []

current_duration = 0.0
loudnes_correction = 1.0
start_pos = 0

allowed_files = [".mp3", ".ogg", ".aif", ".aiff", ".m4a", ".flac"]
converted_files = {}

current_volume = 0.0

_stream = None
_selected_device = None
_samplerate = 44100
_audio_data = None
_current_frame = 0
_is_playing = False
_is_paused = False
_fade_frames_remaining = 0
_fade_total_frames = 0
_fade_target_action = None
_intro_frames_remaining = 0
_intro_total_frames = 0
_needs_board_reset = False
_live_playback_context = None
_current_high_frequency = 20000
_state_lock = threading.Lock()

_current_board = Pedalboard()
_current_eq_settings = {"enabled": False, "bands": {}}


def is_initialized():
    return _stream is not None


def delete_tmp_files():
    global tmp_files
    for file in tmp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
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
        print("Cannot load:", file_path, e)
        return None


def _ensure_stream():
    global _stream
    if _stream is not None:
        return
    _stream = sd.OutputStream(
        samplerate=_samplerate,
        device=_selected_device,
        channels=2,
        callback=_audio_callback,
        blocksize=2048,
        dtype="float32",
        latency="high",
    )
    _stream.start()


def _restart_stream():
    global _stream
    if _stream is not None:
        _stream.stop()
        _stream.close()
        _stream = None
    _ensure_stream()


def quit_device():
    global _stream
    stop()
    if _stream is not None:
        _stream.stop()
        _stream.close()
        _stream = None


def set_device(selected_device):
    global _selected_device, _samplerate
    _selected_device = selected_device
    try:
        device_info = sd.query_devices(_selected_device, "output")
        _samplerate = int(device_info["default_samplerate"])
    except Exception:
        _samplerate = 44100
    _restart_stream()
    print("Device set:", selected_device)


def get_devices(capture_devices: bool = False):
    devices = []
    for device in sd.query_devices():
        if capture_devices and device["max_input_channels"] > 0:
            devices.append(device["name"])
        if not capture_devices and device["max_output_channels"] > 0:
            devices.append(device["name"])
    return tuple(devices)


def pcm_to_float(pcm_data, bit_depth=16):
    max_value = float(2 ** (bit_depth - 1))
    return pcm_data.astype(np.float32) / max_value


def audiosegment_to_float32(audio_segment):
    sample_width = audio_segment.sample_width
    channels = audio_segment.channels
    raw = np.array(audio_segment.get_array_of_samples())

    if channels <= 0:
        raise ValueError("Decoded audio has no channels")

    raw = raw.reshape((-1, channels))

    if sample_width == 1:
        scale = float(2 ** 7)
    elif sample_width == 2:
        scale = float(2 ** 15)
    elif sample_width == 3:
        scale = float(2 ** 23)
    elif sample_width == 4:
        scale = float(2 ** 31)
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")

    return raw.astype(np.float32) / scale


def get_loudness(data, rate):
    meter = pyln.Meter(rate)
    return meter.integrated_loudness(data)


def _effective_gain():
    gain = current_volume * loudnes_correction
    return min(1.0, max(0.0, gain))


def set_volume(volume):
    global current_volume
    current_volume = volume


def pause():
    global _is_paused
    with _state_lock:
        _is_paused = True


def unpause():
    global _is_paused, _intro_total_frames, _intro_frames_remaining
    with _state_lock:
        _is_paused = False
        _intro_total_frames = max(1, int((_samplerate * config.fade_time) / 1000.0))
        _intro_frames_remaining = _intro_total_frames


def init_player():
    global _samplerate
    if _selected_device is None:
        try:
            default_info = sd.query_devices(None, "output")
            _samplerate = int(default_info["default_samplerate"])
        except Exception:
            _samplerate = 44100
    _ensure_stream()


def reset_progress():
    global current_duration, start_pos, _current_frame
    current_duration = 0.0
    start_pos = 0
    _current_frame = 0


def get_loudness_corretion():
    return loudnes_correction


def get_loudness_corretion_db():
    if loudnes_correction <= 0:
        return -100
    return 20 * math.log10(loudnes_correction)


def get_progress():
    if current_duration > 0:
        return ((get_pos() + get_start_pos()) / (current_duration * 1000))
    return 0


def get_pos():
    return int((_current_frame / _samplerate) * 1000)


def get_start_pos():
    return start_pos


def get_duration():
    return int(current_duration * 1000)


def fade():
    global _fade_frames_remaining, _fade_total_frames, _fade_target_action
    if not _is_playing:
        return
    _fade_total_frames = max(1, int((_samplerate * config.fade_time) / 1000.0))
    _fade_frames_remaining = _fade_total_frames
    _fade_target_action = "stop"


def fade_to(target_action="stop", duration_ms=None):
    global _fade_frames_remaining, _fade_total_frames, _fade_target_action
    with _state_lock:
        if not _is_playing:
            return
        fade_ms = config.fade_time if duration_ms is None else duration_ms
        _fade_total_frames = max(1, int((_samplerate * fade_ms) / 1000.0))
        _fade_frames_remaining = _fade_total_frames
        _fade_target_action = target_action


def stop():
    global _is_playing, _is_paused, _current_frame
    global _fade_frames_remaining, _fade_total_frames
    global _intro_frames_remaining, _intro_total_frames, _needs_board_reset, _fade_target_action
    with _state_lock:
        _is_playing = False
        _is_paused = False
        _current_frame = 0
        _fade_frames_remaining = 0
        _fade_total_frames = 0
        _fade_target_action = None
        _intro_frames_remaining = 0
        _intro_total_frames = 0
        _needs_board_reset = False


def decode_mp3_to_pcm(input_mp3_path, samplerate=44100):
    from pydub import AudioSegment

    audio = AudioSegment.from_file(input_mp3_path)
    if audio.frame_rate != samplerate:
        audio = audio.set_frame_rate(samplerate)
    if audio.channels != 2:
        audio = audio.set_channels(2)
    return audio


def _build_board(sample_rate, eq_settings, high_frequency):
    filters = [LowpassFilter(cutoff_frequency_hz=min(float(high_frequency), sample_rate / 2 - 200))]
    if eq_settings and eq_settings.get("enabled", False):
        bands = eq_settings.get("bands", {})
        ordered_bands = sorted((float(freq), float(gain)) for freq, gain in bands.items())
        for index, (center_freq, gain_db) in enumerate(ordered_bands):
            lower_freq = ordered_bands[index - 1][0] if index > 0 else center_freq / 2
            upper_freq = ordered_bands[index + 1][0] if index < len(ordered_bands) - 1 else center_freq * 2
            bandwidth = max(1.0, upper_freq - lower_freq)
            q = max(0.35, center_freq / bandwidth)
            filters.append(PeakFilter(cutoff_frequency_hz=center_freq, gain_db=gain_db, q=q))
    return Pedalboard(filters)


def _normalize_eq_settings(eq_settings):
    if not eq_settings:
        return {"enabled": False, "bands": {}}
    return {
        "enabled": bool(eq_settings.get("enabled", False)),
        "bands": {str(freq): float(gain) for freq, gain in eq_settings.get("bands", {}).items()},
    }


def _apply_processing_change(eq_settings, high_frequency, smooth):
    global _current_board, _current_high_frequency, _current_eq_settings

    normalized_target = _normalize_eq_settings(eq_settings)
    target_high_frequency = float(high_frequency)
    _current_board = _build_board(_samplerate, normalized_target, target_high_frequency)
    _current_eq_settings = normalized_target
    _current_high_frequency = target_high_frequency


def _audio_callback(outdata, frames, time_info, status):
    global _current_frame, _is_playing, _is_paused
    global _fade_frames_remaining, _fade_target_action
    global _intro_frames_remaining, _needs_board_reset
    global _current_board

    outdata.fill(0)

    with _state_lock:
        if not _is_playing or _is_paused or _audio_data is None:
            return

        remaining_frames = len(_audio_data) - _current_frame
        chunk_size = min(frames, remaining_frames)
        if chunk_size <= 0:
            _is_playing = False
            return

        chunk = _audio_data[_current_frame:_current_frame + chunk_size]
        processed = _current_board.process(
            chunk.T,
            _samplerate,
            buffer_size=chunk_size,
            reset=_needs_board_reset,
        ).T
        _needs_board_reset = False

        gain = _effective_gain()
        if _fade_frames_remaining > 0:
            fade_count = min(chunk_size, _fade_frames_remaining)
            fade_start = _fade_frames_remaining / _fade_total_frames
            fade_end = max(0.0, (_fade_frames_remaining - fade_count) / _fade_total_frames)
            ramp = np.linspace(fade_start, fade_end, fade_count, dtype=np.float32).reshape(-1, 1)
            processed[:fade_count] *= ramp * gain
            if fade_count < chunk_size:
                processed[fade_count:] = 0
            _fade_frames_remaining -= fade_count
            if _fade_frames_remaining <= 0:
                if _fade_target_action == "pause":
                    _is_paused = True
                else:
                    _is_playing = False
                _fade_target_action = None
        else:
            processed *= gain

        if _intro_frames_remaining > 0:
            intro_count = min(chunk_size, _intro_frames_remaining)
            intro_start_done = _intro_total_frames - _intro_frames_remaining
            intro_end_done = intro_start_done + intro_count
            intro_start = intro_start_done / _intro_total_frames
            intro_end = intro_end_done / _intro_total_frames
            ramp = np.linspace(intro_start, intro_end, intro_count, dtype=np.float32).reshape(-1, 1)
            processed[:intro_count] *= ramp
            _intro_frames_remaining -= intro_count

        if _fade_frames_remaining <= 0 and remaining_frames <= chunk_size:
            outro_count = min(chunk_size, max(1, int(_samplerate * 0.008)))
            ramp = np.linspace(1.0, 0.0, outro_count, dtype=np.float32).reshape(-1, 1)
            processed[chunk_size - outro_count:chunk_size] *= ramp

        outdata[:chunk_size] = processed
        _current_frame += chunk_size

        if chunk_size < frames:
            _is_playing = False
        elif _current_frame >= len(_audio_data):
            _is_playing = False


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
    audio_segment = decode_mp3_to_pcm(file, 44100)
    return get_loudness(audiosegment_to_float32(audio_segment), 44100)


def detect_silence_start_end_from_file(file, min_silence_len, silence_tresh):
    audio_segment = decode_mp3_to_pcm(file, 44100)
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
    global _audio_data, _current_frame, _is_playing, _is_paused
    global current_duration, start_pos, loudnes_correction, _live_playback_context
    global _samplerate, _fade_frames_remaining, _fade_total_frames
    global _intro_frames_remaining, _intro_total_frames, _needs_board_reset
    global _current_board, _current_eq_settings, _current_high_frequency

    init_player()
    start_time = time.time()

    if _selected_device is not None:
        try:
            device_info = sd.query_devices(_selected_device, "output")
            _samplerate = int(device_info["default_samplerate"])
        except Exception:
            _samplerate = 44100

    audio_segment = decode_mp3_to_pcm(file, _samplerate)
    data = files[song_id]
    if len(data) > 4:
        start_cut, end_cut = data[3], data[4]
    else:
        print("Extra cut for file:", file)
        start_cut, end_cut = utils.detect_silence_start_end(audio_segment, 200, -56)
    print("Cut:", start_cut, end_cut)

    audio_segment = audio_segment[start_cut:end_cut]
    pcm_data = np.array(audio_segment.get_array_of_samples(), dtype=np.int16)
    next_audio_data = audiosegment_to_float32(audio_segment)

    if update_wave:
        threading.Thread(target=lambda: make_wave(pcm_data, _samplerate), daemon=True).start()

    if normalize_volume:
        if len(data) > 2:
            loudness = data[2]
        else:
            print("Extra loudness for file:", file)
            loudness = get_loudness(next_audio_data, _samplerate)
        target_lufs = -20
        difference = target_lufs - loudness
        next_loudness_correction = 10 ** (difference / 20.0)
        print("Volume:", current_volume, min(1.0, max(0.0, current_volume * next_loudness_correction)), next_loudness_correction, loudness)
    else:
        next_loudness_correction = 1.0

    next_board = _build_board(_samplerate, _normalize_eq_settings(eq_settings), high_frequency)
    next_duration = len(next_audio_data) / _samplerate
    next_frame = min(len(next_audio_data), max(0, int((pos / 1000.0) * _samplerate)))
    next_intro_total_frames = max(1, int((_samplerate * config.fade_time) / 1000.0))

    with _state_lock:
        _audio_data = next_audio_data
        _current_board = next_board
        _current_eq_settings = _normalize_eq_settings(eq_settings)
        _current_high_frequency = float(high_frequency)
        loudnes_correction = next_loudness_correction
        current_duration = next_duration
        _current_frame = next_frame
        start_pos = 0
        _is_playing = True
        _is_paused = False
        _fade_frames_remaining = 0
        _fade_total_frames = 0
        _intro_total_frames = next_intro_total_frames
        _intro_frames_remaining = _intro_total_frames
        _needs_board_reset = True

    _live_playback_context = {
        "file": file,
        "song_id": song_id,
        "files": files,
        "normalize_volume": normalize_volume,
        "low_frequency": low_frequency,
        "high_frequency": high_frequency,
        "eq_settings": eq_settings,
    }

    print(f"Decode and prepare time: {time.time() - start_time:.4f} s")
    return current_duration


def extract_h_value(input_string, default_value=20000):
    normalized_value = "" if input_string is None else str(input_string)
    match = re.search(r"h:(\d+)", normalized_value.lower())
    if match:
        return int(match.group(1))
    return default_value


def play_from_list(song_id, songs, pos=0):
    if song_id is None:
        return
    file = songs[song_id][0]
    tags = songs[song_id][1]
    genre = tags.get("genre", "")
    comment = tags.get("comment", "")

    high_frequency = extract_h_value(comment)
    eq_settings = config.get_genre_equalizer_settings(genre)
    print("High frequency:", high_frequency)
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
        print("Error:", str(e))
    print("Playing:", song_id, file)


def update_live_eq(eq_settings):
    global _live_playback_context

    if not _live_playback_context or not get_busy():
        return

    _live_playback_context = dict(_live_playback_context)
    _live_playback_context["eq_settings"] = eq_settings
    _apply_processing_change(eq_settings, _live_playback_context["high_frequency"], smooth=True)


def get_busy():
    return bool(_is_playing and not _is_paused)
