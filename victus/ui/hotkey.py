from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from typing import Callable, Optional

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject


MOD_ALT = 0x0001
MOD_WIN = 0x0008
WM_HOTKEY = 0x0312


class _HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, callback: Callable[[], None], hotkey_id: int) -> None:
        super().__init__()
        self.callback = callback
        self.hotkey_id = hotkey_id

    def nativeEventFilter(self, event_type: bytes, message: int) -> tuple[bool, int]:  # type: ignore[override]
        if sys.platform != "win32":
            return False, 0

        msg = ctypes.cast(message, ctypes.POINTER(wintypes.MSG)).contents
        if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
            self.callback()
            return True, 0
        return False, 0


class GlobalHotkeyManager(QObject):
    """Registers a global hotkey on Windows and routes it into the Qt event loop."""

    def __init__(self, on_toggle: Callable[[], None], hotkey_id: int = 1) -> None:
        super().__init__()
        self.on_toggle = on_toggle
        self.hotkey_id = hotkey_id
        self._filter: Optional[_HotkeyEventFilter] = None
        self._registered = False

        if sys.platform == "win32":
            self._register_hotkey()
        else:
            # Non-Windows platforms simply skip hotkey wiring to avoid crashes.
            self._registered = False

    def _register_hotkey(self) -> None:
        modifiers = MOD_WIN | MOD_ALT
        key_code = ord("V")
        if ctypes.windll.user32.RegisterHotKey(None, self.hotkey_id, modifiers, key_code):
            self._filter = _HotkeyEventFilter(self.on_toggle, self.hotkey_id)
            QCoreApplication.instance().installNativeEventFilter(self._filter)
            self._registered = True

    def unregister(self) -> None:
        if sys.platform != "win32":
            return
        if self._registered:
            ctypes.windll.user32.UnregisterHotKey(None, self.hotkey_id)
            self._registered = False
        if self._filter:
            QCoreApplication.instance().removeNativeEventFilter(self._filter)
            self._filter = None
