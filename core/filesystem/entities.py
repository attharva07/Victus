from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxFile:
    path: str
    size_bytes: int
    extension: str


@dataclass(frozen=True)
class SandboxFileContent:
    path: str
    content: str
    size_bytes: int
