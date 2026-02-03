from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessHandle:
    process: subprocess.Popen[str]


def spawn(command: list[str]) -> ProcessHandle:
    process = subprocess.Popen(command)
    return ProcessHandle(process=process)


def stop(handle: Optional[ProcessHandle]) -> None:
    if handle is None:
        return
    handle.process.terminate()
    handle.process.wait(timeout=10)
