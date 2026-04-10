from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any


def run_command(command: list[str], timeout: int = 2) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return ''
    if result.returncode != 0:
        return ''
    return (result.stdout or '').strip()


def linux_session_type() -> str:
    return (os.getenv('XDG_SESSION_TYPE') or '').strip().lower() or 'unknown'


def linux_desktop_environment() -> str:
    current = (os.getenv('XDG_CURRENT_DESKTOP') or '').strip()
    if current:
        return current
    return (os.getenv('DESKTOP_SESSION') or '').strip() or 'unknown'


def get_platform_support() -> dict[str, Any]:
    import sys

    platform = 'macos' if sys.platform == 'darwin' else ('windows' if sys.platform == 'win32' else 'linux' if sys.platform.startswith('linux') else sys.platform)
    session_type = linux_session_type() if platform == 'linux' else 'n/a'
    desktop_environment = linux_desktop_environment() if platform == 'linux' else 'n/a'

    active_window_supported = platform in {'windows', 'macos'}
    active_window_provider = 'windows-api' if platform == 'windows' else 'appkit' if platform == 'macos' else 'unknown'
    if platform == 'linux':
        if session_type == 'x11':
            active_window_supported = bool(shutil.which('xdotool') and shutil.which('xprop'))
            active_window_provider = 'x11-tools' if active_window_supported else 'missing-x11-tools'
        elif session_type == 'wayland':
            if shutil.which('gdbus'):
                active_window_supported = True
                active_window_provider = 'wayland-gnome'
            elif shutil.which('kdotool'):
                active_window_supported = True
                active_window_provider = 'wayland-kde'
            elif shutil.which('swaymsg'):
                active_window_supported = True
                active_window_provider = 'wayland-sway'
            elif shutil.which('hyprctl'):
                active_window_supported = True
                active_window_provider = 'wayland-hyprland'
            else:
                active_window_provider = 'wayland-unknown'

    return {
        'platform': platform,
        'sessionType': session_type,
        'desktopEnvironment': desktop_environment,
        'activeWindowSupported': active_window_supported,
        'activeWindowProvider': active_window_provider,
    }
