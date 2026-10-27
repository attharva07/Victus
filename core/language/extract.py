from __future__ import annotations

import re
from dataclasses import dataclass

from core.language.facts import USER_KEY, Fact, clean_text, norm_key

MAX_VALUE_CHARS = 120
MAX_ATTR_WORDS = 4

# Words that can start a sentence but are never a named subject.
_NOT_A_NAME = frozenset(
    {
        "what",
        "who",
        "where",
        "when",
        "why",
        "how",
        "which",
        "is",
        "are",
        "do",
        "does",
        "did",
        "can",
        "could",
        "will",
        "would",
        "should",
        "tell",
        "remember",
        "forget",
        "save",
        "note",
        "list",
        "show",
        "it",
        "this",
        "that",
        "there",
        "here",
        "he",
        "she",
        "they",
        "we",
        "you",
        "i",
        "my",
        "your",
        "our",
        "his",
        "her",
        "their",
        "please",
    }
)

# Question phrases that belong to other domains (finance etc.): never claim them.
_RESERVED_ATTR_WORDS = frozenset(
    {"spending", "transaction", "transactions", "summary", "budget", "balance", "spent", "bills"}
)

_NAME = r"[A-Z][\w'\-]*(?:\s[A-Z][\w'\-]*){0,2}"

# --- statements -------------------------------------------------------------

_REMEMBER_PREFIX = re.compile(
    r"^(?:please\s+)?(?:remember|save|note)(?:\s+that)?\s+(?P<rest>.+)$", re.I
)
_FORGET_PREFIX = re.compile(r"^(?:please\s+)?forget(?:\s+that)?\s+(?P<rest>.+)$", re.I)

_MY_ATTR = re.compile(r"^my\s+(?P<attr>[\w'\- ]{1,40}?)\s+(?P<be>is|are)\s+(?P<val>.+)$", re.I)
_OWNER_ATTR = re.compile(
    rf"^(?P<owner>{_NAME})'s\s+(?P<attr>[\w'\- ]{{1,40}}?)\s+(?P<be>is|are)\s+(?P<val>.+)$"
)
_DISLIKE_NEG = re.compile(
    r"^i\s+(?:really\s+)?(?:don'?t|do\s+not)\s+(?:really\s+)?(?:like|enjoy|love)\s+(?P<obj>.+)$",
    re.I,
)
_DISLIKE_VERB = re.compile(r"^i\s+(?:really\s+)?(?:hate|dislike|detest)\s+(?P<obj>.+)$", re.I)
_DISLIKE_CANT = re.compile(r"^i\s+can(?:'?t|not)\s+stand\s+(?P<obj>.+)$", re.I)
_LIKE = re.compile(
    r"^i\s+(?:really\s+|truly\s+|absolutely\s+)?(?:like|love|enjoy|prefer|adore)\s+(?P<obj>.+)$",
    re.I,
)
_LIVE = re.compile(r"^i\s+(?:currently\s+)?live\s+in\s+(?P<obj>.+)$", re.I)
_WORK = re.compile(r"^i\s+(?:currently\s+)?work\s+(?:at|for)\s+(?P<obj>.+)$", re.I)
_FROM = re.compile(r"^i(?:\s+am|'m)\s+from\s+(?P<obj>.+)$", re.I)
_STUDY = re.compile(
    r"^i\s+(?:currently\s+)?study\s+(?P<obj>.+)$|^i(?:\s+am|'m)\s+studying\s+(?P<obj2>.+)$", re.I
)
_IDENTITY = re.compile(r"^i(?:\s+am|'m)\s+(?P<obj>(?:a|an)\s+.+)$", re.I)
_NAMED = re.compile(rf"^(?P<name>{_NAME})\s+(?P<be>is|are)\s+(?P<obj>.+)$")

# --- questions --------------------------------------------------------------

_Q_MY_ATTR = re.compile(r"^what(?:'s|\s+is|\s+are)\s+my\s+(?P<attr>.+)$", re.I)
_Q_OWNER_ATTR = re.compile(
    r"^what(?:'s|\s+is|\s+are)\s+(?P<owner>[A-Za-z][\w\-]*(?:\s[A-Za-z][\w\-]*){0,2})'s\s+(?P<attr>.+)$",
    re.I,
)
_Q_STANCE = re.compile(r"^do\s+i\s+(?:really\s+)?(?:like|love|enjoy)\s+(?P<obj>.+)$", re.I)
_Q_LIST_LIKES = re.compile(r"^what\s+do\s+i\s+(?:like|love|enjoy)$", re.I)
_Q_LIST_DISLIKES = re.compile(r"^what\s+do\s+i\s+(?:hate|dislike)$", re.I)
_Q_LIVE = re.compile(r"^where\s+do\s+i\s+live$", re.I)
_Q_WORK = re.compile(r"^where\s+do\s+i\s+work$", re.I)
_Q_FROM = re.compile(r"^where\s+am\s+i\s+from$", re.I)
_Q_STUDY = re.compile(r"^what\s+do\s+i\s+study$", re.I)
_Q_ABOUT = re.compile(
    r"^(?:what\s+do\s+you\s+(?:know|remember)\s+about|tell\s+me\s+about)\s+(?P<term>.+)$", re.I
)
_Q_WHO = re.compile(r"^who\s+(?:is|are)\s+(?P<term>.+)$", re.I)


def strip_remember(text: str) -> str | None:
    """Return the statement after "remember"/"save"/"note", or None if there is no prefix."""
    match = _REMEMBER_PREFIX.match(clean_text_keep_question(text))
    if match is None:
        return None
    return match.group("rest").strip() or None


def strip_forget(text: str) -> str | None:
    match = _FORGET_PREFIX.match(clean_text_keep_question(text))
    if match is None:
        return None
    return match.group("rest").strip() or None


def clean_text_keep_question(text: str) -> str:
    value = (text or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(value.split()).strip()


def is_question(text: str) -> bool:
    return clean_text_keep_question(text).endswith("?")


def _value(raw: str) -> str | None:
    value = clean_text(raw)
    if not value or len(value) > MAX_VALUE_CHARS or "?" in value:
        return None
    return value


def _attr(raw: str) -> str | None:
    value = clean_text(raw)
    if not value or len(value.split()) > MAX_ATTR_WORDS or "?" in value:
        return None
    return value


def _user_fact(
    relation: str, obj_raw: str, *, polarity: int = 1, copula: str = "is"
) -> Fact | None:
    obj = _value(obj_raw)
    if obj is None:
        return None
    key = norm_key(obj)
    if not key:
        return None
    return Fact(
        subject_key=USER_KEY,
        subject_text="you",
        relation=relation,
        object_key=key,
        object_text=obj,
        polarity=polarity,
        copula=copula,
    )


def extract_fact(text: str) -> Fact | None:
    """Parse one statement into a typed Fact, or None if it does not fit the grammar."""
    raw = clean_text_keep_question(text)
    if not raw or raw.endswith("?"):
        return None
    statement = clean_text(raw)

    match = _MY_ATTR.match(statement)
    if match:
        attr = _attr(match.group("attr"))
        value = _value(match.group("val"))
        if attr is None or value is None:
            return None
        return Fact(
            subject_key=f"{USER_KEY}:{norm_key(attr)}",
            subject_text=f"your {attr}",
            relation="is",
            object_key=norm_key(value),
            object_text=value,
            copula=match.group("be").lower(),
        )

    match = _OWNER_ATTR.match(statement)
    if match:
        owner = clean_text(match.group("owner"))
        attr = _attr(match.group("attr"))
        value = _value(match.group("val"))
        if not owner or attr is None or value is None:
            return None
        return Fact(
            subject_key=f"{norm_key(owner)}:{norm_key(attr)}",
            subject_text=f"{owner}'s {attr}",
            relation="is",
            object_key=norm_key(value),
            object_text=value,
            copula=match.group("be").lower(),
        )

    for pattern in (_DISLIKE_NEG, _DISLIKE_VERB, _DISLIKE_CANT):
        match = pattern.match(statement)
        if match:
            return _user_fact("likes", match.group("obj"), polarity=-1)

    match = _LIKE.match(statement)
    if match:
        return _user_fact("likes", match.group("obj"))

    match = _LIVE.match(statement)
    if match:
        return _user_fact("lives_in", match.group("obj"))
    match = _WORK.match(statement)
    if match:
        return _user_fact("works_at", match.group("obj"))
    match = _FROM.match(statement)
    if match:
        return _user_fact("from", match.group("obj"))
    match = _STUDY.match(statement)
    if match:
        return _user_fact("studies", match.group("obj") or match.group("obj2"))

    match = _IDENTITY.match(statement)
    if match:
        return _user_fact("is", match.group("obj"), copula="are")

    match = _NAMED.match(statement)
    if match:
        name = clean_text(match.group("name"))
        first = name.split()[0].lower()
        value = _value(match.group("obj"))
        if not name or first in _NOT_A_NAME or value is None:
            return None
        return Fact(
            subject_key=norm_key(name),
            subject_text=name,
            relation="is",
            object_key=norm_key(value),
            object_text=value,
            copula=match.group("be").lower(),
        )
    return None


@dataclass(frozen=True)
class Question:
    """A parsed question. ``kind`` is one of: attr, stance, list, relation, about."""

    kind: str
    subject_key: str | None = None
    subject_text: str | None = None
    relation: str | None = None
    object_key: str | None = None
    object_text: str | None = None
    polarity: int = 1
    term_key: str | None = None
    term_text: str | None = None


def _reserved(attr: str) -> bool:
    return any(word in _RESERVED_ATTR_WORDS for word in norm_key(attr).split())


def _about(term_raw: str) -> Question | None:
    term = clean_text(term_raw)
    if not term:
        return None
    lowered = norm_key(term)
    if lowered in {"me", "myself"}:
        return Question(kind="about", term_key=USER_KEY, term_text="you")
    if lowered.startswith("my "):
        attr = lowered[3:].strip()
        if not attr or _reserved(attr):
            return None
        return Question(kind="about", term_key=f"{USER_KEY}:{attr}", term_text=f"your {attr}")
    return Question(kind="about", term_key=lowered, term_text=term)


def parse_question(text: str) -> Question | None:
    """Parse a question into a lookup, or None if it does not fit the grammar."""
    statement = clean_text(clean_text_keep_question(text))
    if not statement:
        return None

    match = _Q_MY_ATTR.match(statement)
    if match:
        attr = _attr(match.group("attr"))
        if attr is None or _reserved(attr):
            return None
        return Question(
            kind="attr",
            subject_key=f"{USER_KEY}:{norm_key(attr)}",
            subject_text=f"your {attr}",
            relation="is",
        )

    match = _Q_OWNER_ATTR.match(statement)
    if match:
        owner = clean_text(match.group("owner"))
        attr = _attr(match.group("attr"))
        if not owner or attr is None or _reserved(attr):
            return None
        return Question(
            kind="attr",
            subject_key=f"{norm_key(owner)}:{norm_key(attr)}",
            subject_text=f"{owner}'s {attr}",
            relation="is",
        )

    match = _Q_STANCE.match(statement)
    if match:
        obj = _value(match.group("obj"))
        if obj is None:
            return None
        return Question(
            kind="stance",
            subject_key=USER_KEY,
            relation="likes",
            object_key=norm_key(obj),
            object_text=obj,
        )

    if _Q_LIST_LIKES.match(statement):
        return Question(kind="list", subject_key=USER_KEY, relation="likes", polarity=1)
    if _Q_LIST_DISLIKES.match(statement):
        return Question(kind="list", subject_key=USER_KEY, relation="likes", polarity=-1)
    if _Q_STUDY.match(statement):
        return Question(kind="list", subject_key=USER_KEY, relation="studies", polarity=1)
    if _Q_LIVE.match(statement):
        return Question(kind="relation", subject_key=USER_KEY, relation="lives_in")
    if _Q_WORK.match(statement):
        return Question(kind="relation", subject_key=USER_KEY, relation="works_at")
    if _Q_FROM.match(statement):
        return Question(kind="relation", subject_key=USER_KEY, relation="from")

    match = _Q_ABOUT.match(statement) or _Q_WHO.match(statement)
    if match:
        return _about(match.group("term"))
    return None
