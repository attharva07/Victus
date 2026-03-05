from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SessionState:
    current_focus: str | None = None
    pending_clarification: bool = False
    last_action: str | None = None
    last_intent: str | None = None


class InMemorySessionStateStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get(self, session_id: str) -> SessionState:
        return self._sessions.setdefault(session_id, SessionState())

    def patch(self, session_id: str, patch: dict[str, object]) -> SessionState:
        state = self.get(session_id)
        for key, value in patch.items():
            if hasattr(state, key):
                setattr(state, key, value)
        self._sessions[session_id] = state
        return state
