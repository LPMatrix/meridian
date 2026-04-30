from __future__ import annotations

import json
from typing import Any

from mcp.types import CallToolResult, TextContent


def tool_result_to_llm_text(result: CallToolResult) -> str:
    """Separate raw MCP payloads from narrative formatting for the LLM context."""
    parts: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        else:
            parts.append(block.model_dump_json())
    body = "\n".join(parts) if parts else ""
    payload: dict[str, Any] = {
        "is_error": result.isError,
        "text": body,
    }
    if result.structuredContent is not None:
        payload["structured"] = result.structuredContent
    return json.dumps(payload, ensure_ascii=False)
