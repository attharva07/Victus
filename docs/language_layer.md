# Language layer (LLM-free talk and remember)

`core/language/` lets Victus take a sentence, store what it means as a typed fact, and answer
questions from those facts in plain English. No model is involved anywhere in the path.

## Flow

```
sentence -> extract (controlled grammar) -> Fact -> FactStore (SQLite, exact keys)
question -> parse_question -> lookup -> realizer (templates) -> sentence
```

| Module | Job |
| --- | --- |
| `facts.py` | `Fact` (subject, relation, object, polarity) and key normalization |
| `extract.py` | statement and question grammar; returns `None` rather than guessing |
| `store.py` | `facts` table; upsert semantics; exact-match lookups only |
| `realizer.py` | template output, deterministic variation, first-to-second-person flip |
| `intents.py` | maps an utterance to `fact.remember / ask / forget / suggest` |
| `service.py` | the four handlers |
| `chat.py` | LLM-free entry point for a chat box; never reaches tools |

## Rules

1. **Identity is exact.** Subjects and objects are matched on normalized keys, never on similarity.
   "Alice" and "Alicia" are different entities.
2. **No silent writes.** Only `remember ...` (also `save`, `note`) writes. A bare statement such as
   "my exam is on Friday" gets a suggestion back and stores nothing.
3. **Stance is a typed edge.** "I like X" and "I don't like X" are one edge `(user, likes, X)` with
   polarity +1 or -1, so a contradiction flips the edge instead of creating a second row.
4. **Single-valued facts are replaced, and the reply says so.** "I live in A", then "I live in B"
   answers with the old value. Multi-valued relations (likes, studies) accumulate.
5. **Output is closed-vocabulary.** Every word the realizer emits is fixed template text or text
   copied from a stored fact. `test_realizer_only_emits_template_or_fact_words` enforces this.
6. **Personal data stays out of logs.** Audit events record relation, status and counts, never content.

## Supported sentences

Statements (after `remember`): `my <attr> is/are <value>`, `<Owner>'s <attr> is <value>`,
`I like/love/enjoy/prefer <x>`, `I don't like / hate / dislike / can't stand <x>`,
`I live in`, `I work at/for`, `I'm from`, `I study`, `I'm a/an <x>`, `<Name> is <x>`.

Questions: `what is my <attr>`, `what is <Owner>'s <attr>`, `do I like <x>`, `what do I like / hate`,
`where do I live / work`, `where am I from`, `what do I study`, `who is <Name>`,
`tell me about <x>`, `what do you know about me`.

Anything else is answered with help text. Free-text notes (`remember buy milk`) still use the
older notes memory, and `tell me about <x>` falls back to notes when no fact matches.

## Where it plugs in

- `fact.*` actions are allow-listed in `core/orchestrator/policy.py` and enabled in
  `core/config.py`, and run through `route_intent` like any other tool.
- `POST /chat` (authenticated) uses `core.language.chat.reply`, which reaches **only** this layer.
  `/api/dialogue/send` is untouched; it is unauthenticated, so it should not be pointed at memory.

## Known limits

- English only; a fixed grammar. Paraphrase is not understood, only the forms above.
- "hate" and "don't like" collapse to the same stored stance.
- Verb agreement for stored third-person text is limited to the copula (`is`/`are`).

## Swapping the store

`FactStore` is the only thing that touches storage. A knowledge graph with an entity registry can
replace it behind the same methods (`upsert`, `get`, `find`, `list_by`, `about`, `delete`) without
changing the extractor, the realizer, or the handlers.

## Known repo issue found while building this

`core/orchestrator/deterministic.py` imports `victus.core.confidence`, and
`core/cognition/decision_advisor.py` imports `core.signals.models`. Neither module exists in the
repo (both were removed in commit `12b4e97`), so the orchestrator, the router and the FastAPI app
cannot be imported on a clean checkout. `platformdirs` is also used but not declared anywhere.
The language layer does not depend on any of this. The orchestrator and `/chat` tests skip with a
reason until the imports resolve.
