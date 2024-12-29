import pygame
import pyloudnorm as pyln
import soundfile as sf

import config
from mutagen.mp3 import MP3
import os

import utils
import uuid
import json

current_duration = 0
start_pos = 0

allowed_files = [".mp3",".ogg"]

converted_files = {}

import pygame._sdl2.audio as sdl2_audio


def remove_converted_file_from_list(name):
    global converted_files
    del converted_files[name]

def load_converted_files():
    global converted_files
    file_name = config.get_converted_files_full_file_name()
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            converted_files = json.load(file)


def get_converted_files():
    return converted_files

def save_converted_files():
    file_name = config.get_converted_files_full_file_name()
    with open(file_name, 'w') as file:
        json.dump(converted_files, file,indent=4)

def can_load_sound(file_path):
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()
        if extension in allowed_files:
            return file_path
        else:
            new_sound_file = str(uuid.uuid4())+".mp3"
            new_file = os.path.join(config.get_application_support_directory(), new_sound_file)
            utils.convert_to_mp3_with_tags(file_path,new_file)
            converted_files[new_file] = file_path
            return new_file
    except Exception as e:
        # W przypadku błędu zwróci False
        print("Cannot load: ",file_path,e)
        return None

def set_device(selected_device):
    pygame.mixer.quit()  # Zatrzymanie aktualnego urządzenia
    pygame.mixer.init(devicename=selected_device)

def get_devices(capture_devices: bool = False):
    devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
    return devices


def get_loudness(file_path):
    data, rate = sf.read(file_path)
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(data)
    return loudness


def calculate_replay_volume(file_path,target_lufs=-20):
    loudness = get_loudness(file_path)
    replay_gain = target_lufs - loudness
    linear_volume = 10 ** (replay_gain/ 20)
    return linear_volume

def set_volume(volume):
    pygame.mixer.music.set_volume(volume)

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

def get_progress():
    global current_duration
    global start_pos
    if current_duration>0:
        pos = get_pos()
        #print(pos,start_pos,current_duration)
        return (pos+start_pos)/(current_duration*1000)
    else:
        return 0

def get_pos():
    return pygame.mixer_music.get_pos()

def fade():
    pygame.mixer.music.fadeout(config.fade_time)

def stop():
    pygame.mixer.music.stop()

def play_from_file(file, pos=0):
    global current_duration
    global start_pos
    pygame.mixer.music.load(file)
    audio = MP3(file)
    duration = audio.info.length
    current_duration = duration
    start_pos = start_pos+pos
    pos = pos/1000


    fade_time = 0
    if pos >0:
        fade_time = config.fade_time
    pygame.mixer.music.play(fade_ms=fade_time, start=pos)

    return duration
    #time.sleep(3)

     #Zatrzymaj odtwarzanie po 10 sekundach
    #pygame.mixer.music.stop()

def play_from_list(song_id,songs, pos =0):
    if song_id is not None:
        file = songs[song_id][0]
        try:
            play_from_file(file, pos=pos)
        except Exception as e:
            print(str(e))
        print("Playing: ",song_id,file)

def get_busy():
    return pygame.mixer.music.get_busy()
