from __future__ import annotations

from meridian_support.agent import chat_messages_to_prior_turns


def test_chat_messages_to_prior_turns() -> None:
    history: list[dict[str, str]] = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "Any monitors?"},
    ]
    msgs = chat_messages_to_prior_turns(history)
    assert msgs == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "Any monitors?"},
    ]
