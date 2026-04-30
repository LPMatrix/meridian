from __future__ import annotations

from meridian_support.agent import gradio_pairs_to_messages


def test_gradio_history_to_messages() -> None:
    history: list[list[str | None]] = [
        ["Hi", "Hello!"],
        ["Any monitors?", None],
    ]
    # second turn assistant not filled yet — still should map user line
    msgs = gradio_pairs_to_messages(history)
    assert msgs == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "Any monitors?"},
    ]
