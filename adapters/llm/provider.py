from __future__ import annotations

from core.orchestrator.schemas import Intent


class LLMProvider:
    """LLM wrapper that only proposes structured intents."""

    def propose_intent(self, text: str) -> Intent | None:
        """Stub for Phase 1. Returns None to indicate no intent."""
        return None
