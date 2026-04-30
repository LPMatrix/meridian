from __future__ import annotations

import json
import logging
from typing import Any

from mcp import ClientSession
from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError

from meridian_support.mcp_bridge import invoke_tool, list_tools_paginated, mcp_client_session
from meridian_support.openai_tools import mcp_tools_to_openai
from meridian_support.prompts import SYSTEM_PROMPT
from meridian_support.results import tool_result_to_llm_text
from meridian_support.settings import Settings

logger = logging.getLogger(__name__)


def chat_messages_to_prior_turns(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize UI chat history (user/assistant messages) to OpenAI-style turns (no system)."""
    turns: list[dict[str, Any]] = []
    for block in history:
        role = block.get("role")
        content = block.get("content")
        if role not in ("user", "assistant"):
            continue
        text: str | None
        if isinstance(content, str):
            text = content
        elif isinstance(content, (list, tuple)):
            text = str(content)
        else:
            text = None
        if text:
            turns.append({"role": role, "content": text})
    return turns


class SupportAgent:
    """LLM orchestration with MCP tool execution; invocation is separate from result formatting."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncOpenAI | None = None
        if settings.openai_api_key.strip():
            client_kw: dict[str, Any] = {
                "api_key": settings.openai_api_key,
                "timeout": settings.request_timeout_seconds,
            }
            if settings.openai_base_url:
                client_kw["base_url"] = settings.openai_base_url
            self._client = AsyncOpenAI(**client_kw)

    async def reply(self, message: str, history: list[dict[str, Any]]) -> str:
        if self._client is None:
            return (
                "Missing OPENAI_API_KEY. Set it in the environment or Hugging Face Space secrets "
                "to enable the assistant."
            )

        prior = chat_messages_to_prior_turns(history)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *prior,
            {"role": "user", "content": message},
        ]

        mcp_url = str(self._settings.mcp_server_url)

        try:
            async with mcp_client_session(mcp_url) as session:
                mcp_tools = await list_tools_paginated(session)
                openai_tools = mcp_tools_to_openai(mcp_tools)
                return await self._run_tool_loop(session, messages, openai_tools, self._client)
        except (OSError, TimeoutError, APIConnectionError) as exc:
            logger.exception("Connectivity failure")
            return (
                "I could not reach Meridian's systems right now. Please try again in a moment. "
                f"(detail: {exc!s})"
            )
        except APIError as exc:
            logger.exception("LLM API error")
            return f"The AI service returned an error: {exc!s}"

    async def _run_tool_loop(
        self,
        session: ClientSession,
        messages: list[dict[str, Any]],
        openai_tools: list[dict[str, Any]],
        client: AsyncOpenAI,
    ) -> str:
        rounds = 0
        while rounds < self._settings.max_tool_rounds:
            rounds += 1
            try:
                completion = await client.chat.completions.create(
                    model=self._settings.llm_model,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )
            except RateLimitError as exc:
                return f"Rate limited by the AI provider. Please wait and retry. ({exc!s})"

            choice = completion.choices[0]
            assistant = choice.message

            if assistant.tool_calls:
                dump = assistant.model_dump(exclude_none=True)
                messages.append(dump)
                for tc in assistant.tool_calls:
                    name = tc.function.name
                    raw = tc.function.arguments or "{}"
                    try:
                        args: dict[str, Any] = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON arguments for %s: %s", name, raw)
                        args = {}
                    result = await invoke_tool(session, name, args)
                    text_for_llm = tool_result_to_llm_text(result)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": text_for_llm,
                        }
                    )
                continue

            text = (assistant.content or "").strip()
            if text:
                return text
            return "I do not have a response yet — could you rephrase your question?"

        return (
            "Stopped after too many tool rounds to protect cost and latency. "
            "Please narrow your request or try again."
        )
