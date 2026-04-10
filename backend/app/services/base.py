from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActiveWindowInfo:
    hwnd: int
    pid: int | None
    app_name: str
    window_title: str
    executable_path: str | None

    def to_payload(self) -> dict[str, Any]:
        return {
            'hwnd': self.hwnd,
            'pid': self.pid,
            'appName': self.app_name,
            'windowTitle': self.window_title,
            'executablePath': self.executable_path,
        }


_SYSTEM_PROCESS_NAMES = {
    'desktop',
    'lockapp',
    'logonui',
    'searchapp',
    'searchhost',
    'shellexperiencehost',
    'startmenuexperiencehost',
    'textinputhost',
    'applicationframehost',
    'dwm',
    'csrss',
    'taskmgr',
    'loginwindow',
    'screensaverengine',
    'screensaver',
    'cinnamon-session',
    'cinnamon-screensaver',
    'gnome-shell',
    'gnome-screensaver',
    'plasmashell',
    'kscreenlocker',
    'xscreensaver',
    'i3lock',
    'swaylock',
    'xfce4-session',
}

_IGNORED_WINDOW_NAMES = {
    'default ime',
    'msctfime ui',
    'program manager',
    'activity review',
    'acticity review',
}

_DISPLAY_NAME_MAP = {
    'work-review': 'Activity Review',
    'work_review': 'Activity Review',
    'workreview': 'Activity Review',
    'work review': 'Activity Review',
    'activity-review': 'Activity Review',
    'activity_review': 'Activity Review',
    'acticity-review': 'Activity Review',
    'acticity_review': 'Activity Review',
    'acticity review': 'Activity Review',
    'chrome': 'Google Chrome',
    'google chrome': 'Google Chrome',
    'msedge': 'Microsoft Edge',
    'edge': 'Microsoft Edge',
    'microsoft edge': 'Microsoft Edge',
    'brave': 'Brave Browser',
    'brave browser': 'Brave Browser',
    'firefox': 'Firefox',
    'safari': 'Safari',
    'opera': 'Opera',
    'vivaldi': 'Vivaldi',
    'chromium': 'Chromium',
    'arc': 'Arc',
    'orion': 'Orion',
    'zen browser': 'Zen Browser',
    'zen': 'Zen Browser',
    'librewolf': 'LibreWolf',
    'waterfox': 'Waterfox',
    'qqbrowser': 'QQ Browser',
    'qq browser': 'QQ Browser',
    'qq浏览器': 'QQ Browser',
    '360se': '360 Browser',
    '360chrome': '360 Browser',
    '360 browser': '360 Browser',
    '360浏览器': '360 Browser',
    'sogouexplorer': 'Sogou Browser',
    'sogou browser': 'Sogou Browser',
    '搜狗浏览器': 'Sogou Browser',
    'code': 'VS Code',
    'vscode': 'VS Code',
    'visual studio code': 'VS Code',
    'vs code': 'VS Code',
    'cursor': 'Cursor',
    'wechat': 'WeChat',
    'weixin': 'WeChat',
    '微信': 'WeChat',
    'wecom': 'WeCom',
    '企业微信': 'WeCom',
    'qq': 'QQ',
    'notion': 'Notion',
    'obsidian': 'Obsidian',
    'slack': 'Slack',
    'discord': 'Discord',
    'winword': 'Microsoft Word',
    'word': 'Microsoft Word',
    'excel': 'Microsoft Excel',
    'powerpnt': 'Microsoft PowerPoint',
    'powerpoint': 'Microsoft PowerPoint',
    'outlook': 'Microsoft Outlook',
    'explorer': 'File Explorer',
    'windowsterminal': 'Windows Terminal',
    'windows terminal': 'Windows Terminal',
    'powershell': 'PowerShell',
    'pwsh': 'PowerShell',
    'cmd': 'Command Prompt',
    'gnome-terminal': 'GNOME Terminal',
    'gnome-terminal-server': 'GNOME Terminal',
    'xfce4-terminal': 'Xfce Terminal',
    'konsole': 'Konsole',
    'tilix': 'Tilix',
    'terminator': 'Terminator',
    'nemo': 'Nemo',
    'nautilus': 'Files',
    'org.gnome.nautilus': 'Files',
    'thunar': 'Thunar',
    'dolphin': 'Dolphin',
}


def normalize_display_app_name(app_name: str) -> str:
    trimmed = (app_name or '').strip().removesuffix('.exe').removesuffix('.EXE').strip()
    if not trimmed:
        return 'Unknown App'
    return _DISPLAY_NAME_MAP.get(trimmed.lower(), trimmed)


def is_system_process(app_name: str) -> bool:
    normalized = (app_name or '').strip().lower().removesuffix('.exe')
    return normalized in _SYSTEM_PROCESS_NAMES


def is_window_eligible(info: ActiveWindowInfo | None) -> bool:
    if info is None:
        return False
    title = info.window_title.strip().lower()
    app_name = info.app_name.strip().lower()
    if not title:
        return False
    if title in _IGNORED_WINDOW_NAMES or app_name in _IGNORED_WINDOW_NAMES:
        return False
    if is_system_process(app_name):
        return False
    return True
