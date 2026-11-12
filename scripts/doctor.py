#!/usr/bin/env python3
"""Read-only dependency check. Does not install, download, transcribe or print credentials."""
from web_runtime import use_web_environment
use_web_environment(__file__)
import importlib.util,json,platform,shutil,sys
from pathlib import Path
print(json.dumps({'python':platform.python_version(),'active_python':sys.executable,'web_python':str(Path.home()/'.workbuddy/venvs/link-extract'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')),'python_supported':sys.version_info>=(3,10),
'web':{name:bool(importlib.util.find_spec(module)) for name,module in [('requests','requests'),('beautifulsoup4','bs4'),('markdownify','markdownify')]},
'optional':{'yt-dlp':bool(shutil.which('yt-dlp')),'ffmpeg':bool(shutil.which('ffmpeg')),'faster-whisper':bool(importlib.util.find_spec('faster_whisper'))},
'note':'技能包不附带这些运行工具；只检查是否存在，不代表已验证目标链接或音频'},ensure_ascii=False,indent=2))
