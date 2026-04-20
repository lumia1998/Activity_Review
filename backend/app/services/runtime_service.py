from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .data_service import data_dir_path, get_activity, get_connection, initialize_database, table_exists

RUNTIME_STATE_FILE = 'runtime_state.json'
DEFAULT_ACTIVITY_DURATION = 20

_last_screenshot_hash: str | None = None
_last_screenshot_timestamp: int = 0
_last_activity_context: str | None = None

_RUNTIME_STATE: dict[str, Any] = {
    'is_recording': True,
    'is_paused': False,
    'last_activity_timestamp': 0,
    'main_window_visible': True,
    'dock_visible': True,
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


def _try_perform_ocr(image_path: str | None) -> str | None:
    if not image_path:
        return None
    try:
        from .ocr_service import perform_ocr, filter_sensitive_text
        raw_text = perform_ocr(image_path)
        if raw_text:
            return filter_sensitive_text(raw_text)
    except Exception:
        pass
    return None


def _check_idle() -> bool:
    try:
        from .idle_service import is_user_idle
        if is_user_idle():
            return True
    except Exception:
        pass
    return False


def _check_screen_locked() -> bool:
    try:
        from .idle_service import is_screen_locked
        return is_screen_locked()
    except Exception:
        return False


def capture_activity_tick(payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    global _last_screenshot_hash, _last_screenshot_timestamp, _last_activity_context

    payload = payload or {}
    if _RUNTIME_STATE.get('is_paused'):
        return None
    if _check_screen_locked() or _check_idle():
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

    current_context = f'{app_name}|{window_title}'
    screenshot_path = None
    ocr_text = None

    try:
        from .screenshot_service import capture_screenshot, is_idle_by_screenshot
        screenshot_result = capture_screenshot()
        if screenshot_result:
            screenshot_path = screenshot_result.get('path')
            current_hash = screenshot_result.get('hash', '')
            if is_idle_by_screenshot(current_hash, _last_screenshot_hash):
                _last_screenshot_hash = current_hash
                _last_activity_context = current_context
                return None
            _last_screenshot_hash = current_hash
            _last_screenshot_timestamp = now_ts
    except Exception:
        screenshot_path = None

    if screenshot_path:
        ocr_text = _try_perform_ocr(screenshot_path)

    _last_activity_context = current_context

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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now_ts, app_name, window_title, screenshot_path, ocr_text, category, duration,
             browser_url, executable_path, semantic_category, None),
        )
        connection.commit()
        activity_id = int(cursor.lastrowid)

    _RUNTIME_STATE['last_activity_timestamp'] = now_ts
    _save_runtime_state()
    return get_activity(activity_id)


def set_dock_visibility(visible: bool) -> bool:
    _RUNTIME_STATE['dock_visible'] = bool(visible)
    _save_runtime_state()
    return bool(_RUNTIME_STATE['dock_visible'])
