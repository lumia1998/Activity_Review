from __future__ import annotations

import json

from ..base import ActiveWindowInfo, normalize_display_app_name
from .common import run_command


def _from_gnome() -> ActiveWindowInfo | None:
    output = run_command([
        'gdbus', 'call', '--session', '--dest', 'org.gnome.Shell', '--object-path', '/org/gnome/Shell/Extensions/WindowsExt', '--method', 'org.gnome.Shell.Extensions.WindowsExt.FocusInfo'
    ])
    if not output:
        return None
    title = output.strip().strip('()').strip().strip("'")
    app_name = 'Unknown App'
    if '|' in title:
        app_name, _, title = title.partition('|')
    app_name = normalize_display_app_name(app_name.strip() or 'Unknown App')
    return ActiveWindowInfo(hwnd=0, pid=None, app_name=app_name, window_title=title.strip() or app_name, executable_path=None)


def _walk_sway_tree(node: dict) -> ActiveWindowInfo | None:
    if node.get('focused'):
        app_name = normalize_display_app_name((node.get('app_id') or node.get('window_properties', {}).get('class') or 'Sway App').strip())
        title = (node.get('name') or app_name).strip()
        pid = node.get('pid')
        return ActiveWindowInfo(hwnd=0, pid=pid if isinstance(pid, int) else None, app_name=app_name, window_title=title, executable_path=None)
    for child in node.get('nodes', []) + node.get('floating_nodes', []):
        info = _walk_sway_tree(child)
        if info:
            return info
    return None


def _from_sway() -> ActiveWindowInfo | None:
    output = run_command(['swaymsg', '-t', 'get_tree'])
    if not output:
        return None
    try:
        tree = json.loads(output)
    except json.JSONDecodeError:
        return None
    return _walk_sway_tree(tree)


def _from_hyprland() -> ActiveWindowInfo | None:
    output = run_command(['hyprctl', 'activewindow', '-j']) or run_command(['hyprctl', 'activewindow'])
    if not output:
        return None
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        title = str(payload.get('title') or 'Wayland Window').strip()
        app_name = normalize_display_app_name(str(payload.get('class') or payload.get('initialClass') or 'Hyprland App').strip())
        pid = payload.get('pid')
        return ActiveWindowInfo(hwnd=0, pid=pid if isinstance(pid, int) else None, app_name=app_name, window_title=title or app_name, executable_path=None)

    title = 'Wayland Window'
    app_name = 'Hyprland App'
    for line in output.splitlines():
        lower = line.lower().strip()
        if lower.startswith('title:'):
            title = line.split(':', 1)[-1].strip() or title
        elif lower.startswith('class:'):
            app_name = normalize_display_app_name(line.split(':', 1)[-1].strip() or app_name)
    return ActiveWindowInfo(hwnd=0, pid=None, app_name=app_name, window_title=title, executable_path=None)


def _from_kde() -> ActiveWindowInfo | None:
    title = run_command(['kdotool', 'getactivewindow', 'getwindowname'])
    if not title:
        return None
    app_name = run_command(['kdotool', 'getactivewindow', 'getwindowclassname']) or title
    return ActiveWindowInfo(hwnd=0, pid=None, app_name=normalize_display_app_name(app_name), window_title=title, executable_path=None)


def get_foreground_window_info() -> ActiveWindowInfo | None:
    for provider in (_from_gnome, _from_kde, _from_sway, _from_hyprland):
        info = provider()
        if info:
            return info
    return None
