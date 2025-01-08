import sys
from cx_Freeze import setup, Executable
import config

includefiles = [
    ('icons/delete.png', 'icons/delete.png'),
    ('icons/icon.png', 'icons/icon.png'),
    ('icons/next.png', 'icons/next.png'),
    ('icons/pause.png', 'icons/pause.png'),
    ('icons/play.png', 'icons/play.png'),
    ('icons/stop.png', 'icons/stop.png'),

    ('icon.ico', 'icon.ico'),

    ('ffmpeg/ffmpeg.exe', 'ffmpeg/ffmpeg.exe'),
    ('ffmpeg/ffprobe.exe', 'ffmpeg/ffprobe.exe'),
]

includes = []
excludes = []
packages = []

base = "Win32GUI"


product_name = 'Milonga'

directory_table = [
    ("ProgramMenuFolder", "TARGETDIR", "."),
    ("MyProgramMenu", "ProgramMenuFolder", "MYPROG~1|My Program"),]
   
shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "Milonga",           # Name that will be show on the link
     "TARGETDIR",              # Component_
     "[TARGETDIR]Milonga.exe",# Target exe to exexute
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     ),
     

    ]


msi_data = {"Shortcut": shortcut_table}


bdist_msi_options = {
    # 'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01E}',
    'add_to_path': False,
    'initial_target_dir': r'C:\ProgramFiles\%s' % (product_name),
    'target_name' : 'Milonga',
    'directories' : directory_table, 
    "summary_data": {"author": "Me",
    "comments": "Milonga DJ"},
    "data":msi_data
    }
   

# Konfiguracja `setup`
setup(
    name="Milonga",
    version=config.get_version(),
    description='Milonga DJ App',
    author='Paweł Wąsowicz',
    options={
        'build_exe': {
            "include_msvcr": True,
            'includes': includes,
            'excludes': excludes,
            'packages': packages,
            'include_files': includefiles
        },
        'bdist_msi': bdist_msi_options
    },
    executables=[
        Executable(
            "milonga.py",
            base=base,
            target_name='Milonga',
            icon="icon.ico"  # Opcjonalnie: ustaw ikonę aplikacji
        )
    ],
)
