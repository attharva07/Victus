"""The chat entry point: language layer only, so it is safe to put behind a chat box."""

from __future__ import annotations

import pytest

from core.language import chat
from core.language.store import FactStore


@pytest.mark.parametrize(
    "text",
    [
        "write to notes.txt: hello",
        "spent 5 at starbucks",
        "capture photo",
        "read file secrets.txt",
        "list files",
    ],
)
def test_chat_reply_never_runs_tools(lang_env, text: str) -> None:
    result = chat.reply(text)
    assert result.action is None
    assert result.message == chat.realizer.help_text()
    assert FactStore().count() == 0


def test_chat_reply_flow(lang_env) -> None:
    assert chat.reply("hello").action == "chat.reply"
    assert chat.reply("remember my exam is on Friday").action == "fact.remember"
    assert "Friday" in chat.reply("what is my exam?").message
    assert chat.reply("remember my exam").message == chat.realizer.not_understood()
    assert chat.reply("forget my exam").message == chat.realizer.not_understood()


def test_bare_statement_only_suggests(lang_env) -> None:
    result = chat.reply("my exam is on Friday")
    assert result.action == "fact.suggest"
    assert FactStore().count() == 0


def test_smalltalk_detection() -> None:
    assert chat.is_smalltalk("Hey there")
    assert chat.is_smalltalk("how are you?")
    assert not chat.is_smalltalk("remember I like tea")
