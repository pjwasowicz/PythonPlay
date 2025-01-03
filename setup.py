import os

from cx_Freeze import setup, Executable
import platform

includefiles = []


if platform.system() == 'Windows':

    includefiles = [
        ('icons/delete.png', 'icons/delete.png'),
        ('icons/icon.png', 'icons/icon.png'),
        ('icons/next.png', 'icons/next.png'),
        ('icons/pause.png', 'icons/pause.png'),
        ('icons/play.png', 'icons/play.png'),
        ('icons/stop.png', 'icons/stop.png'),

        ('ffmpeg/ffmpeg.exe', 'ffmpeg/ffmpeg.exe'),
        ('ffmpeg/ffprobe.exe', 'ffmpeg/ffprobe.exe'),


    ]
else:
    includefiles = [
        ('icons/delete.png', 'icons/delete.png'),
        ('icons/icon.png', 'icons/icon.png'),
        ('icons/next.png', 'icons/next.png'),
        ('icons/pause.png', 'icons/pause.png'),
        ('icons/play.png', 'icons/play.png'),
        ('icons/stop.png', 'icons/stop.png'),

        ('ffmpeg/ffmpeg', 'ffmpeg/ffmpeg'),
        ('ffmpeg/ffprobe', 'ffmpeg/ffprobe'),

    ]


includes = []
excludes = []
packages = []

base = ""

if platform.system() == 'Windows':
    base = 'Win32GUI'

setup(
    name="Milonga",
    version="1.0",
    description="Milonga",
    options = {'build_exe': {'includes':includes,'excludes':excludes,'packages':packages,'include_files':includefiles}},
    executables=[Executable("milonga.py", base=base)],
)

import subprocess

os.chdir('./build')
script_path = "./make_app.sh"
try:
    result = subprocess.run(["bash", script_path], capture_output=True, text=True, check=True)
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error: ", e.stderr)