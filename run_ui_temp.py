"""Temporary Phase 4 popup runner for text-only UI checks.

Launch this script locally to open the Victus popup immediately. No
hotkeys, tray icons, or background listeners are used. All requests flow
through ``VictusApp.run_request`` to preserve policy and executor
coverage.
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Dict

from PySide6.QtWidgets import QApplication

from victus.app import VictusApp
from victus.core.policy import PolicyError
from victus.core.schemas import Context, PlanStep, PrivacySettings
from victus.domains.productivity.allowlisted_plugins import (
    DocsPlugin,
    GmailPlugin,
    OpenAIPlugin,
    SpotifyPlugin,
)
from victus.domains.system.system_plugin import SystemPlugin
from victus.ui.popup_window import PopupWindow


class PopupController:
    """Runs the popup window directly for local testing."""

    def __init__(self) -> None:
        self.qt_app = QApplication.instance() or QApplication(sys.argv)

        self.victus = self._build_victus_app()
        self.popup = PopupWindow(self._handle_submit)
        self._show_popup()

    def _show_popup(self) -> None:
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    def _build_victus_app(self) -> VictusApp:
        plugins = {
            "system": SystemPlugin(),
            "gmail": GmailPlugin(),
            "docs": DocsPlugin(),
            "spotify": SpotifyPlugin(),
            "openai": OpenAIPlugin(),
        }
        return VictusApp(plugins)

    def _build_context(self) -> Context:
        return Context(
            session_id="ui-temp-session",
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

    def exec(self) -> int:
        return self.qt_app.exec()


def main() -> None:
    controller = PopupController()
    sys.exit(controller.exec())


if __name__ == "__main__":
    main()
