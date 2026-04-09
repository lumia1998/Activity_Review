from dataclasses import dataclass


@dataclass
class WindowState:
    label: str
    visible: bool = True
    minimized: bool = False
    maximized: bool = False
