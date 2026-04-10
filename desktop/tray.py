from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock, Thread
from typing import Callable

try:
    import pystray
except ImportError:  # pragma: no cover - optional runtime dependency
    pystray = None

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - optional runtime dependency
    Image = None
    ImageDraw = None


MenuAction = Callable[[], None]
StateProvider = Callable[[], dict[str, bool]]


@dataclass
class TrayController:
    on_show: MenuAction
    on_hide: MenuAction
    on_quit: MenuAction
    on_toggle_recording: MenuAction | None = None
    on_toggle_lightweight: MenuAction | None = None
    on_toggle_avatar: MenuAction | None = None
    get_state: StateProvider | None = None
    icon: object | None = None
    thread: Thread | None = None
    visible: bool = False
    _lock: RLock = field(default_factory=RLock)

    @property
    def supported(self) -> bool:
        return bool(pystray and Image and ImageDraw)

    def start(self, visible: bool = True) -> bool:
        if not self.supported:
            self.visible = False
            return False
        if visible:
            return self.show()
        return True

    def _menu_item(self, text: str, action: MenuAction | None, checked: Callable[[object], bool] | None = None) -> object:
        if checked is None:
            return pystray.MenuItem(text, lambda icon, item: action() if action else None)
        return pystray.MenuItem(
            text,
            lambda icon, item: action() if action else None,
            checked=lambda item: checked(item),
        )

    def _state(self) -> dict[str, bool]:
        if not self.get_state:
            return {
                'is_recording': True,
                'is_paused': False,
                'lightweight_mode': False,
                'avatar_enabled': True,
            }
        try:
            state = self.get_state() or {}
        except Exception:
            state = {}
        return {
            'is_recording': bool(state.get('is_recording', True)),
            'is_paused': bool(state.get('is_paused', False)),
            'lightweight_mode': bool(state.get('lightweight_mode', False)),
            'avatar_enabled': bool(state.get('avatar_enabled', True)),
        }

    def _build_menu(self) -> object:
        state = self._state()
        recording_text = '继续录制' if state['is_paused'] else '暂停录制'
        lightweight_text = '关闭轻量模式' if state['lightweight_mode'] else '开启轻量模式'
        avatar_text = '隐藏桌宠' if state['avatar_enabled'] else '显示桌宠'
        return pystray.Menu(
            self._menu_item('显示主界面', self.on_show),
            self._menu_item('隐藏主界面', self.on_hide),
            pystray.Menu.SEPARATOR,
            self._menu_item(recording_text, self.on_toggle_recording, checked=lambda _: not state['is_paused']),
            self._menu_item(lightweight_text, self.on_toggle_lightweight, checked=lambda _: state['lightweight_mode']),
            self._menu_item(avatar_text, self.on_toggle_avatar, checked=lambda _: state['avatar_enabled']),
            pystray.Menu.SEPARATOR,
            self._menu_item('退出', self.on_quit),
        )

    def refresh_menu(self) -> bool:
        with self._lock:
            if not self.visible or not self.icon:
                return False
            self.icon.menu = self._build_menu()
            try:
                self.icon.update_menu()
            except Exception:
                pass
            return True

    def show(self) -> bool:
        with self._lock:
            if not self.supported:
                self.visible = False
                return False
            if self.visible and self.icon:
                self.refresh_menu()
                return True

            self.icon = pystray.Icon('acticity-review', _build_icon(), 'Acticity Review', self._build_menu())
            self.thread = Thread(target=self.icon.run, daemon=True)
            self.thread.start()
            self.visible = True
            return True

    def hide(self) -> bool:
        with self._lock:
            icon = self.icon
            self.icon = None
            was_visible = self.visible
            self.visible = False
        if icon:
            icon.stop()
        return was_visible

    def stop(self) -> None:
        self.hide()


def _build_icon() -> Image.Image:
    image = Image.new('RGBA', (64, 64), (15, 23, 42, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=16, fill=(15, 23, 42, 242))
    draw.ellipse((15, 18, 33, 36), fill=(148, 163, 184, 255))
    draw.ellipse((31, 18, 49, 36), fill=(99, 102, 241, 255))
    draw.rounded_rectangle((18, 36, 46, 46), radius=5, fill=(226, 232, 240, 255))
    return image


def create_tray_controller(
    on_show: MenuAction,
    on_hide: MenuAction,
    on_quit: MenuAction,
    on_toggle_recording: MenuAction | None = None,
    on_toggle_lightweight: MenuAction | None = None,
    on_toggle_avatar: MenuAction | None = None,
    get_state: StateProvider | None = None,
) -> TrayController:
    return TrayController(
        on_show=on_show,
        on_hide=on_hide,
        on_quit=on_quit,
        on_toggle_recording=on_toggle_recording,
        on_toggle_lightweight=on_toggle_lightweight,
        on_toggle_avatar=on_toggle_avatar,
        get_state=get_state,
    )
