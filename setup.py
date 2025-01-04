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

        ('icon.icns', 'icon.icns'),

        ('ffmpeg/ffmpeg', 'ffmpeg/ffmpeg'),
        ('ffmpeg/ffprobe', 'ffmpeg/ffprobe'),

    ]


includes = []
excludes = []
packages = []

base = ""

"""
<key>LSEnvironment</key>
<dict>
    <key>LANG</key>
    <string>pl_PL.UTF-8</string>
    <key>LC_ALL</key>
    <string>pl_PL.UTF-8</string>
</dict>

python setup.py bdist_mac
bdist_dmg
"""


if platform.system() == 'Windows':
    base = 'Win32GUI'

plist_items = [
    ('LSEnvironment', {
        'LANG': 'pl_PL.UTF-8',
        'LC_ALL': 'pl_PL.UTF-8'
    })
]

setup(
    name="Milonga",
    version="1.0",
    description = 'Milonga DJ App',
    author = 'Paweł Wąsowicz',
    options = {'bdist_dmg':{'show_icon_preview':True},
               'bdist_mac':{'plist_items':plist_items, "iconfile":"icon.icns"},
               'build_exe': {'includes':includes,'excludes':excludes,'packages':packages,'include_files':includefiles}},
    executables=[Executable("milonga.py", base=base, target_name='Milonga')],
)
