from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config_service import load_config
from .data_service import data_dir_path, get_activity, get_connection, initialize_database, table_exists

RUNTIME_STATE_FILE = 'runtime_state.json'
DEFAULT_ACTIVITY_DURATION = 20

_RUNTIME_STATE: dict[str, Any] = {
    'is_recording': True,
    'is_paused': False,
    'last_activity_timestamp': 0,
    'main_window_visible': True,
    'dock_visible': True,
    'avatar_position': None,
}


def _runtime_state_path() -> Path:
    return data_dir_path() / RUNTIME_STATE_FILE


def _load_runtime_state_from_disk() -> None:
    path = _runtime_state_path()
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return
    if isinstance(payload, dict):
        _RUNTIME_STATE.update(payload)


def _save_runtime_state() -> None:
    path = _runtime_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_RUNTIME_STATE, ensure_ascii=False, indent=2), encoding='utf-8')


_load_runtime_state_from_disk()


def get_recording_state() -> list[bool]:
    return [bool(_RUNTIME_STATE.get('is_recording', True)), bool(_RUNTIME_STATE.get('is_paused', False))]


def pause_recording() -> list[bool]:
    _RUNTIME_STATE['is_recording'] = True
    _RUNTIME_STATE['is_paused'] = True
    _RUNTIME_STATE['main_window_visible'] = False
    _save_runtime_state()
    return get_recording_state()


def resume_recording() -> list[bool]:
    _RUNTIME_STATE['is_recording'] = True
    _RUNTIME_STATE['is_paused'] = False
    _RUNTIME_STATE['main_window_visible'] = True
    _save_runtime_state()
    return get_recording_state()


def _normalize_text(value: Any, fallback: str = '') -> str:
    text = str(value or '').strip()
    return text or fallback


def capture_activity_tick(payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    payload = payload or {}
    if _RUNTIME_STATE.get('is_paused'):
        return None

    app_name = _normalize_text(payload.get('appName'), 'Activity Review')
    window_title = _normalize_text(payload.get('windowTitle'), app_name)
    browser_url = _normalize_text(payload.get('browserUrl')) or None
    executable_path = _normalize_text(payload.get('executablePath')) or None
    category = _normalize_text(payload.get('category'), 'development')
    semantic_category = _normalize_text(payload.get('semanticCategory')) or None

    duration = int(payload.get('duration') or DEFAULT_ACTIVITY_DURATION)
    now_ts = int(datetime.now().timestamp())
    _RUNTIME_STATE['main_window_visible'] = False

    initialize_database()
    with get_connection() as connection:
        if not table_exists(connection, 'activities'):
            return None

        previous = connection.execute(
            """
            SELECT id, timestamp, duration, app_name, window_title, browser_url, executable_path
            FROM activities
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

        if previous:
            same_context = (
                (previous['app_name'] or '') == app_name
                and (previous['window_title'] or '') == window_title
                and (previous['browser_url'] or None) == browser_url
                and (previous['executable_path'] or None) == executable_path
            )
            if same_context and now_ts - int(previous['timestamp'] or 0) <= max(duration * 2, 45):
                connection.execute(
                    """
                    UPDATE activities
                    SET timestamp = ?, duration = COALESCE(duration, 0) + ?
                    WHERE id = ?
                    """,
                    (now_ts, duration, previous['id']),
                )
                connection.commit()
                _RUNTIME_STATE['last_activity_timestamp'] = now_ts
                _save_runtime_state()
                return get_activity(int(previous['id']))

        cursor = connection.execute(
            """
            INSERT INTO activities (
                timestamp,
                app_name,
                window_title,
                screenshot_path,
                ocr_text,
                category,
                duration,
                browser_url,
                executable_path,
                semantic_category,
                semantic_confidence
            ) VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?)
            """,
            (now_ts, app_name, window_title, category, duration, browser_url, executable_path, semantic_category, None),
        )
        connection.commit()
        activity_id = int(cursor.lastrowid)

    _RUNTIME_STATE['last_activity_timestamp'] = now_ts
    _save_runtime_state()
    return get_activity(activity_id)


def get_avatar_state() -> dict[str, Any]:
    config = load_config()
    latest_activity = None
    initialize_database()
    with get_connection() as connection:
        if table_exists(connection, 'activities'):
            latest_activity = connection.execute(
                """
                SELECT app_name, window_title
                FROM activities
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
                """
            ).fetchone()

    is_paused = bool(_RUNTIME_STATE.get('is_paused'))
    main_window_visible = bool(_RUNTIME_STATE.get('main_window_visible', True))
    app_name = (latest_activity['app_name'] if latest_activity else None) or 'Activity Review'
    window_title = (latest_activity['window_title'] if latest_activity else None) or '待命中'
    hint = '录制已暂停，随时可以继续。' if is_paused else '准备陪你开始工作'
    context_label = '已暂停' if is_paused else window_title[:24]

    return {
        'mode': 'idle' if is_paused else 'working',
        'appName': app_name,
        'contextLabel': context_label,
        'hint': hint,
        'isIdle': is_paused,
        'isGeneratingReport': False,
        'avatarOpacity': float(config.get('avatar_opacity') or 0.82),
        'mainWindowVisible': main_window_visible,
        'position': _RUNTIME_STATE.get('avatar_position'),
    }


def save_avatar_position(x: int, y: int) -> dict[str, int]:
    _RUNTIME_STATE['avatar_position'] = {'x': int(x), 'y': int(y)}
    _save_runtime_state()
    return _RUNTIME_STATE['avatar_position']


def set_dock_visibility(visible: bool) -> bool:
    _RUNTIME_STATE['dock_visible'] = bool(visible)
    _save_runtime_state()
    return bool(_RUNTIME_STATE['dock_visible'])


def show_main_window(source_window_label: str | None = None) -> bool:
    _RUNTIME_STATE['main_window_visible'] = True
    if source_window_label:
        _RUNTIME_STATE['last_source_window_label'] = source_window_label
    _save_runtime_state()
    return True
