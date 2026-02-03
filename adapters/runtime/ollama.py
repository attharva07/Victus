from __future__ import annotations

import subprocess
from typing import Optional

from adapters.runtime.supervisor import ProcessHandle, spawn


class OllamaRuntime:
    """Minimal placeholder for managing an Ollama process."""

    def __init__(self) -> None:
        self._handle: Optional[ProcessHandle] = None

    def start(self) -> None:
        if self._handle is None:
            self._handle = spawn(["ollama", "serve"])

    def stop(self) -> None:
        if self._handle:
            self._handle.process.terminate()
            self._handle.process.wait(timeout=10)
            self._handle = None

    def check(self) -> bool:
        if self._handle is None:
            return False
        return self._handle.process.poll() is None
