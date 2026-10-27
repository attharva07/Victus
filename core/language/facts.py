from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

# Relations that hold a single value per subject: a new value replaces the old one.
FUNCTIONAL_RELATIONS: frozenset[str] = frozenset({"lives_in", "works_at", "from"})

USER_KEY = "user"

_LEADING_ARTICLE = re.compile(r"^(?:the|a|an)\s+", re.IGNORECASE)
_EDGE_PUNCT = " \t\r\n.,;:!?\"'`“”‘’"


def clean_text(text: str) -> str:
    """Whitespace/quote cleanup that keeps the user's own casing."""
    value = (text or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    value = " ".join(value.split())
    return value.strip(_EDGE_PUNCT)


def norm_key(text: str) -> str:
    """Normalized identity key: lowercase, cleaned, no leading article."""
    value = clean_text(text).lower()
    value = _LEADING_ARTICLE.sub("", value)
    return value.strip(_EDGE_PUNCT)


@dataclass(frozen=True)
class Fact:
    """One typed statement.

    ``subject_key`` / ``object_key`` are the exact-match identity; ``*_text`` keep the
    user's own wording and casing for realization. ``subject_key`` is ``"user"`` for the
    user, ``"user:<attr>"`` for the user's attributes ("my exam"), ``"<name>"`` for a
    named thing, or ``"<owner>:<attr>"`` for someone else's attribute.
    """

    subject_key: str
    subject_text: str
    relation: str
    object_key: str
    object_text: str
    polarity: int = 1
    copula: str = "is"
    id: str | None = None

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.subject_key, self.relation, self.object_key)

    @property
    def is_functional(self) -> bool:
        if self.relation in FUNCTIONAL_RELATIONS:
            return True
        return self.relation == "is" and ":" in self.subject_key

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
