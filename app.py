from __future__ import annotations

import logging
import os
from typing import Any

import gradio as gr

from meridian_support.agent import SupportAgent
from meridian_support.settings import get_settings

logging.basicConfig(
    level=getattr(logging, get_settings().log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

_settings = get_settings()
_agent = SupportAgent(_settings)


async def respond(message: str, history: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Gradio handler: MCP + LLM live in the agent; UI only displays text."""
    text = message.strip()
    if not text:
        return history, ""
    try:
        reply = await _agent.reply(text, history)
    except Exception:
        logger.exception("Unhandled failure during chat turn")
        reply = "Something went wrong on our side. Please try again."
    return [
        *history,
        {"role": "user", "content": text},
        {"role": "assistant", "content": reply},
    ], ""


def build_ui() -> gr.Blocks:
    # theme on Blocks is deprecated in Gradio 6+ (move to launch then); current SDK has no theme= on launch.
    with gr.Blocks(
        title="Meridian Electronics — Support",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown(
            "# Meridian Electronics · Customer Support (prototype)\n"
            "Ask about **products**, **orders**, or **account verification**. "
            "The assistant uses Meridian’s live **MCP ordering service** — it only "
            "states facts returned by tools.\n\n"
        )
        chatbot = gr.Chatbot(
            label="Conversation",
            height=420,
            type="messages",
            allow_tags=False,
        )
        with gr.Row():
            user = gr.Textbox(
                label="Your message",
                placeholder="e.g. Search for 4K monitors, or verify me with my email and PIN",
                lines=2,
                scale=4,
                show_label=True,
            )
            submit_btn = gr.Button("Send", variant="primary", scale=0, min_width=100)
        submit_inputs = [user, chatbot]
        submit_outputs = [chatbot, user]
        submit_btn.click(respond, submit_inputs, submit_outputs)
        user.submit(respond, submit_inputs, submit_outputs)
    return demo


demo = build_ui()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=port,
        share=_settings.gradio_share,
    )
