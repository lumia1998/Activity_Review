from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config_service import load_config
from .data_service import data_dir_path, get_activity, get_connection, initialize_database, table_exists

RUNTIME_STATE_FILE = 'runtime_state.json'
DEFAULT_ACTIVITY_DURATION = 20

# 上一次截图哈希（用于空闲检测）
_last_screenshot_hash: str | None = None
# 连续截图相似命中次数
_screenshot_idle_hits: int = 0
# 上一次截图时间（用于间隔截图策略）
_last_screenshot_timestamp: int = 0
# 上一次活动上下文（用于检测应用切换）
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


def _try_capture_screenshot() -> str | None:
    """尝试捕获截图，返回截图路径或 None"""
    try:
        from .screenshot_service import capture_screenshot
        result = capture_screenshot()
        if result:
            return result.get('path')
    except Exception:
        pass
    return None


def _auto_classify_app(app_name: str, window_title: str | None, executable_path: str | None) -> str | None:
    """自动分类应用，返回分类名或 None（如果前端已提供分类）"""
    try:
        from .app_classifier_service import classify_app
        config = load_config()
        rules = config.get('app_category_rules') or []
        return classify_app(app_name, window_title, executable_path, rules)
    except Exception:
        return None


def _screenshot_interval_seconds(storage_config: dict[str, Any]) -> int:
    value = storage_config.get('screenshot_interval_seconds')
    try:
        return max(30, int(value or 180))
    except (TypeError, ValueError):
        return 180


def _should_capture_screenshot(current_context: str, now_ts: int, storage_config: dict[str, Any]) -> bool:
    interval_seconds = _screenshot_interval_seconds(storage_config)
    if _last_activity_context is None:
        return True
    if current_context != _last_activity_context:
        return True
    return now_ts - _last_screenshot_timestamp >= interval_seconds


def capture_activity_tick(payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    global _last_screenshot_hash, _screenshot_idle_hits, _last_screenshot_timestamp, _last_activity_context

    payload = payload or {}
    if _RUNTIME_STATE.get('is_paused'):
        return None

    # 检查屏幕锁定
    if _check_screen_locked():
        return None

    # 检查空闲状态
    if _check_idle():
        return None

    app_name = _normalize_text(payload.get('appName'), 'Activity Review')
    window_title = _normalize_text(payload.get('windowTitle'), app_name)
    browser_url = _normalize_text(payload.get('browserUrl')) or None
    executable_path = _normalize_text(payload.get('executablePath')) or None
    category = _normalize_text(payload.get('category'), '') or None
    semantic_category = _normalize_text(payload.get('semanticCategory')) or None

    # 自动分类（如果前端没提供分类）
    if not category:
        category = _auto_classify_app(app_name, window_title, executable_path) or 'other'

    # 语义分类置信度（classify_semantic 尚未实现，保留变量供 INSERT 使用）
    semantic_confidence: float | None = None

    duration = int(payload.get('duration') or DEFAULT_ACTIVITY_DURATION)
    now_ts = int(datetime.now().timestamp())
    _RUNTIME_STATE['main_window_visible'] = False

    # 检测应用切换，切换时捕获截图
    current_context = f'{app_name}|{window_title}'

    screenshot_path = None
    ocr_text = None
    config = load_config()
    storage_config = config.get('storage') or {}
    screenshots_enabled = storage_config.get('screenshots_enabled', True)
    ocr_enabled = storage_config.get('ocr_enabled', True)
    should_capture = screenshots_enabled and _should_capture_screenshot(current_context, now_ts, storage_config)

    if should_capture:
        try:
            from .screenshot_service import capture_screenshot, get_screenshot_similarity
            screenshot_result = capture_screenshot()
            if screenshot_result:
                screenshot_path = screenshot_result.get('path')
                current_hash = screenshot_result.get('hash', '')

                # 连续截图稳定判定（屏幕内容无变化）
                screenshot_idle_enabled = storage_config.get('screenshot_idle_enabled', True)
                consecutive_threshold = max(1, int(storage_config.get('screenshot_idle_consecutive_hits', 3)))

                if screenshot_idle_enabled and _last_screenshot_hash:
                    similarity = get_screenshot_similarity(current_hash, _last_screenshot_hash)
                    if similarity.get('is_similar'):
                        _screenshot_idle_hits += 1
                    else:
                        _screenshot_idle_hits = 0

                    if _screenshot_idle_hits >= consecutive_threshold:
                        _last_screenshot_hash = current_hash
                        _last_activity_context = current_context
                        return None
                else:
                    _screenshot_idle_hits = 0

                _last_screenshot_hash = current_hash
                _last_screenshot_timestamp = now_ts
        except Exception:
            screenshot_path = None

        if screenshot_path and ocr_enabled:
            ocr_text = _try_perform_ocr(screenshot_path)

    # 应用切换时重置截图稳定计数
    if current_context != _last_activity_context:
        _screenshot_idle_hits = 0

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
             browser_url, executable_path, semantic_category, semantic_confidence),
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


def show_main_window(source_window_label: str | None = None) -> bool:
    _RUNTIME_STATE['main_window_visible'] = True
    if source_window_label:
        _RUNTIME_STATE['last_source_window_label'] = source_window_label
    _save_runtime_state()
    return True
