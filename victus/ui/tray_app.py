from __future__ import annotations

import sys
from datetime import datetime
from typing import Dict

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon
from PySide6.QtCore import QObject, QSharedMemory

from ..app import VictusApp
from ..core.schemas import Context, PlanStep, PrivacySettings
from ..domains.productivity.allowlisted_plugins import DocsPlugin, GmailPlugin, OpenAIPlugin, SpotifyPlugin
from ..domains.system.system_plugin import SystemPlugin
from ..core.policy import PolicyError
from .hotkey import GlobalHotkeyManager
from .popup_window import PopupWindow


class SingleInstanceGuard:
    """Prevents multiple tray instances from running simultaneously."""

    def __init__(self, key: str) -> None:
        self._memory = QSharedMemory(key)

    def acquire(self) -> bool:
        if self._memory.attach():
            return False
        return self._memory.create(1)

    def release(self) -> None:
        if self._memory.isAttached():
            self._memory.detach()


class TrayController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.qt_app = QApplication.instance() or QApplication(sys.argv)

        self._guard = SingleInstanceGuard("VictusTrayApp")
        if not self._guard.acquire():
            sys.exit(0)

        self.victus = self._build_victus_app()
        self.popup = PopupWindow(self._handle_submit)
        self.tray_icon = self._build_tray_icon()
        self.hotkey = GlobalHotkeyManager(self.toggle_popup)
        self.last_position = None

    def _build_victus_app(self) -> VictusApp:
        plugins = {
            "system": SystemPlugin(),
            "gmail": GmailPlugin(),
            "docs": DocsPlugin(),
            "spotify": SpotifyPlugin(),
            "openai": OpenAIPlugin(),
        }
        return VictusApp(plugins)

    def _build_tray_icon(self) -> QSystemTrayIcon:
        tray_icon = QSystemTrayIcon()
        tray_icon.setIcon(QIcon(self.qt_app.style().standardIcon(QStyle.SP_ComputerIcon)))

        menu = QMenu()
        toggle_action = QAction("Open/Hide", self.qt_app)
        toggle_action.triggered.connect(self.toggle_popup)
        menu.addAction(toggle_action)

        quit_action = QAction("Quit Victus", self.qt_app)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        tray_icon.setContextMenu(menu)
        tray_icon.setToolTip("Victus Tray")
        tray_icon.show()
        return tray_icon

    def toggle_popup(self) -> None:
        if self.popup.isVisible():
            self.hide_popup()
        else:
            self.show_popup()

    def show_popup(self) -> None:
        if self.last_position:
            self.popup.move(self.last_position)
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    def hide_popup(self) -> None:
        self.last_position = self.popup.pos()
        self.popup.hide()

    def _build_context(self) -> Context:
        return Context(
            session_id="tray-session",
            timestamp=datetime.utcnow(),
            mode="dev",
            foreground_app=None,
            privacy=PrivacySettings(allow_send_to_openai=True),
        )

    def _build_steps(self, user_text: str) -> list[PlanStep]:
        return [
            PlanStep(
                id="openai-1",
                tool="openai",
                action="generate_text",
                args={"prompt": user_text},
            )
        ]

    def _handle_submit(self, text: str) -> None:
        self.popup.append_user_message(text)
        self.popup.set_thinking()
        try:
            results = self.victus.run_request(
                user_input=text,
                context=self._build_context(),
                domain="productivity",
                steps=self._build_steps(text),
            )
            response_text = self._format_results(results)
            self.popup.append_victus_message(response_text)
            self.popup.set_ready()
        except PolicyError as exc:
            self.popup.append_victus_message(f"Denied: {exc}")
            self.popup.set_denied()
        except Exception as exc:  # noqa: BLE001 - display minimal error message
            self.popup.append_victus_message(f"Error: {exc}")
            self.popup.set_error()

    @staticmethod
    def _format_results(results: Dict[str, object]) -> str:
        if not results:
            return "No response"
        first = next(iter(results.values()))
        if isinstance(first, dict):
            for key in ("content", "summary"):
                if key in first:
                    return str(first[key])
            return str(first)
        return str(first)

    def quit(self) -> None:
        self.hotkey.unregister()
        self.tray_icon.hide()
        self._guard.release()
        self.qt_app.quit()

    def exec(self) -> int:
        code = self.qt_app.exec()
        self._guard.release()
        return code


def main() -> None:
    controller = TrayController()
    sys.exit(controller.exec())


if __name__ == "__main__":
    main()
