from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from meridian_support.agent import SupportAgent
from meridian_support.settings import get_settings

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent


def resolve_public_dir() -> Path:
    """Repo `public/` on disk; on Vercel the bundle root may differ from `__file__`."""
    candidates = [
        ROOT / "public",
        Path.cwd() / "public",
        Path("/var/task/public"),
    ]
    for p in candidates:
        if p.is_dir() and (p / "index.html").is_file():
            return p
    return ROOT / "public"


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
    """Mount the chat endpoint at `path` (e.g. `/api`, `/api/chat`, or `/` on Vercel)."""

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
    register_chat_routes(app, "/api")

    public = resolve_public_dir()
    index_html = public / "index.html"
    if index_html.is_file():
        @app.get("/")
        async def serve_index() -> FileResponse:
            return FileResponse(index_html)

        css_dir = public / "css"
        if css_dir.is_dir():
            app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
        js_dir = public / "js"
        if js_dir.is_dir():
            app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    else:
        logger.warning("public/index.html missing — browser UI will 404 at /")

    return app


app = create_app()
