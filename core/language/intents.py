from __future__ import annotations

from dataclasses import dataclass

from core.language.extract import (
    clean_text_keep_question,
    extract_fact,
    parse_question,
    strip_forget,
    strip_remember,
)

FACT_ACTIONS: tuple[str, ...] = ("fact.remember", "fact.ask", "fact.forget", "fact.suggest")


@dataclass(frozen=True)
class LanguageIntent:
    action: str
    text: str


def classify(text: str) -> LanguageIntent | None:
    """Map an utterance to a fact action, or None if it is not for the language layer.

    Writes need an explicit "remember ..." (or "save"/"note"); a bare statement is only
    offered back as a suggestion. Anything that does not parse returns None so the
    existing deterministic routes (notes, finance, files, camera) keep their behavior.
    """
    stripped = clean_text_keep_question(text)
    if not stripped:
        return None

    rest = strip_remember(stripped)
    if rest is not None and extract_fact(rest) is not None:
        return LanguageIntent("fact.remember", stripped)

    rest = strip_forget(stripped)
    if rest is not None and extract_fact(rest) is not None:
        return LanguageIntent("fact.forget", stripped)

    if parse_question(stripped) is not None:
        return LanguageIntent("fact.ask", stripped)

    if extract_fact(stripped) is not None:
        return LanguageIntent("fact.suggest", stripped)
    return None
