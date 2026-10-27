"""Template realizer: structured results in, plain English out. No model involved.

Every word that leaves this module is either fixed text from the template tables
below or text copied from a stored fact. ``template_vocabulary()`` exposes the fixed
part so tests can prove nothing else sneaks in.
"""

from __future__ import annotations

import re
import zlib

from core.language.extract import Question
from core.language.facts import Fact
from core.language.store import DUPLICATE, FLIPPED, NEW, REPLACED, UpsertResult

# --- fixed template text ----------------------------------------------------

REMEMBERED = ("Got it. {s}", "Noted. {s}", "Okay, I'll remember that. {s}")
ALREADY_KNEW = ("I already knew that. {s}", "That's already on record. {s}")
REPLACED_TMPL = (
    "Updated. {s} Before, I had: {old}",
    "Changed. {s} Before, I had: {old}",
)
FLIPPED_TMPL = (
    "Changed. {s} I had the opposite on record.",
    "Updated. {s} Before, I had the opposite.",
)
FORGOTTEN = ("Forgotten. I no longer have: {s}", "Done. I removed: {s}")
NOTHING_TO_FORGET = ("I don't have that on record, so there is nothing to forget.",)
NOT_UNDERSTOOD = (
    "I couldn't fit that into a fact I can store. Try a form like: remember my exam is on Friday.",
)
SUGGEST = (
    "I haven't stored that. If you want me to, say: remember {text}",
    "That is only a statement so far. To store it, say: remember {text}",
)
ANSWER_ONE = ("{s}", "As far as I know: {s}")
ANSWER_MANY = ("Here is what I have: {items}", "This is what I have on record: {items}")
MORE = "And {n} more."
STANCE_YES = "Yes. {s}"
STANCE_NO = "No. {s}"
STANCE_UNKNOWN = ("I don't know whether you like {obj}.",)
UNKNOWN_TERM = (
    "I don't have anything about {term} yet.",
    "Nothing is stored about {term} yet. You can tell me with: remember ...",
)
UNKNOWN_ATTR = ("I don't have {subject} on record yet.",)
UNKNOWN_LIST = ("I don't have anything on record for that yet.",)
NOTES_FOUND = (
    "I have no stored facts about {term}, but I found {n} saved notes that mention it. Latest: {latest}",
)
GREETINGS = ("Hello.", "Hi there.", "Hey.")
HELP = (
    "I can remember facts and answer from them. "
    "Tell me something with: remember my exam is on Friday. "
    "Then ask: what is my exam? "
    "I can also use saved notes, finance, files and camera commands."
)

_TEMPLATE_GROUPS: tuple[tuple[str, ...], ...] = (
    REMEMBERED,
    ALREADY_KNEW,
    REPLACED_TMPL,
    FLIPPED_TMPL,
    FORGOTTEN,
    NOTHING_TO_FORGET,
    NOT_UNDERSTOOD,
    SUGGEST,
    ANSWER_ONE,
    ANSWER_MANY,
    (MORE, STANCE_YES, STANCE_NO),
    STANCE_UNKNOWN,
    UNKNOWN_TERM,
    UNKNOWN_ATTR,
    UNKNOWN_LIST,
    NOTES_FOUND,
    GREETINGS,
    (HELP,),
)
# Fixed words used by sentence() and the person flip below.
_SENTENCE_WORDS = (
    "you are your is like do not don't live in work at study from doesn't has have "
    "yours yourself you're you've you'll you'd"
)

# Stored text is in the user's own voice ("my sister"); replies speak to the user.
# Phrases come first so verb agreement follows the pronoun ("I am" -> "you are").
_PERSON_FLIP = {
    "i am": "you are",
    "i was": "you were",
    "my": "your",
    "mine": "yours",
    "myself": "yourself",
    "me": "you",
    "i": "you",
    "i'm": "you're",
    "i've": "you've",
    "i'll": "you'll",
    "i'd": "you'd",
}
_PERSON_WORD = re.compile(
    r"\b(?:i am|i was|i'm|i've|i'll|i'd|mine|myself|my|me|i)\b", re.IGNORECASE
)
_AFTER_SENTENCE_END = re.compile(r"[.!?]\s+$")

_WORD = re.compile(r"[a-z0-9']+")


def flip_person(text: str) -> str:
    """Deterministic first-person to second-person flip (word table, no inference).

    Capitalization follows position, not source casing: "I" is always capitalized in
    English, so mid-sentence "Alice thinks I am late" must become "Alice thinks you are
    late". A flipped word is capitalized after sentence-ending punctuation, or at the very
    start of the text when the source word was capitalized ("My sister" -> "Your sister",
    but a fragment like "my sister" stays lowercase).
    """

    def _replace(match: re.Match[str]) -> str:
        flipped = _PERSON_FLIP[match.group(0).lower()]
        before = text[: match.start()]
        at_start = not before.strip()
        capitalize = (at_start and match.group(0)[:1].isupper()) or (
            not at_start and bool(_AFTER_SENTENCE_END.search(before))
        )
        return flipped[:1].upper() + flipped[1:] if capitalize else flipped

    return _PERSON_WORD.sub(_replace, text)


def tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def template_vocabulary() -> set[str]:
    """Every fixed word this module can emit (placeholders excluded)."""
    vocab = tokens(_SENTENCE_WORDS)
    for group in _TEMPLATE_GROUPS:
        for template in group:
            vocab |= tokens(re.sub(r"\{[a-z]+\}", " ", template))
    return vocab


def _pick(templates: tuple[str, ...], key: str) -> str:
    """Deterministic variation: same input always gives the same template."""
    return templates[zlib.crc32(key.encode("utf-8")) % len(templates)]


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


# --- facts -> sentences -----------------------------------------------------


def sentence(fact: Fact) -> str:
    """Render one fact as one sentence, in second person for the user."""
    obj = flip_person(fact.object_text)
    you = fact.subject_key == "user"
    if fact.relation == "likes":
        return f"You like {obj}." if fact.polarity > 0 else f"You don't like {obj}."
    if fact.relation == "lives_in":
        return f"You live in {obj}."
    if fact.relation == "works_at":
        return f"You work at {obj}."
    if fact.relation == "studies":
        return f"You study {obj}."
    if fact.relation == "from":
        return f"You are from {obj}."
    subject = _cap(flip_person(fact.subject_text))
    copula = "are" if you else fact.copula
    return f"{subject} {copula} {obj}."


def _fact_key(fact: Fact) -> str:
    return "|".join((fact.subject_key, fact.relation, fact.object_key, str(fact.polarity)))


# --- write confirmations ----------------------------------------------------


def confirm_remembered(result: UpsertResult) -> str:
    fact = result.fact
    key = _fact_key(fact)
    s = sentence(fact)
    if result.status == DUPLICATE:
        return _pick(ALREADY_KNEW, key).format(s=s)
    if result.status == FLIPPED:
        return _pick(FLIPPED_TMPL, key).format(s=s)
    if result.status == REPLACED and result.previous is not None:
        return _pick(REPLACED_TMPL, key).format(s=s, old=sentence(result.previous))
    return _pick(REMEMBERED, key).format(s=s)


def confirm_forgotten(fact: Fact, deleted: bool) -> str:
    if not deleted:
        return NOTHING_TO_FORGET[0]
    return _pick(FORGOTTEN, _fact_key(fact)).format(s=sentence(fact))


def not_understood() -> str:
    return NOT_UNDERSTOOD[0]


def suggest_remember(text: str) -> str:
    cleaned = " ".join(text.split()).rstrip(".!")
    return _pick(SUGGEST, cleaned.lower()).format(text=cleaned)


# --- answers ----------------------------------------------------------------


def answer(question: Question, facts: list[Fact]) -> str:
    """Realize the answer to a question from stored facts only."""
    if question.kind == "stance":
        if not facts:
            return STANCE_UNKNOWN[0].format(obj=question.object_text or "that")
        fact = facts[0]
        template = STANCE_YES if fact.polarity > 0 else STANCE_NO
        return template.format(s=sentence(fact))

    if not facts:
        if question.kind == "attr":
            return _pick(UNKNOWN_ATTR, question.subject_key or "").format(
                subject=question.subject_text or "that"
            )
        if question.kind == "about":
            return _pick(UNKNOWN_TERM, question.term_key or "").format(
                term=question.term_text or "that"
            )
        return UNKNOWN_LIST[0]

    key = "|".join(_fact_key(f) for f in facts)
    if len(facts) == 1:
        return _pick(ANSWER_ONE, key).format(s=sentence(facts[0]))
    shown = facts[:10]
    items = " ".join(sentence(f) for f in shown)
    text = _pick(ANSWER_MANY, key).format(items=items)
    if len(facts) > len(shown):
        text += " " + MORE.format(n=len(facts) - len(shown))
    return text


def notes_found(term: str, count: int, latest: str) -> str:
    return NOTES_FOUND[0].format(term=term, n=count, latest=latest)


# --- small talk / help ------------------------------------------------------


def greeting(text: str) -> str:
    return _pick(GREETINGS, text.strip().lower())


def help_text() -> str:
    return HELP
