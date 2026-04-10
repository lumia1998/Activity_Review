from __future__ import annotations

import socket
from contextlib import closing
from dataclasses import dataclass
from threading import Event, Thread
from typing import Callable

HOST = '127.0.0.1'
PORT = 47653
SHOW_WINDOW_MESSAGE = 'SHOW_WINDOW'


@dataclass
class SingleInstanceManager:
    on_activate: Callable[[], None]
    socket: socket.socket | None = None
    stop_event: Event | None = None
    thread: Thread | None = None

    def acquire(self) -> bool:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((HOST, PORT))
            server.listen(1)
        except OSError:
            server.close()
            return False
        self.socket = server
        self.stop_event = Event()
        self.thread = Thread(target=self._serve, daemon=True)
        self.thread.start()
        return True

    def _serve(self) -> None:
        assert self.socket is not None
        assert self.stop_event is not None
        self.socket.settimeout(1)
        while not self.stop_event.is_set():
            try:
                conn, _ = self.socket.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with closing(conn):
                try:
                    payload = conn.recv(128).decode('utf-8').strip()
                except OSError:
                    continue
                if payload == SHOW_WINDOW_MESSAGE:
                    try:
                        self.on_activate()
                    except Exception:
                        continue

    def close(self) -> None:
        if self.stop_event is not None:
            self.stop_event.set()
        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None


def notify_existing_instance() -> bool:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(1)
    try:
        client.connect((HOST, PORT))
        client.sendall(SHOW_WINDOW_MESSAGE.encode('utf-8'))
        return True
    except OSError:
        return False
    finally:
        client.close()
