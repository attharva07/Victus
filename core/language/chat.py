from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from core.language import realizer, service
from core.language.extract import strip_forget, strip_remember
from core.language.intents import classify

_SMALLTALK: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(hi|hello|hey|howdy)\b", re.IGNORECASE),
    re.compile(r"\bhow are you\b", re.IGNORECASE),
    re.compile(r"\bwhat(?:'s| is) up\b", re.IGNORECASE),
    re.compile(r"^\s*good (morning|afternoon|evening)\b", re.IGNORECASE),
)


def is_smalltalk(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in _SMALLTALK)


@dataclass(frozen=True)
class ChatReply:
    message: str
    action: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


def reply(text: str) -> ChatReply:
    """LLM-free conversation: facts, greetings, and an honest help message.

    This only ever reaches the language layer. It never calls finance, files, or camera
    tools, so it is safe to expose on a chat box. Use ``/orchestrate`` for tool actions.
    """
    intent = classify(text)
    if intent is not None:
        handler = {
            "fact.remember": service.remember,
            "fact.forget": service.forget,
            "fact.suggest": service.suggest,
            "fact.ask": service.ask,
        }[intent.action]
        message, payload = handler(intent.text)
        return ChatReply(message=message, action=intent.action, payload=payload)
    if strip_remember(text) is not None or strip_forget(text) is not None:
        # The user asked to write/remove something we could not parse: say so, don't guess.
        return ChatReply(message=realizer.not_understood(), action=None)
    if is_smalltalk(text):
        return ChatReply(message=realizer.greeting(text), action="chat.reply")
    return ChatReply(message=realizer.help_text(), action=None)
