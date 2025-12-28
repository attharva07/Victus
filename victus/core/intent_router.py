from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RoutedAction:
    action: str
    args: Dict[str, object] = field(default_factory=dict)


def route_intent(user_input: str) -> Optional[RoutedAction]:
    """Deterministically route monitoring intents to system actions.

    Returns a ``RoutedAction`` when a known system monitoring phrase is detected,
    otherwise ``None`` so the LLM planner can handle the request.
    """

    normalized = user_input.lower().strip()
    intent_map: Dict[str, List[str]] = {
        "status": ["system status", "status check", "system health"],
        "net_snapshot": ["network snapshot", "net snapshot", "network summary", "network status"],
        "net_connections": ["list connections", "network connections", "active connections"],
        "exposure_snapshot": ["listening ports", "open ports", "port status"],
        "bt_status": ["bluetooth status", "bt status", "bluetooth devices"],
        "local_devices": ["connected devices", "local devices", "usb devices"],
        "access_overview": [
            "access overview",
            "who is connected",
            "what has access",
            "connections to my laptop",
            "open connections",
        ],
    }

    for action, phrases in intent_map.items():
        if any(phrase in normalized for phrase in phrases):
            return RoutedAction(action=action)

    return None
