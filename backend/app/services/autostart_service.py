from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

from ..core.paths import APP_NAME, PROJECT_ROOT
from .config_service import load_config

AUTOSTART_FILE_NAME = 'Activity Review.cmd'
LINUX_AUTOSTART_FILE = f'{APP_NAME}.desktop'
MACOS_AUTOSTART_FILE = f'{APP_NAME}.plist'


def _windows_startup_dir() -> Path:
    appdata = os.getenv('APPDATA')
    if appdata:
        return Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    return Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'


def _linux_autostart_dir() -> Path:
    config_home = os.getenv('XDG_CONFIG_HOME')
    if config_home:
        return Path(config_home) / 'autostart'
    return Path.home() / '.config' / 'autostart'


def _macos_launch_agents_dir() -> Path:
    return Path.home() / 'Library' / 'LaunchAgents'


def _autostart_file_path() -> Path:
    if sys.platform == 'win32':
        return _windows_startup_dir() / AUTOSTART_FILE_NAME
    if sys.platform == 'darwin':
        return _macos_launch_agents_dir() / MACOS_AUTOSTART_FILE
    return _linux_autostart_dir() / LINUX_AUTOSTART_FILE


def _launch_args() -> str:
    config = load_config()
    return ' --silent' if bool(config.get('auto_start_silent')) else ''


def _build_windows_autostart_command() -> str:
    project_root = str(PROJECT_ROOT)
    python_executable = str(Path(sys.executable))
    return (
        '@echo off\r\n'
        f'cd /d "{project_root}"\r\n'
        f'"{python_executable}" -m desktop.main{_launch_args()}\r\n'
    )


def _build_linux_desktop_entry() -> str:
    python_executable = str(Path(sys.executable))
    exec_line = f'"{python_executable}" -m desktop.main{_launch_args()}'.strip()
    return (
        '[Desktop Entry]\n'
        'Type=Application\n'
        'Version=1.0\n'
        'Name=Activity Review\n'
        f'Exec={exec_line}\n'
        f'Path={PROJECT_ROOT}\n'
        'Terminal=false\n'
        'X-GNOME-Autostart-enabled=true\n'
    )


def _build_macos_launch_agent() -> str:
    python_executable = str(Path(sys.executable))
    launch_args = _launch_args().strip().split() if _launch_args().strip() else []
    args_xml = '\n'.join(f'      <string>{arg}</string>' for arg in ['-m', 'desktop.main', *launch_args])
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        '  <dict>\n'
        f'    <key>Label</key><string>{APP_NAME}</string>\n'
        '    <key>ProgramArguments</key>\n'
        '    <array>\n'
        f'      <string>{python_executable}</string>\n'
        f'{args_xml}\n'
        '    </array>\n'
        f'    <key>WorkingDirectory</key><string>{PROJECT_ROOT}</string>\n'
        '    <key>RunAtLoad</key><true/>\n'
        '    <key>KeepAlive</key><false/>\n'
        '  </dict>\n'
        '</plist>\n'
    )


def _build_autostart_content() -> str:
    if sys.platform == 'win32':
        return _build_windows_autostart_command()
    if sys.platform == 'darwin':
        return _build_macos_launch_agent()
    return _build_linux_desktop_entry()


def enable_autostart() -> bool:
    path = _autostart_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_build_autostart_content(), encoding='utf-8')
    if sys.platform != 'win32':
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return True


def disable_autostart() -> bool:
    path = _autostart_file_path()
    if path.exists():
        path.unlink()
    return True


def is_autostart_enabled() -> bool:
    return _autostart_file_path().exists()
