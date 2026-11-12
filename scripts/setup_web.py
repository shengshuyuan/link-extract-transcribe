#!/usr/bin/env python3
"""Prepare only the web extractor dependencies in a private WorkBuddy venv."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

PACKAGES = ('requests', 'beautifulsoup4', 'markdownify')

def python_in(venv):
    return venv / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')

def check(executable):
    if not executable.is_file():
        return {'ready': False, 'missing': list(PACKAGES), 'reason': '专用Python环境尚未创建'}
    probe = "import importlib.metadata,json; names=" + repr(PACKAGES) + "; result={}\nfor name in names:\n try: result[name]=importlib.metadata.version(name)\n except importlib.metadata.PackageNotFoundError: result[name]=None\nprint(json.dumps(result))"
    result = subprocess.run([str(executable), '-c', probe], capture_output=True, text=True, check=True)
    versions = json.loads(result.stdout)
    # Import the real modules too; metadata alone does not prove the interpreter can use them.
    imports = subprocess.run([str(executable), '-c', 'import requests,bs4,markdownify'], capture_output=True, text=True)
    missing = [name for name, version in versions.items() if version is None]
    return {'ready': not missing and imports.returncode == 0, 'versions': versions, 'missing': missing,
            'reason': '' if imports.returncode == 0 else '模块导入失败，需要检查或修复依赖'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='明确执行创建环境和安装网页依赖；省略则只检查')
    parser.add_argument('--venv', type=Path, default=Path.home()/'.workbuddy/venvs/link-extract')
    args = parser.parse_args()
    venv = args.venv.expanduser().resolve()
    executable = python_in(venv)
    requirements = Path(__file__).resolve().parents[1]/'requirements-web.txt'
    try:
        if sys.version_info < (3,10):
            raise RuntimeError('需要Python 3.10或更新版本')
        if args.install:
            if not requirements.is_file():
                raise FileNotFoundError('技能包缺少requirements-web.txt，请重新导入完整技能ZIP')
            if venv.exists() and not executable.is_file():
                raise RuntimeError('目标目录已存在但不是有效虚拟环境，不会覆盖；请先检查此目录或用--venv指定新目录')
            if not executable.exists():
                subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
            subprocess.run([str(executable),'-m','pip','install','-r',str(requirements)],check=True)
        status = check(executable)
        print(json.dumps({**status, 'python':str(executable), 'skill':str(requirements.parent),
                          'next':'网页脚本必须使用上面这个Python运行；安装成功不代表目标链接已实测',
                          'audio_note':'只安装网页依赖；未安装语音模型、未下载媒体、未上传或调用付费服务'},ensure_ascii=False,indent=2))
        return 0 if status['ready'] else 1
    except Exception as exc:
        print(json.dumps({'ready':False,'message':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 1
if __name__ == '__main__':
    sys.exit(main())
