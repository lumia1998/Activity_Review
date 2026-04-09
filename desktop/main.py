from __future__ import annotations

import json
import threading
import time
import webbrowser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import webview

from backend.app.services.data_service import data_dir_path

from .tray import create_tray_controller
from .windows import WindowState

FRONTEND_DEV_URL = 'http://127.0.0.1:5173'
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_INDEX = PROJECT_ROOT / 'dist' / 'index.html'
RUNTIME_STATE_PATH = data_dir_path() / 'runtime_state.json'
WINDOW_LABEL = 'main'


def resolve_start_url() -> str:
    if DIST_INDEX.exists():
        return DIST_INDEX.as_uri()
    return FRONTEND_DEV_URL


def resolve_version() -> str:
    try:
        return version('acticity-review')
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


class DesktopApi:
    def __init__(self, app_version: str, window_state: WindowState) -> None:
        self.app_version = app_version
        self.window_state = window_state
        self.window: webview.Window | None = None

    def attach_window(self, window: webview.Window) -> None:
        self.window = window

    @property
    def currentWindowLabel(self) -> str:
        return self.window_state.label

    def _require_window(self) -> webview.Window:
        if self.window is None:
            raise RuntimeError('desktop window is not ready')
        return self.window

    def _dispatch_event(self, event_name: str, payload: Any = None) -> None:
        window = self.window
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
        if label and label != self.currentWindowLabel:
            return False
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
        title = str(options.get('title') or 'Acticity Review')
        message = str(options.get('message') or '')
        return bool(window.create_confirmation_dialog(title, message))


def _bootstrap(window: webview.Window, desktop_api: DesktopApi) -> None:
    stop_event = threading.Event()
    tray = create_tray_controller(
        on_show=desktop_api.showWindow,
        on_hide=desktop_api.hideWindow,
        on_quit=window.destroy,
    )
    tray.start(visible=bool(_load_runtime_state().get('dock_visible', True)))

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
        tray.stop()
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

    threading.Thread(target=sync_runtime_preferences, daemon=True).start()


def main() -> None:
    window_state = WindowState(label=WINDOW_LABEL)
    desktop_api = DesktopApi(app_version=resolve_version(), window_state=window_state)
    window = webview.create_window(
        title='Acticity Review',
        url=resolve_start_url(),
        js_api=desktop_api,
        width=1000,
        height=700,
        min_size=(800, 600),
    )
    desktop_api.attach_window(window)
    webview.start(_bootstrap, window, desktop_api)


if __name__ == '__main__':
    main()
