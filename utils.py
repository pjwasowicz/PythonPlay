from tkinter import *
from PIL import Image, ImageTk
import subprocess
import itertools



def db_to_float(db, using_amplitude=True):
    """
    Converts the input db to a float, which represents the equivalent
    ratio in power.
    """
    db = float(db)
    if using_amplitude:
        return 10 ** (db / 20)
    else: # using power
        return 10 ** (db / 10)

def detect_silence_start_end(audio_segment, min_silence_len=1000, silence_thresh=-16, seek_step=1):


    seg_len = len(audio_segment)
    if seg_len < min_silence_len:
        return []

    # convert silence threshold to a float value (so we can compare it to rms)
    silence_thresh = db_to_float(silence_thresh) * audio_segment.max_possible_amplitude

    # find silence and add start and end indicies to the to_cut list
    silence_starts = []

    # check successive (1 sec by default) chunk of sound for silence
    # try a chunk at every "seek step" (or every chunk for a seek step == 1)
    last_slice_start = seg_len - min_silence_len
    slice_starts = range(0, last_slice_start + 1, seek_step)

     # guarantee last_slice_start is included in the range
    # to make sure the last portion of the audio is seached
    if last_slice_start % seek_step:
        slice_starts = itertools.chain(slice_starts, [last_slice_start])

    #silenceAtStart = True
    for i in slice_starts:
        audio_slice = audio_segment[i:i + min_silence_len]
        if audio_slice.rms < silence_thresh:
            silence_starts.append(i)
        else:
            break

    #find the silences at the end of the file
    silence_ends = []
    lst = list(slice_starts)
    lst.reverse()

    for i in lst:
        audio_slice = audio_segment[i-min_silence_len:i]
        if audio_slice.rms < silence_thresh:
            silence_ends.append(i)
        else:
            break

    # combine the silence we detected into ranges (start ms - end ms)
    silent_ranges = []

    if silence_starts:
        silent_ranges.append([0,silence_starts[len(silence_starts)-1]])
    if silence_ends:
        silent_ranges.append([silence_ends[len(silence_ends)-1], silence_ends[0]])

    silences = silent_ranges

    if (len(silences) > 1):
        starttime = silences[0][1]
        stoptime = silences[len(silences) - 1][0]
        tango_tstart = starttime
        tango_tend = stoptime
    elif len(silences) == 1:
        if (silences[0][0] == 0):
            tango_tstart = silences[0][1]
            tango_tend = len(audio_segment)
        elif silences[0][0] > len(audio_segment) * 3 / 4:
            tango_tstart = 0
            tango_tend = silences[0][0]
    elif len(silences) == 0:
        tango_tstart = 0
        tango_tend = len(audio_segment)
    else:
        tango_tstart = 0
        tango_tend = 0

    return tango_tstart, tango_tend






def convert_to_mp3_with_tags(input_file, output_file):

    ffmpeg_command = ['ffmpeg', '-i', input_file, output_file]

    subprocess.run(ffmpeg_command, check=True)


def get_files_from_tree(tree, songs):
    files = []
    for item_id in tree.get_children():
        files.append(songs[item_id])
    return files


def load_and_resize_image(file, size=(32, 32)):
    image = Image.open(file)  # Załaduj obraz
    image_resized = image.resize(size)  # Przeskaluj obraz
    return ImageTk.PhotoImage(image_resized)


import os


def get_libraries():
    # Uruchomienie lsof i filtrowanie bibliotek z /Users/pawel
    output = os.popen("lsof | grep dylib | grep '/Users/pawel'").read()

    # Wyodrębnienie unikalnych katalogów
    directories = set()
    for line in output.splitlines():
        # Załóż, że ścieżka jest ostatnią kolumną
        path = line.split()[-1]
        directory = os.path.dirname(path)
        directories.add(directory)

    # Wyświetlenie unikalnych katalogów
    #print("Katalogi z bibliotekami dylib:")
    res = []
    for directory in sorted(directories):
        directory = os.path.relpath(directory, "")
        res.append(directory)
    res = str(res)
    res = "resources_dirs = {res}".format(res=res)

    with open("libs.py", "w") as file:
        file.write(res)
    print(res)
