from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from meridian_support.agent import SupportAgent
from meridian_support.settings import get_settings

logger = logging.getLogger(__name__)

PKG_DIR = Path(__file__).resolve().parent
ROOT = PKG_DIR.parent
TEMPLATE_DIR = PKG_DIR / "templates"
INDEX_HTML_PATH = TEMPLATE_DIR / "index.html"


def _load_index_html() -> str:
    """HTML must be in the function bundle; `public/` is excluded from it on Vercel."""
    try:
        return INDEX_HTML_PATH.read_text(encoding="utf-8")
    except OSError:
        logger.exception("Could not load %s", INDEX_HTML_PATH)
        return "<!doctype html><meta charset=utf-8><title>Meridian</title><p>UI bundle missing.</p>"


INDEX_HTML = _load_index_html()


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

    @app.get("/", response_class=HTMLResponse)
    async def serve_index() -> HTMLResponse:
        return HTMLResponse(INDEX_HTML)

    # Local-dev convenience: when `public/` is present (uvicorn), serve assets from there.
    # On Vercel, `public/` is the CDN root — these mounts simply never register and the CDN
    # responds to /css/* and /js/* directly.
    public = ROOT / "public"
    css_dir = public / "css"
    js_dir = public / "js"
    if css_dir.is_dir():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.is_dir():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

    return app


app = create_app()
