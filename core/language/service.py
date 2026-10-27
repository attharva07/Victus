from __future__ import annotations

from typing import Any

from core.language import realizer
from core.language.extract import (
    Question,
    clean_text_keep_question,
    extract_fact,
    parse_question,
    strip_forget,
    strip_remember,
)
from core.language.store import DEFAULT_STORE, FactStore
from core.logging.audit import audit_event, safe_excerpt

HandlerResult = tuple[str, dict[str, Any]]


def remember(text: str, store: FactStore | None = None) -> HandlerResult:
    """Store one explicit statement. Only called for "remember ..." utterances."""
    store = store or DEFAULT_STORE
    statement = strip_remember(text) or clean_text_keep_question(text)
    fact = extract_fact(statement)
    if fact is None:
        return realizer.not_understood(), {"status": "not_understood"}
    result = store.upsert(fact)
    # Audit the structure, never the content: facts are personal data.
    audit_event(
        "fact_remembered", fact_id=result.fact.id, relation=fact.relation, status=result.status
    )
    return realizer.confirm_remembered(result), {
        "status": result.status,
        "fact": result.fact.to_dict(),
        "previous": result.previous.to_dict() if result.previous else None,
    }


def forget(text: str, store: FactStore | None = None) -> HandlerResult:
    store = store or DEFAULT_STORE
    statement = strip_forget(text) or clean_text_keep_question(text)
    fact = extract_fact(statement)
    if fact is None:
        return realizer.not_understood(), {"status": "not_understood"}
    deleted = store.delete(fact)
    audit_event("fact_forgotten", relation=fact.relation, deleted=deleted)
    return realizer.confirm_forgotten(fact, deleted), {"deleted": deleted, "fact": fact.to_dict()}


def suggest(text: str) -> HandlerResult:
    """A bare statement: offer to store it, but write nothing."""
    statement = clean_text_keep_question(text)
    fact = extract_fact(statement)
    if fact is None:
        return realizer.not_understood(), {"status": "not_understood"}
    return realizer.suggest_remember(statement), {"status": "suggested", "fact": fact.to_dict()}


def _lookup(question: Question, store: FactStore):
    if question.kind == "attr" and question.subject_key:
        return store.get(question.subject_key, question.relation)
    if question.kind == "relation" and question.subject_key and question.relation:
        return store.get(question.subject_key, question.relation)
    if (
        question.kind == "stance"
        and question.subject_key
        and question.relation
        and question.object_key
    ):
        found = store.find(question.subject_key, question.relation, question.object_key)
        return [found] if found else []
    if question.kind == "list" and question.subject_key and question.relation:
        return store.list_by(question.subject_key, question.relation, question.polarity)
    if question.kind == "about" and question.term_key:
        return store.about(question.term_key)
    return []


def _notes_fallback(question: Question) -> HandlerResult | None:
    """Free-text notes are the older memory system; mention them only as a fallback."""
    if question.kind != "about" or not question.term_text:
        return None
    try:
        from core.memory.service import search_memories

        notes = search_memories(query=question.term_text, tags=None, limit=3)
    except Exception:  # noqa: BLE001 - notes are best-effort, never block an answer
        return None
    if not notes:
        return None
    latest = safe_excerpt(str(notes[0].get("content", "")).strip(), max_len=80)
    return realizer.notes_found(question.term_text, len(notes), latest), {
        "notes": len(notes),
        "facts": 0,
    }


def ask(text: str, store: FactStore | None = None) -> HandlerResult:
    store = store or DEFAULT_STORE
    question = parse_question(text)
    if question is None:
        return realizer.help_text(), {"status": "not_understood"}
    facts = _lookup(question, store)
    audit_event("fact_asked", kind=question.kind, returned=len(facts))
    if not facts:
        fallback = _notes_fallback(question)
        if fallback is not None:
            return fallback
    return realizer.answer(question, facts), {
        "facts": [fact.to_dict() for fact in facts],
        "kind": question.kind,
    }
