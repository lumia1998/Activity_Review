from __future__ import annotations

import os
import sys
from pathlib import Path

from ..core.paths import PROJECT_ROOT
from .config_service import load_config

AUTOSTART_FILE_NAME = 'Activity Review.cmd'


def _startup_dir() -> Path:
    appdata = os.getenv('APPDATA')
    if appdata:
        return Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    return Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'


def _autostart_file_path() -> Path:
    return _startup_dir() / AUTOSTART_FILE_NAME


def _build_autostart_command() -> str:
    project_root = str(PROJECT_ROOT)
    python_executable = str(Path(sys.executable))
    launch_args = ''
    config = load_config()
    if bool(config.get('auto_start_silent')):
        launch_args = ' --silent'

    return (
        '@echo off\r\n'
        f'cd /d "{project_root}"\r\n'
        f'"{python_executable}" -m desktop.main{launch_args}\r\n'
    )


def enable_autostart() -> bool:
    path = _autostart_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_build_autostart_command(), encoding='utf-8')
    return True


def disable_autostart() -> bool:
    path = _autostart_file_path()
    if path.exists():
        path.unlink()
    return True


def is_autostart_enabled() -> bool:
    return _autostart_file_path().exists()
