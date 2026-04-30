from __future__ import annotations

import logging
import os

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


async def respond(message: str, history: list[list[str | None]]) -> tuple[list[list[str | None]], str]:
    """Gradio handler: MCP + LLM live in the agent; UI only displays text."""
    text = message.strip()
    if not text:
        return history, ""
    try:
        reply = await _agent.reply(text, history)
    except Exception:
        logger.exception("Unhandled failure during chat turn")
        reply = "Something went wrong on our side. Please try again."
    return history + [[text, reply]], ""


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Meridian Electronics — Support",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown(
            "# Meridian Electronics · Customer Support (prototype)\n"
            "Ask about **products**, **orders**, or **account verification**. "
            "The assistant uses Meridian’s live **MCP ordering service** — it only "
            "states facts returned by tools.\n\n"
            "**Note:** Place an API key (`OPENAI_API_KEY`) in environment or Hugging Face Space secrets."
        )
        chatbot = gr.Chatbot(label="Conversation", height=420, type="tuples")
        user = gr.Textbox(
            label="Your message",
            placeholder="e.g. Search for 4K monitors, or verify me with my email and PIN",
            lines=2,
        )
        user.submit(respond, [user, chatbot], [chatbot, user])
        gr.Markdown(
            "Deployment: set `MCP_SERVER_URL` (optional; default is the provided Cloud Run URL) "
            "and `OPENAI_API_KEY`. Model defaults to **gpt-4o-mini** via `LLM_MODEL`."
        )
    return demo


demo = build_ui()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.queue(default_enabled=True).launch(
        server_name="0.0.0.0",
        server_port=port,
        share=_settings.gradio_share,
    )
