"""Grammar tests: statements and questions parse deterministically, or not at all."""

from __future__ import annotations

import pytest

from core.language.extract import extract_fact, parse_question, strip_forget, strip_remember
from core.language.facts import norm_key


# --- statements -------------------------------------------------------------


def test_possessive_attribute_statement() -> None:
    fact = extract_fact("my exam is on Friday")
    assert fact is not None
    assert (fact.subject_key, fact.relation, fact.object_key) == ("user:exam", "is", "on friday")
    assert fact.object_text == "on Friday"  # user's casing is kept for realization
    assert fact.polarity == 1


def test_possessive_plural_keeps_copula() -> None:
    fact = extract_fact("my keys are in the drawer")
    assert fact is not None
    assert fact.copula == "are"
    assert fact.subject_key == "user:keys"


def test_owner_attribute_statement() -> None:
    fact = extract_fact("Alice's birthday is May 3")
    assert fact is not None
    assert fact.subject_key == "alice:birthday"
    assert fact.subject_text == "Alice's birthday"
    assert fact.object_text == "May 3"


@pytest.mark.parametrize(
    "text", ["I like cold brew", "I love cold brew", "i really enjoy cold brew."]
)
def test_positive_stance(text: str) -> None:
    fact = extract_fact(text)
    assert fact is not None
    assert (fact.subject_key, fact.relation, fact.object_key, fact.polarity) == (
        "user",
        "likes",
        "cold brew",
        1,
    )


@pytest.mark.parametrize(
    "text",
    [
        "I don't like cold brew",
        "I do not like cold brew",
        "I hate cold brew",
        "I dislike cold brew",
        "I can't stand cold brew",
    ],
)
def test_negative_stance_is_same_edge_with_opposite_polarity(text: str) -> None:
    fact = extract_fact(text)
    assert fact is not None
    assert (fact.subject_key, fact.relation, fact.object_key, fact.polarity) == (
        "user",
        "likes",
        "cold brew",
        -1,
    )


@pytest.mark.parametrize(
    ("text", "relation", "obj"),
    [
        ("I live in Aiken", "lives_in", "aiken"),
        ("I work at USCA", "works_at", "usca"),
        ("I work for USCA", "works_at", "usca"),
        ("I'm from Pune", "from", "pune"),
        ("I study cybersecurity", "studies", "cybersecurity"),
        ("I am studying networks", "studies", "networks"),
        ("I'm a student", "is", "student"),
    ],
)
def test_user_relations(text: str, relation: str, obj: str) -> None:
    fact = extract_fact(text)
    assert fact is not None
    assert (fact.subject_key, fact.relation, fact.object_key) == ("user", relation, obj)


def test_named_subject_needs_capitalized_name() -> None:
    fact = extract_fact("Alice is my sister")
    assert fact is not None
    assert (fact.subject_key, fact.object_key) == ("alice", "my sister")
    assert extract_fact("the sky is blue") is None  # not a named subject: no guessing


@pytest.mark.parametrize(
    "text",
    [
        "What is my exam",  # question word is not a name
        "Who is Alice",
        "It is raining",
        "This is a test",
        "I spent 5 dollars on lunch",
        "blah blah blah",
        "my exam",
        "",
        "   ",
    ],
)
def test_non_statements_return_none(text: str) -> None:
    assert extract_fact(text) is None


def test_question_mark_is_never_a_statement() -> None:
    assert extract_fact("my exam is on Friday?") is None
    assert extract_fact("I like cold brew?") is None


def test_overlong_value_is_rejected() -> None:
    assert extract_fact("my note is " + "x" * 500) is None


def test_prefix_stripping() -> None:
    assert strip_remember("remember my exam is on Friday") == "my exam is on Friday"
    assert strip_remember("Remember that I like tea") == "I like tea"
    assert strip_remember("please save I live in Aiken") == "I live in Aiken"
    assert strip_remember("my exam is on Friday") is None
    assert strip_forget("forget that I live in Aiken") == "I live in Aiken"
    assert strip_forget("remember x") is None


def test_norm_key_is_exact_not_fuzzy() -> None:
    assert norm_key("  The Beach. ") == "beach"
    assert norm_key("Augusta") != norm_key("Charlotte")  # identity is discrete, never similarity


# --- questions --------------------------------------------------------------


def test_attr_question() -> None:
    q = parse_question("what is my exam?")
    assert q is not None
    assert (q.kind, q.subject_key, q.relation) == ("attr", "user:exam", "is")
    assert parse_question("What's my exam") == q


def test_owner_attr_question() -> None:
    q = parse_question("what is Alice's birthday?")
    assert q is not None
    assert (q.kind, q.subject_key) == ("attr", "alice:birthday")


def test_stance_and_list_questions() -> None:
    stance = parse_question("do I like cold brew?")
    assert stance is not None
    assert (stance.kind, stance.relation, stance.object_key) == ("stance", "likes", "cold brew")

    likes = parse_question("what do I like?")
    dislikes = parse_question("what do I hate?")
    assert likes is not None and dislikes is not None
    assert (likes.kind, likes.polarity) == ("list", 1)
    assert (dislikes.kind, dislikes.polarity) == ("list", -1)


@pytest.mark.parametrize(
    ("text", "relation"),
    [
        ("where do I live?", "lives_in"),
        ("where do I work?", "works_at"),
        ("where am I from?", "from"),
    ],
)
def test_relation_questions(text: str, relation: str) -> None:
    q = parse_question(text)
    assert q is not None
    assert (q.kind, q.relation) == ("relation", relation)


def test_about_questions() -> None:
    me = parse_question("what do you know about me?")
    assert me is not None and me.term_key == "user"
    mine = parse_question("tell me about my exam")
    assert mine is not None and mine.term_key == "user:exam"
    who = parse_question("who is Alice?")
    assert who is not None and (who.kind, who.term_key) == ("about", "alice")


@pytest.mark.parametrize(
    "text",
    [
        "what is my spending summary",  # belongs to finance: never claimed
        "what is my budget",
        "tell me about my transactions",
        "list transactions",
        "hello there",
        "",
    ],
)
def test_other_domains_are_not_claimed(text: str) -> None:
    assert parse_question(text) is None
