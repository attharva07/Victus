"""Deterministic, LLM-free language layer.

Language comes in through a small controlled grammar (``extract``), is stored as
typed facts (``store``), and goes back out through a template realizer
(``realizer``). Nothing in this package calls a model: every word the realizer
emits is either fixed template text or text taken from a stored fact.

Design rules (see ``docs/language_layer.md``):

* Identity is settled by exact normalized-key lookup, never by similarity.
* Nothing is written unless the user explicitly says "remember ...".
* Stance is a typed edge: ``(user, likes, X, polarity=+1/-1)``.
* If a sentence does not fit the grammar, say so; never guess.
"""
