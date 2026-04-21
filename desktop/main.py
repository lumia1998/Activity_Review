from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
import webbrowser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import webview

from backend.app.services.data_service import data_dir_path
from backend.app.services.config_service import load_config, save_config

from .tray import create_tray_controller
from .single_instance import SingleInstanceManager, notify_existing_instance
from .windows import WindowState

logger = logging.getLogger(__name__)

FRONTEND_DEV_URL = 'http://127.0.0.1:5173'

# ── Path resolution (dev vs PyInstaller) ────────────────────────────────────

def _is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


def _get_base_path() -> Path:
    """Return the base path for bundled resources.

    When running from a PyInstaller bundle ``sys._MEIPASS`` points to the
    temporary extraction directory.  In development mode we fall back to the
    normal project root (one level above this file).
    """
    if _is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BASE_PATH = _get_base_path()
DIST_INDEX = _BASE_PATH / 'dist' / 'index.html'
RUNTIME_STATE_PATH = data_dir_path() / 'runtime_state.json'
WINDOW_LABEL = 'main'

API_ROOT = 'http://127.0.0.1:8000'
API_BASE = f'{API_ROOT}/api'
RECORDER_INTERVAL = 20  # seconds between activity ticks
_WINDOW_APIS: dict[str, 'DesktopApi'] = {}

# ── Embedded backend (subprocess) ────────────────────────────────────────────

_backend_process: 'subprocess.Popen | None' = None


def _build_backend_cmd() -> list[str]:
    """Return the command to start the backend server."""
    if _is_frozen():
        # In frozen mode, re-invoke the EXE in backend-only mode via a dedicated
        # backend_server entry point bundled alongside the EXE, or use the same
        # EXE with an env flag.  We use a standalone uvicorn invocation instead.
        internal = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        # Use the bundled python via the EXE's own interpreter path trick:
        # PyInstaller exposes sys.executable as the EXE.  We cannot call it
        # directly for a sub-module, so we run uvicorn via the bundled Python.
        exe_dir = Path(sys.executable).parent
        # The bundled pythonXY.dll is in _internal; we need the python binary.
        # PyInstaller does not ship a standalone python.exe, so we run the
        # backend logic in a thread instead (see _start_backend_thread below).
        return []  # signals: use thread mode
    # Development mode: use current interpreter + uvicorn
    return [
        sys.executable, '-m', 'uvicorn',
        'backend.app.main:app',
        '--host', '127.0.0.1',
        '--port', '8000',
        '--log-level', 'info',
    ]


def _run_backend_thread() -> None:
    """Run uvicorn in a background thread (used in frozen mode)."""
    import asyncio
    import platform as _platform
    if _platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    import uvicorn
    from backend.app.main import app as _app
    uvicorn.run(_app, host='127.0.0.1', port=8000, log_level='info')


_backend_thread: 'threading.Thread | None' = None


def _start_backend() -> None:
    """Launch the FastAPI backend — subprocess in dev, thread in frozen mode."""
    global _backend_process, _backend_thread
    cmd = _build_backend_cmd()
    if cmd:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        _backend_process = proc
    else:
        t = threading.Thread(target=_run_backend_thread, daemon=True, name='uvicorn-backend')
        t.start()
        _backend_thread = t


def _stop_backend() -> None:
    """Terminate the backend process (subprocess mode only; thread is daemon)."""
    global _backend_process
    if _backend_process is not None:
        try:
            _backend_process.terminate()
            _backend_process.wait(timeout=5)
        except Exception:
            try:
                _backend_process.kill()
            except Exception:
                pass
    _backend_process = None


def _wait_for_backend(timeout: int = 30) -> bool:
    """Block until the backend /health endpoint responds OK."""
    for _ in range(timeout):
        if _api_ping():
            logger.info('Backend is ready')
            return True
        time.sleep(1)
    logger.error('Backend did not become ready within %ds', timeout)
    return False


def resolve_start_url() -> str:
    if _is_frozen() or DIST_INDEX.exists():
        return f'{API_ROOT}/'
    return FRONTEND_DEV_URL


def resolve_version() -> str:
    try:
        return version('activity-review')
    except PackageNotFoundError:
        return '0.1.0'


def _load_runtime_state() -> dict[str, Any]:
    if not RUNTIME_STATE_PATH.exists():
        return {}
    try:
        return json.loads(RUNTIME_STATE_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_runtime_state(patch: dict[str, Any]) -> None:
    state = _load_runtime_state()
    state.update(patch)
    RUNTIME_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


# ── Recorder thread ─────────────────────────────────────────────────────────

def _api_post(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """POST JSON to local FastAPI, return parsed response or None."""
    url = f'{API_BASE}{path}'
    data = json.dumps(payload or {}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, Exception):
        return None


def _api_get(path: str) -> dict[str, Any] | None:
    """GET from local FastAPI."""
    url = f'{API_BASE}{path}'
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, Exception):
        return None


def _load_desktop_state() -> dict[str, bool]:
    state = _load_runtime_state()
    config = load_config()
    return {
        'is_recording': bool(state.get('is_recording', True)),
        'is_paused': bool(state.get('is_paused', False)),
        'lightweight_mode': bool(config.get('lightweight_mode', False)),
    }


def _api_ping() -> bool:
    try:
        with urllib.request.urlopen(f'{API_ROOT}/health', timeout=5) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
            return payload.get('status') == 'ok'
    except (urllib.error.URLError, OSError, json.JSONDecodeError, Exception):
        return False


def _recorder_loop(stop_event: threading.Event) -> None:
    """Background thread that periodically captures foreground window activity.

    Each tick:
    1. Check if recording is paused (via runtime state file)
    2. Get foreground window info via monitor_service
    3. Enrich with browser URL via browser_service
    4. POST to FastAPI /api/runtime/activity-tick
    """
    logger.info('Recorder thread started')

    # Wait for FastAPI to be available
    for attempt in range(30):
        if stop_event.is_set():
            return
        if _api_ping():
            break
        time.sleep(1)
    else:
        logger.error('FastAPI not available after 30s, recorder exiting')
        return

    while not stop_event.is_set():
        try:
            state = _load_runtime_state()
            is_paused = state.get('is_paused', False)
            is_recording = state.get('is_recording', True)

            if is_recording and not is_paused:
                _capture_tick()
        except Exception as exc:
            logger.debug('Recorder tick error: %s', exc)

        # Sleep in small increments to respond quickly to stop_event
        for _ in range(RECORDER_INTERVAL):
            if stop_event.is_set():
                break
            time.sleep(1)

    logger.info('Recorder thread stopped')


def _capture_tick() -> None:
    """Capture a single activity tick from system state."""
    try:
        from backend.app.services.monitor_service import get_foreground_window_info, is_window_eligible
        from backend.app.services.browser_service import enrich_activity_payload
    except ImportError:
        return

    info = get_foreground_window_info()
    if not is_window_eligible(info):
        return

    payload = info.to_payload()
    payload = enrich_activity_payload(payload)

    # Remove internal fields not expected by the API
    payload.pop('hwnd', None)
    payload.pop('pid', None)

    _api_post('/runtime/activity-tick', payload)


# ── DesktopApi ──────────────────────────────────────────────────────────────

class DesktopApi:
    def __init__(self, app_version: str, window_state: WindowState) -> None:
        self.app_version = app_version
        self.window_state = window_state
        self._window: webview.Window | None = None
        self._stop_event = threading.Event()
        self._recorder_thread: threading.Thread | None = None
        self._single_instance: SingleInstanceManager | None = None

    def attach_window(self, window: webview.Window) -> None:
        self._window = window
        _WINDOW_APIS[self.currentWindowLabel] = self

    @property
    def currentWindowLabel(self) -> str:
        return self.window_state.label

    def _require_window(self) -> webview.Window:
        if self._window is None:
            raise RuntimeError('desktop window is not ready')
        return self._window

    def _dispatch_event(self, event_name: str, payload: Any = None) -> None:
        window = self._window
        if window is None:
            return
        detail = json.dumps(payload, ensure_ascii=False)
        script = (
            "window.dispatchEvent(new CustomEvent(" + json.dumps(event_name) + ", { detail: " + detail + " }));"
        )
        try:
            window.evaluate_js(script)
        except Exception:
            return

    def _sync_window_visibility(self, visible: bool) -> None:
        self.window_state.visible = bool(visible)
        if self.currentWindowLabel == WINDOW_LABEL:
            _save_runtime_state({'main_window_visible': bool(visible)})
        self._dispatch_event('window-visibility-changed', {'visible': bool(visible)})

    def inject_bridge(self) -> None:
        window = self._require_window()
        script = f"""
(() => {{
  const api = window.pywebview?.api;
  if (!api) return;
  window.__ACTICITY_DESKTOP__ = {{
    version: {json.dumps(self.app_version)},
    currentWindowLabel: {json.dumps(self.currentWindowLabel)},
    openExternal: (url) => api.openExternal(url),
    relaunch: () => api.relaunch(),
    getVersion: () => api.getVersion(),
    emitTo: (label, eventName, payload) => api.emitTo(label, eventName, payload),
    startDragging: () => Promise.resolve(),
    listenWindowEvent: (eventName, callback) => {{
      api.listenWindowEvent(eventName);
      const handler = (event) => callback({{ payload: event.detail }});
      window.addEventListener(eventName, handler);
      return Promise.resolve(async () => {{
        window.removeEventListener(eventName, handler);
      }});
    }},
    onWindowMoved: (callback) => {{
      api.onWindowMoved();
      const handler = (event) => callback({{ payload: event.detail }});
      window.addEventListener('window-moved', handler);
      return Promise.resolve(async () => {{
        window.removeEventListener('window-moved', handler);
      }});
    }},
    closeWindow: () => api.closeWindow(),
    hideWindow: () => api.hideWindow(),
    showWindow: () => api.showWindow(),
    minimizeWindow: () => api.minimizeWindow(),
    maximizeWindow: () => api.maximizeWindow(),
    unmaximizeWindow: () => api.unmaximizeWindow(),
    isMaximized: () => api.isMaximized(),
    isVisible: () => api.isVisible(),
    pickDirectory: (options) => api.pickDirectory(options || {{}}),
    confirm: (options) => api.confirm(options || {{}}),
  }};
  window.dispatchEvent(new CustomEvent('acticity-desktop-ready'));
}})();
"""
        window.evaluate_js(script)

    def _activate_existing_window(self) -> None:
        try:
            self.showWindow()
        except Exception:
            return

    def toggle_recording(self) -> None:
        """Toggle recording pause/resume via API."""
        state = _load_runtime_state()
        is_paused = state.get('is_paused', False)
        if is_paused:
            _api_post('/runtime/resume-recording')
        else:
            _api_post('/runtime/pause-recording')
        # Sync tray menu state
        if self._tray_controller:
            self._tray_controller.refresh_menu()

    def toggle_lightweight_mode(self) -> None:
        """Toggle lightweight mode (hide main window, keep tray)."""
        config = load_config()
        lightweight = bool(config.get('lightweight_mode', False))
        config['lightweight_mode'] = not lightweight
        save_config(config)
        if config['lightweight_mode']:
            self.hideWindow()
        else:
            self.showWindow()
        if self._tray_controller:
            self._tray_controller.refresh_menu()

    _tray_controller: Any = None

    # ── pywebview API methods ────────────────────────────────────────────

    def openExternal(self, url: str) -> bool:
        if not url:
            return False
        webbrowser.open(url)
        return True

    def relaunch(self) -> bool:
        window = self._require_window()
        window.load_url(resolve_start_url())
        return True

    def getVersion(self) -> str:
        return self.app_version

    def emitTo(self, label: str, event_name: str, payload: Any = None) -> bool:
        self._dispatch_event(event_name, payload)
        return True

    def listenWindowEvent(self, event_name: str) -> bool:
        return bool(event_name)

    def onWindowMoved(self) -> bool:
        return True

    def closeWindow(self) -> bool:
        return self.hideWindow()

    def hideWindow(self) -> bool:
        window = self._require_window()
        window.hide()
        self._sync_window_visibility(False)
        return True

    def showWindow(self) -> bool:
        window = self._require_window()
        window.show()
        try:
            window.restore()
        except Exception:
            pass
        self.window_state.minimized = False
        self._sync_window_visibility(True)
        return True

    def minimizeWindow(self) -> bool:
        window = self._require_window()
        window.minimize()
        self.window_state.minimized = True
        return True

    def maximizeWindow(self) -> bool:
        window = self._require_window()
        try:
            window.maximize()
        except Exception:
            return False
        self.window_state.maximized = True
        self._dispatch_event('window-maximized', {'maximized': True})
        return True

    def unmaximizeWindow(self) -> bool:
        window = self._require_window()
        try:
            window.restore()
        except Exception:
            return False
        self.window_state.maximized = False
        self.window_state.minimized = False
        self._dispatch_event('window-maximized', {'maximized': False})
        return True

    def isMaximized(self) -> bool:
        return bool(self.window_state.maximized)

    def isVisible(self) -> bool:
        return bool(self.window_state.visible)

    def pickDirectory(self, options: dict[str, Any] | None = None) -> str | None:
        window = self._require_window()
        options = options or {}
        result = window.create_file_dialog(
            webview.FileDialog.FOLDER,
            directory=options.get('defaultPath') or None,
        )
        if not result:
            return None
        return result[0]

    def confirm(self, options: dict[str, Any] | None = None) -> bool:
        window = self._require_window()
        options = options or {}
        title = str(options.get('title') or 'Activity Review')
        message = str(options.get('message') or '')
        return bool(window.create_confirmation_dialog(title, message))


# ── Bootstrap ────────────────────────────────────────────────────────────────

def _bootstrap(window: webview.Window, desktop_api: DesktopApi) -> None:
    stop_event = desktop_api._stop_event
    tray = create_tray_controller(
        on_show=desktop_api.showWindow,
        on_hide=desktop_api.hideWindow,
        on_quit=window.destroy,
        on_toggle_recording=desktop_api.toggle_recording,
        on_toggle_lightweight=desktop_api.toggle_lightweight_mode,
        get_state=_load_desktop_state,
    )
    desktop_api._tray_controller = tray
    tray.start(visible=bool(_load_runtime_state().get('dock_visible', True)))

    recorder = threading.Thread(target=_recorder_loop, args=(stop_event,), daemon=True)
    recorder.start()
    desktop_api._recorder_thread = recorder

    def on_loaded(*_args: Any) -> None:
        desktop_api.inject_bridge()

    def on_moved(x: int, y: int) -> None:
        desktop_api._dispatch_event('window-moved', {'x': x, 'y': y})

    def on_shown(*_args: Any) -> None:
        desktop_api._sync_window_visibility(True)

    def on_minimized(*_args: Any) -> None:
        desktop_api.window_state.minimized = True
        desktop_api.window_state.maximized = False
        desktop_api._dispatch_event('window-minimized', {'minimized': True})

    def on_restored(*_args: Any) -> None:
        desktop_api.window_state.minimized = False
        desktop_api.window_state.maximized = False
        desktop_api._dispatch_event('window-minimized', {'minimized': False})
        desktop_api._dispatch_event('window-maximized', {'maximized': False})
        desktop_api._sync_window_visibility(True)

    def on_closing(*_args: Any) -> bool:
        stop_event.set()
        _stop_backend()
        tray.stop()
        if desktop_api._single_instance:
            desktop_api._single_instance.close()
        return True

    window.events.loaded += on_loaded
    window.events.moved += on_moved
    window.events.shown += on_shown
    window.events.minimized += on_minimized
    window.events.restored += on_restored
    window.events.closing += on_closing

    def sync_runtime_preferences() -> None:
        last_dock_visible: bool | None = None
        while not stop_event.is_set():
            state = _load_runtime_state()
            dock_visible = bool(state.get('dock_visible', True))
            if dock_visible != last_dock_visible:
                if dock_visible:
                    tray.show()
                else:
                    tray.hide()
                last_dock_visible = dock_visible

            if bool(state.get('main_window_visible')) and not desktop_api.isVisible():
                desktop_api.showWindow()
            time.sleep(1)

    def _start_sync() -> None:
        # Wait for page to finish loading before starting sync loop
        # to avoid WinForms Invoke contention during WebView2 initialization
        window.events.loaded.wait(timeout=30)
        threading.Thread(target=sync_runtime_preferences, daemon=True).start()

    threading.Thread(target=_start_sync, daemon=True).start()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    # ── Start embedded backend ──────────────────────────────────────────
    if not _api_ping():
        logger.info('Starting embedded backend ...')
        _start_backend()
        if not _wait_for_backend(timeout=30):
            logger.critical('Cannot start backend – aborting')
            _stop_backend()
            return
    else:
        logger.info('Backend already running, skipping embedded launch')

    # ── Desktop window ──────────────────────────────────────────────────
    window_state = WindowState(label=WINDOW_LABEL)
    desktop_api = DesktopApi(app_version=resolve_version(), window_state=window_state)
    single_instance = SingleInstanceManager(on_activate=desktop_api._activate_existing_window)
    if not single_instance.acquire():
        notify_existing_instance()
        _stop_backend()
        return
    desktop_api._single_instance = single_instance

    window = webview.create_window(
        title='Activity Review',
        url=resolve_start_url(),
        js_api=desktop_api,
        width=1000,
        height=700,
        min_size=(800, 600),
    )
    desktop_api.attach_window(window)

    # Disable SmartScreen only; --force-renderer-accessibility=disabled causes hangs on WebView2 147+
    os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = '--disable-features=msSmartScreenProtection'

    # Use a persistent cache dir so WebView2 doesn't re-initialize on every launch
    webview_cache = data_dir_path() / 'webview-cache'
    webview_cache.mkdir(parents=True, exist_ok=True)

    webview.start(
        lambda: _bootstrap(window, desktop_api),
        storage_path=str(webview_cache),
        private_mode=False,
    )

    # ── Cleanup ─────────────────────────────────────────────────────────
    _stop_backend()
    logger.info('Application exited')


if __name__ == '__main__':
    main()