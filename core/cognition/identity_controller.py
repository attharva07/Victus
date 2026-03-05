from __future__ import annotations

from typing import Any

from core.cognition.models import Decision, IdentityResult


class IdentityController:
    def resolve(
        self,
        *,
        user_text: str,
        decision: Decision,
        session_state: dict[str, Any],
        memory_candidates: list[dict[str, Any]],
        memory_cap: int = 3,
    ) -> IdentityResult:
        lowered = user_text.lower()
        persona_mode = "jarvis_playful"
        if decision.risk in {"high", "blocked"}:
            persona_mode = "crisp_cautious"
        elif any(token in lowered for token in ("sad", "upset", "anxious", "stressed")):
            persona_mode = "warm"

        selected: list[dict[str, Any]] = []
        for memory in memory_candidates:
            tags = {str(tag).lower() for tag in memory.get("tags", [])}
            if decision.risk in {"high", "blocked"} and (memory.get("sensitive") or "sensitive" in tags):
                continue
            selected.append(memory)
            if len(selected) >= memory_cap:
                break

        patch = {
            "current_focus": session_state.get("current_focus") or decision.mode,
            "last_action": session_state.get("last_action"),
        }
        if decision.mode == "clarify":
            patch["pending_clarification"] = True
        elif decision.mode in {"act", "suggest", "refuse"}:
            patch["pending_clarification"] = False

        return IdentityResult(persona_mode=persona_mode, selected_memories=selected, state_patch=patch)
