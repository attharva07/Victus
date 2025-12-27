from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class LLMClientBase(ABC):
    """Shared interface for LLM providers."""

    @abstractmethod
    def generate_text(self, *, prompt: str) -> Dict[str, str]:
        """Generate free-form text from a prompt."""

    @abstractmethod
    def summarize(self, *, text: str) -> Dict[str, str]:
        """Summarize provided text."""

    @abstractmethod
    def outline(self, *, topic: str) -> Dict[str, List[str]]:
        """Create a structured outline for the given topic."""

    @abstractmethod
    def draft_email(self, *, to: str, subject: str, body: str) -> Dict[str, str]:
        """Draft an email."""
