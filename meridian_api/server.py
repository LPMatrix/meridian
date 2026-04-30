from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from meridian_support.agent import SupportAgent
from meridian_support.settings import get_settings

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT / "public"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=0)
    history: list[dict[str, Any]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    history: list[dict[str, Any]]


_settings = get_settings()
_agent = SupportAgent(_settings)


async def run_chat(request: ChatRequest) -> ChatResponse:
    text = request.message.strip()
    if not text:
        return ChatResponse(reply="", history=request.history)

    history = list(request.history)
    try:
        reply = await _agent.reply(text, history)
    except Exception:
        logger.exception("Unhandled failure during chat turn")
        reply = "Something went wrong on our side. Please try again."

    new_history = [
        *history,
        {"role": "user", "content": text},
        {"role": "assistant", "content": reply},
    ]
    return ChatResponse(reply=reply, history=new_history)


def register_chat_routes(app: FastAPI, path: str) -> None:
    """Mount the chat endpoint at `path` (e.g. `/api/chat` or `/` for Vercel `api/chat.py`)."""

    async def chat_endpoint(body: ChatRequest) -> ChatResponse:
        return await run_chat(body)

    safe = path.replace("/", "_") or "_root"
    chat_endpoint.__name__ = f"chat{safe}"
    app.add_api_route(
        path,
        chat_endpoint,
        methods=["POST"],
        response_model=ChatResponse,
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Meridian Support")

    register_chat_routes(app, "/api/chat")

    if PUBLIC_DIR.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(PUBLIC_DIR), html=True),
            name="public",
        )
    return app


def create_vercel_chat_app() -> FastAPI:
    """Minimal app for `api/chat.py` on Vercel (path may be `/` or `/api/chat` per runtime)."""
    app = FastAPI(title="Meridian Support API")
    register_chat_routes(app, "/")
    register_chat_routes(app, "/api/chat")
    return app


app = create_app()
