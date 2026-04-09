from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock, Thread
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


@dataclass
class TrayController:
    on_show: MenuAction
    on_hide: MenuAction
    on_quit: MenuAction
    icon: object | None = None
    thread: Thread | None = None
    visible: bool = False
    _lock: Lock = field(default_factory=Lock)

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

    def show(self) -> bool:
        with self._lock:
            if not self.supported:
                self.visible = False
                return False
            if self.visible and self.icon:
                return True

            menu = pystray.Menu(
                pystray.MenuItem('显示主界面', lambda icon, item: self.on_show()),
                pystray.MenuItem('隐藏主界面', lambda icon, item: self.on_hide()),
                pystray.MenuItem('退出', lambda icon, item: self.on_quit()),
            )
            self.icon = pystray.Icon('acticity-review', _build_icon(), 'Acticity Review', menu)
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


def create_tray_controller(on_show: MenuAction, on_hide: MenuAction, on_quit: MenuAction) -> TrayController:
    return TrayController(on_show=on_show, on_hide=on_hide, on_quit=on_quit)
