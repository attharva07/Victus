"""Store semantics and the remember/ask/forget flows, against a real temp SQLite DB."""

from __future__ import annotations

import pytest

from core.language import service
from core.language.extract import extract_fact
from core.language.store import DUPLICATE, FLIPPED, NEW, REPLACED, FactStore


def _fact(text: str):
    fact = extract_fact(text)
    assert fact is not None, text
    return fact


# --- store ------------------------------------------------------------------


def test_new_then_duplicate(lang_env) -> None:
    store = FactStore()
    first = store.upsert(_fact("I like cold brew"))
    second = store.upsert(_fact("I like cold brew"))
    assert first.status == NEW
    assert second.status == DUPLICATE
    assert store.count() == 1


def test_polarity_flip_updates_the_same_edge(lang_env) -> None:
    store = FactStore()
    store.upsert(_fact("I like cold brew"))
    result = store.upsert(_fact("I don't like cold brew"))
    assert result.status == FLIPPED
    assert result.previous is not None and result.previous.polarity == 1
    assert store.count() == 1  # one typed edge, not two contradictory rows
    stored = store.find("user", "likes", "cold brew")
    assert stored is not None and stored.polarity == -1


def test_functional_relation_replaces_old_value(lang_env) -> None:
    store = FactStore()
    store.upsert(_fact("I live in Aiken"))
    result = store.upsert(_fact("I live in Augusta"))
    assert result.status == REPLACED
    assert result.previous is not None and result.previous.object_key == "aiken"
    assert [f.object_key for f in store.get("user", "lives_in")] == ["augusta"]


def test_possessive_attribute_is_single_valued(lang_env) -> None:
    store = FactStore()
    store.upsert(_fact("my exam is on Friday"))
    result = store.upsert(_fact("my exam is on Monday"))
    assert result.status == REPLACED
    assert [f.object_text for f in store.get("user:exam")] == ["on Monday"]


def test_multi_valued_relations_accumulate(lang_env) -> None:
    store = FactStore()
    store.upsert(_fact("I like tea"))
    store.upsert(_fact("I like coffee"))
    assert {f.object_key for f in store.list_by("user", "likes", 1)} == {"tea", "coffee"}


def test_proper_nouns_never_merge(lang_env) -> None:
    """Regression guard for the embedding proper-noun collapse: identity is exact-match."""
    store = FactStore()
    store.upsert(_fact("Alice is my sister"))
    store.upsert(_fact("Bob is my sister"))
    assert store.count() == 2
    assert [f.subject_key for f in store.about("alice")] == ["alice"]


def test_about_matches_exact_terms_only(lang_env) -> None:
    store = FactStore()
    store.upsert(_fact("Alice's birthday is May 3"))
    store.upsert(_fact("Alicia's birthday is June 9"))
    keys = {f.subject_key for f in store.about("alice")}
    assert keys == {"alice:birthday"}  # "alicia" is a different entity, not a near-match


def test_about_escapes_like_wildcards(lang_env) -> None:
    store = FactStore()
    store.upsert(_fact("Alice is my sister"))
    assert store.about("%") == []
    assert store.about("_lice") == []


def test_delete(lang_env) -> None:
    store = FactStore()
    store.upsert(_fact("I live in Aiken"))
    assert store.delete(_fact("I live in Aiken")) is True
    assert store.delete(_fact("I live in Aiken")) is False
    assert store.count() == 0


# --- service ----------------------------------------------------------------


def test_remember_then_ask_round_trip(lang_env) -> None:
    message, payload = service.remember("remember my exam is on Friday")
    assert "Your exam is on Friday." in message
    assert payload["status"] == NEW

    answer, _ = service.ask("what is my exam?")
    assert "Your exam is on Friday." in answer


def test_update_reports_previous_value(lang_env) -> None:
    service.remember("remember my exam is on Friday")
    message, payload = service.remember("remember my exam is on Monday")
    assert "Your exam is on Monday." in message
    assert "Your exam is on Friday." in message
    assert payload["status"] == REPLACED


def test_stance_answers_yes_no_and_unknown(lang_env) -> None:
    service.remember("remember I like cold brew")
    assert service.ask("do I like cold brew?")[0].startswith("Yes.")
    service.remember("remember I don't like cold brew")
    assert service.ask("do I like cold brew?")[0].startswith("No.")
    assert "don't know" in service.ask("do I like pizza?")[0]


def test_unknown_is_honest_not_invented(lang_env) -> None:
    assert "don't have" in service.ask("what is my favorite color?")[0]
    assert "don't have" in service.ask("tell me about Tokyo")[0]


def test_second_person_flip_in_answers(lang_env) -> None:
    service.remember("remember Alice is my sister")
    answer, _ = service.ask("who is Alice?")
    assert "your sister" in answer
    assert " my " not in f" {answer.lower()} "


def test_know_about_me_lists_user_facts(lang_env) -> None:
    service.remember("remember my exam is on Friday")
    service.remember("remember I live in Aiken")
    answer, payload = service.ask("what do you know about me?")
    assert "Your exam is on Friday." in answer
    assert "You live in Aiken." in answer
    assert len(payload["facts"]) == 2


def test_forget_removes_fact(lang_env) -> None:
    service.remember("remember I live in Aiken")
    message, payload = service.forget("forget that I live in Aiken")
    assert payload["deleted"] is True and "Forgotten" in message
    assert (
        "don't have" in service.ask("where do I live?")[0]
        or "nothing" in service.ask("where do I live?")[0].lower()
    )
    again, payload = service.forget("forget that I live in Aiken")
    assert payload["deleted"] is False
    assert "nothing to forget" in again


def test_suggest_writes_nothing(lang_env) -> None:
    message, payload = service.suggest("my exam is on Friday")
    assert payload["status"] == "suggested"
    assert "remember my exam is on Friday" in message
    assert FactStore().count() == 0


def test_unparseable_remember_stores_nothing(lang_env) -> None:
    message, payload = service.remember("remember blah blah")
    assert payload["status"] == "not_understood"
    assert FactStore().count() == 0


def test_notes_fallback_for_about(lang_env) -> None:
    from core.memory.service import add_memory

    add_memory(content="tokyo trip planning notes")
    message, payload = service.ask("tell me about tokyo")
    assert "saved notes" in message and "tokyo trip planning notes" in message
    assert payload["facts"] == 0


def test_audit_does_not_log_fact_content(lang_env, monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[tuple[str, dict]] = []

    def capture(name: str, **fields) -> None:
        events.append((name, fields))

    monkeypatch.setattr(service, "audit_event", capture)
    service.remember("remember my exam is on Friday")
    service.ask("what is my exam?")
    blob = repr(events).lower()
    assert "friday" not in blob and "exam" not in blob
    assert [name for name, _ in events] == ["fact_remembered", "fact_asked"]
