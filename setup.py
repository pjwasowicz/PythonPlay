from cx_Freeze import setup, Executable
import config

includefiles = []



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
python setup.py bdist_mac
bdist_dmg
codesign --deep --force --verify --verbose --sign "Milonga" build/milonga-1.1.app 
"""

plist_items = [
    ('LSEnvironment', {
        'LANG': 'pl_PL.UTF-8',
        'LC_ALL': 'pl_PL.UTF-8'
    })
]

setup(
    name="Milonga",
    version=config.get_version(),
    description = 'Milonga DJ App',
    author = 'Paweł Wąsowicz',
    options = {'bdist_dmg':{'show_icon_preview':True},
               'bdist_mac':{'plist_items':plist_items, "iconfile":"icon.icns"},
               'build_exe': {'includes':includes,'excludes':excludes,'packages':packages,'include_files':includefiles}},
    executables=[Executable("milonga.py", base=base, target_name='Milonga')],
)
