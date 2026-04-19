import os
import platform
import subprocess
from functools import wraps

import logs


def setup_application_environment():
    the_path = os.path.dirname(os.path.abspath(__file__))
    path_to_remove = os.path.join("lib", "library.zip")
    if the_path.endswith(path_to_remove):
        the_path = the_path[: -len(path_to_remove)]
    print("App path:", the_path)

    os.chdir(the_path)

    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg")
    os.environ["PATH"] += os.pathsep + ffmpeg_path

    if platform.system() == "Windows":
        old_popen = subprocess.Popen

        @wraps(old_popen)
        def new_popen(*args, startupinfo=None, **kwargs):
            if startupinfo is None:
                startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            return old_popen(*args, startupinfo=startupinfo, **kwargs)

        subprocess.Popen = new_popen
