from __future__ import annotations

from typing import Any

from mcp.types import Tool


def mcp_tool_to_openai_chat_tool(tool: Tool) -> dict[str, Any]:
    """Map MCP JSON Schema (inputSchema) to OpenAI Chat Completions tool format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": (tool.description or "").strip(),
            "parameters": tool.inputSchema,
        },
    }


def mcp_tools_to_openai(tools: list[Tool]) -> list[dict[str, Any]]:
    return [mcp_tool_to_openai_chat_tool(t) for t in tools]
