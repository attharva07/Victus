from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .schemas import Context, Plan, PlanStep


@dataclass
class RoutedRequest:
    user_input: str
    context: Context
    plan: Optional[Plan]


class Router:
    """Simple request router placeholder.

    Phase 1 only validates that an input/context pair is packaged for planning.
    """

    def route(self, user_input: str, context: Context) -> RoutedRequest:
        if not user_input:
            raise ValueError("user_input must be provided")
        inferred_plan = self._map_intent_to_plan(user_input)
        return RoutedRequest(user_input=user_input, context=context, plan=inferred_plan)

    def _map_intent_to_plan(self, user_input: str) -> Plan | None:
        intent = user_input.lower()
        intent_map = {
            "access_overview": ["what has access", "connections to my laptop", "who is connected", "open connections"],
            "net_connections": ["list connections"],
            "exposure_snapshot": ["listening ports"],
            "local_devices": ["connected devices"],
        }

        for action, keywords in intent_map.items():
            if any(keyword in intent for keyword in keywords):
                step = PlanStep(id="step-1", tool="system", action=action, args={})
                return Plan(goal=user_input, domain="system", steps=[step], risk="low")
        return None
