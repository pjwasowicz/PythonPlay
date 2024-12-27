import pygame
import pyloudnorm as pyln
import soundfile as sf

import config
from mutagen.mp3 import MP3

current_duration = 0
start_pos = 0



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
    current_duration = 0;
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
        play_from_file(file, pos=pos)
        print("Playing: ",song_id,file)

def get_busy():
    return pygame.mixer.music.get_busy()
