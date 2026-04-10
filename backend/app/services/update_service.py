from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..core.paths import resolve_data_dir

UPDATE_SETTINGS_FILE = 'update_settings.json'
LATEST_RELEASE_API = 'https://api.github.com/repos/lumia1998/Acticity_Review/releases/latest'
RELEASES_PAGE_URL = 'https://github.com/lumia1998/Acticity_Review/releases/latest'


def _update_settings_path() -> Path:
    return resolve_data_dir() / UPDATE_SETTINGS_FILE


def _load_update_settings() -> dict[str, Any]:
    path = _update_settings_path()
    if not path.exists():
        return {'autoCheck': True, 'lastCheckTime': 0, 'checkIntervalHours': 24}

    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {'autoCheck': True, 'lastCheckTime': 0, 'checkIntervalHours': 24}

    if not isinstance(payload, dict):
        return {'autoCheck': True, 'lastCheckTime': 0, 'checkIntervalHours': 24}
    return {
        'autoCheck': bool(payload.get('autoCheck', True)),
        'lastCheckTime': int(payload.get('lastCheckTime') or 0),
        'checkIntervalHours': int(payload.get('checkIntervalHours') or 24),
    }


def _save_update_settings(settings: dict[str, Any]) -> dict[str, Any]:
    path = _update_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')
    return settings


def _normalize_version(version: str) -> tuple[int, ...]:
    normalized = str(version or '').strip().lstrip('vV')
    parts: list[int] = []
    for segment in normalized.split('.'):
        digits = ''.join(ch for ch in segment if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts)


def _fetch_latest_release() -> dict[str, Any]:
    request = Request(
        LATEST_RELEASE_API,
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'Acticity-Review-Python-Rebuild',
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as error:
        raise RuntimeError(f'GitHub release API returned HTTP {error.code}') from error
    except URLError as error:
        raise RuntimeError(f'GitHub release API request failed: {error.reason}') from error


def _platform_label() -> str:
    if sys.platform == 'win32':
        return 'windows'
    if sys.platform == 'darwin':
        return 'macos'
    if sys.platform.startswith('linux'):
        return 'linux'
    return sys.platform


def check_github_update(current_version: str) -> dict[str, Any]:
    release = _fetch_latest_release()
    latest_version = str(release.get('tag_name') or '').strip() or str(current_version)
    release_url = str(release.get('html_url') or RELEASES_PAGE_URL)
    published_at = str(release.get('published_at') or '')

    available = _normalize_version(latest_version) > _normalize_version(current_version)

    return {
        'available': available,
        'currentVersion': current_version,
        'latestVersion': latest_version,
        'releaseUrl': release_url,
        'publishedAt': published_at,
        'autoUpdateReady': False,
        'platform': _platform_label(),
        'manualOnly': True,
        'notes': 'Python 重构版当前使用手动下载安装流程，不再依赖 Tauri 内建 updater。',
    }


def update_last_check_time() -> dict[str, Any]:
    settings = _load_update_settings()
    settings['lastCheckTime'] = int(datetime.now(timezone.utc).timestamp())
    return _save_update_settings(settings)


def should_check_updates() -> bool:
    settings = _load_update_settings()
    if not settings.get('autoCheck', True):
        return False

    last_check_time = int(settings.get('lastCheckTime') or 0)
    interval_hours = max(int(settings.get('checkIntervalHours') or 24), 1)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    return now_ts - last_check_time >= interval_hours * 3600


def download_and_install_github_update(expected_version: str | None = None) -> dict[str, Any]:
    release_info = check_github_update(expected_version or '0.0.0')
    return {
        'started': False,
        'manual': True,
        'platform': _platform_label(),
        'releaseUrl': release_info.get('releaseUrl') or RELEASES_PAGE_URL,
        'version': release_info.get('latestVersion') or expected_version,
        'message': '当前版本使用手动下载更新包流程。',
    }


def quit_app_for_update() -> bool:
    raise SystemExit(0)
