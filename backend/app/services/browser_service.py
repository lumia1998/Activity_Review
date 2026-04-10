from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


BROWSER_FAMILY_PATTERNS = {
    'chrome': ('chrome', 'google chrome'),
    'edge': ('msedge', 'edge', 'microsoft edge'),
    'brave': ('brave', 'brave browser'),
    'vivaldi': ('vivaldi',),
    'opera': ('opera',),
    'chromium': ('chromium',),
    'firefox': ('firefox',),
    'zen': ('zen', 'zen browser'),
    'librewolf': ('librewolf',),
    'waterfox': ('waterfox',),
    'safari': ('safari',),
    'arc': ('arc',),
    'orion': ('orion',),
    'qqbrowser': ('qqbrowser', 'qq browser', 'qq浏览器'),
    '360browser': ('360se', '360chrome', '360 browser', '360浏览器'),
    'sogou': ('sogouexplorer', 'sogou browser', '搜狗浏览器'),
}

_BROWSER_DISPLAY_NAMES = {
    'chrome': 'Google Chrome',
    'edge': 'Microsoft Edge',
    'brave': 'Brave Browser',
    'vivaldi': 'Vivaldi',
    'opera': 'Opera',
    'chromium': 'Chromium',
    'firefox': 'Firefox',
    'zen': 'Zen Browser',
    'librewolf': 'LibreWolf',
    'waterfox': 'Waterfox',
    'safari': 'Safari',
    'arc': 'Arc',
    'orion': 'Orion',
    'qqbrowser': 'QQ Browser',
    '360browser': '360 Browser',
    'sogou': 'Sogou Browser',
}

_URL_PATTERN = re.compile(
    r"(?i)(https?://[^\s<>\"']+|(?:localhost|(?:[a-z0-9-]+\.)+[a-z]{2,}|(?:\d{1,3}\.){3}\d{1,3})(?::\d{2,5})?(?:/[^\s<>\"']*)?)"
)


def detect_browser_family(app_name: str | None, executable_path: str | None = None) -> str | None:
    corpus = f"{app_name or ''} {executable_path or ''}".lower()
    for family, patterns in BROWSER_FAMILY_PATTERNS.items():
        if any(pattern in corpus for pattern in patterns):
            return family
    return None


def normalize_browser_name(app_name: str | None, executable_path: str | None = None) -> str | None:
    family = detect_browser_family(app_name, executable_path)
    if not family:
        return None
    return _BROWSER_DISPLAY_NAMES.get(family, family.title())


def _trim_url_candidate(value: str) -> str:
    return value.strip().strip('"\'`()[]{}<>,;|')


def _normalize_url(candidate: str | None) -> str | None:
    value = _trim_url_candidate(candidate or '')
    if not value:
        return None
    parsed_input = value if '://' in value else f'https://{value}'
    try:
        parsed = urlparse(parsed_input)
    except ValueError:
        return None
    host = (parsed.hostname or '').strip().lower()
    if not host:
        return None
    path = parsed.path or ''
    query = f'?{parsed.query}' if parsed.query else ''
    fragment = f'#{parsed.fragment}' if parsed.fragment else ''
    if '://' in value:
        scheme = parsed.scheme or 'https'
        port = f':{parsed.port}' if parsed.port else ''
        return f'{scheme}://{host}{port}{path}{query}{fragment}'.rstrip('/')
    port = f':{parsed.port}' if parsed.port else ''
    return f'{host}{port}{path}{query}{fragment}'.rstrip('/')


def _extract_url_like_text(window_title: str | None) -> str | None:
    title = (window_title or '').strip()
    if not title:
        return None
    match = _URL_PATTERN.search(title)
    if match:
        return _normalize_url(match.group(0))
    return None


def _extract_url_from_title_segments(window_title: str | None) -> str | None:
    title = (window_title or '').strip()
    if not title:
        return None
    for segment in re.split(r'\s+[\-–—|·•]\s+|\s+[\-–—|·•]|[\-–—|·•]\s+', title):
        normalized = _normalize_url(segment)
        if normalized:
            return normalized
    return None


def get_browser_url(app_name: str | None, window_title: str | None, executable_path: str | None = None) -> str | None:
    family = detect_browser_family(app_name, executable_path)
    if not family:
        return None
    return _extract_url_like_text(window_title) or _extract_url_from_title_segments(window_title)


def enrich_activity_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    normalized_browser_name = normalize_browser_name(
        data.get('appName'),
        data.get('executablePath'),
    )
    if normalized_browser_name:
        data['appName'] = normalized_browser_name
    if not data.get('browserUrl'):
        data['browserUrl'] = get_browser_url(
            data.get('appName'),
            data.get('windowTitle'),
            data.get('executablePath'),
        )
    return data
