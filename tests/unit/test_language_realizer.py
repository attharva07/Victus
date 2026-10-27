"""Realizer guarantees: deterministic, second-person, and nothing but template + fact words."""

from __future__ import annotations

import pytest

from core.language import realizer
from core.language.extract import extract_fact, parse_question
from core.language.facts import Fact
from core.language.store import DUPLICATE, FLIPPED, NEW, REPLACED, UpsertResult

STATEMENTS = [
    "my exam is on Friday",
    "my keys are in the drawer",
    "Alice's birthday is May 3",
    "I like cold brew",
    "I don't like cold brew",
    "I live in Aiken",
    "I work at USCA",
    "I'm from Pune",
    "I study cybersecurity",
    "I'm a student",
    "Alice is my sister",
]


def _fact(text: str) -> Fact:
    fact = extract_fact(text)
    assert fact is not None
    return fact


def test_flip_person_table() -> None:
    assert realizer.flip_person("my sister") == "your sister"
    assert realizer.flip_person("Me and I'm") == "You and you're"
    assert realizer.flip_person("mine, myself") == "yours, yourself"
    assert realizer.flip_person("this is amy") == "this is amy"  # word boundaries only


def test_flip_person_capitalization_follows_position_not_source_case() -> None:
    # "I" is always capitalized in English, so source case must not decide the output case.
    assert realizer.flip_person("Alice thinks I am late") == "Alice thinks you are late"
    assert (
        realizer.flip_person("My sister said I'm here. I like it")
        == "Your sister said you're here. You like it"
    )
    assert realizer.flip_person("I am a student") == "You are a student"  # verb agreement


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ("my exam is on Friday", "Your exam is on Friday."),
        ("my keys are in the drawer", "Your keys are in the drawer."),
        ("Alice's birthday is May 3", "Alice's birthday is May 3."),
        ("I like cold brew", "You like cold brew."),
        ("I don't like cold brew", "You don't like cold brew."),
        ("I live in Aiken", "You live in Aiken."),
        ("I work at USCA", "You work at USCA."),
        ("I'm from Pune", "You are from Pune."),
        ("I study cybersecurity", "You study cybersecurity."),
        ("I'm a student", "You are a student."),
        ("Alice is my sister", "Alice is your sister."),
    ],
)
def test_sentence(statement: str, expected: str) -> None:
    assert realizer.sentence(_fact(statement)) == expected


def test_variation_is_deterministic_not_random() -> None:
    fact = _fact("I like cold brew")
    first = realizer.confirm_remembered(UpsertResult(NEW, fact))
    assert all(realizer.confirm_remembered(UpsertResult(NEW, fact)) == first for _ in range(20))


def test_variation_actually_varies_across_inputs() -> None:
    outputs = {
        realizer.confirm_remembered(UpsertResult(NEW, _fact(s))).split(".")[0] for s in STATEMENTS
    }
    assert len(outputs) > 1  # several template variants are in use


def test_status_templates() -> None:
    fact = _fact("I live in Aiken")
    old = _fact("I live in Augusta")
    assert "already" in realizer.confirm_remembered(UpsertResult(DUPLICATE, fact)).lower()
    assert "Before, I had: You live in Augusta." in realizer.confirm_remembered(
        UpsertResult(REPLACED, fact, old)
    )
    assert "opposite" in realizer.confirm_remembered(UpsertResult(FLIPPED, fact, old))


def test_realizer_only_emits_template_or_fact_words() -> None:
    """The no-hallucination property: every output word is fixed template text or from a fact."""
    vocab = realizer.template_vocabulary()
    facts = [_fact(s) for s in STATEMENTS]
    outputs: list[tuple[str, list[Fact]]] = []

    for fact in facts:
        for status in (NEW, DUPLICATE):
            outputs.append((realizer.confirm_remembered(UpsertResult(status, fact)), [fact]))
        outputs.append(
            (realizer.confirm_remembered(UpsertResult(REPLACED, fact, facts[0])), [fact, facts[0]])
        )
        outputs.append((realizer.confirm_remembered(UpsertResult(FLIPPED, fact, fact)), [fact]))
        outputs.append((realizer.confirm_forgotten(fact, True), [fact]))
        question = parse_question("do I like cold brew?")
        assert question is not None
        outputs.append((realizer.answer(question, [fact]), [fact]))
    outputs.append((realizer.answer(parse_question("tell me about my exam"), facts), facts))
    outputs.append((realizer.answer(parse_question("what do I like?"), []), []))
    outputs.append((realizer.answer(parse_question("what is my exam?"), []), []))
    outputs.append((realizer.answer(parse_question("tell me about Tokyo"), []), []))
    outputs.append((realizer.answer(parse_question("do I like pizza?"), []), []))
    outputs.append((realizer.not_understood(), []))
    outputs.append((realizer.help_text(), []))
    outputs.append((realizer.greeting("hello"), []))

    # Words that come from the user's own input echoed by design (question terms, suggestions).
    echoed = realizer.tokens("exam favorite color tokyo pizza cold brew")
    for text, used in outputs:
        allowed = set(vocab) | echoed
        for fact in used:
            allowed |= realizer.tokens(
                realizer.flip_person(f"{fact.subject_text} {fact.object_text}")
            )
        extra = {
            t for t in realizer.tokens(text) - allowed if not t.isdigit()
        }  # counts like "And 4 more."
        assert not extra, f"unexpected words {extra} in {text!r}"


def test_many_facts_are_capped_with_a_count() -> None:
    q = parse_question("what do you know about me?")
    assert q is not None
    facts = [
        Fact(
            subject_key="user",
            subject_text="you",
            relation="likes",
            object_key=f"x{i}",
            object_text=f"x{i}",
        )
        for i in range(14)
    ]
    text = realizer.answer(q, facts)
    assert "And 4 more." in text
    assert "x9" in text and "x10" not in text


def test_suggest_echoes_the_statement_cleanly() -> None:
    assert realizer.suggest_remember("my exam is on Friday.").endswith(
        "remember my exam is on Friday"
    )
