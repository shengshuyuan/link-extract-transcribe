"""Use the prepared web venv for direct CLI invocations, without installing anything."""
import os
from pathlib import Path
import sys

def use_web_environment(script):
    venv=Path.home()/'.workbuddy/venvs/link-extract'
    executable=venv/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    # Respect an explicitly selected virtual environment, including setup_web.py --venv targets.
    if sys.prefix != sys.base_prefix:
        return
    if executable.is_file() and Path(sys.prefix).resolve()!=venv.resolve():
        os.execv(str(executable),[str(executable),str(Path(script).resolve()),*sys.argv[1:]])
