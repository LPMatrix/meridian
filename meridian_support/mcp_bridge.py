from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import CallToolResult, Tool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def mcp_client_session(server_url: str) -> AsyncIterator[ClientSession]:
    """Initialize MCP session exactly once before tools/list or tools/call."""
    async with streamablehttp_client(server_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def list_tools_paginated(session: ClientSession) -> list[Tool]:
    """Full discovery including pagination (do not assume first page is complete)."""
    tools: list[Tool] = []
    cursor: str | None = None
    while True:
        page = await session.list_tools(cursor=cursor)
        tools.extend(page.tools)
        if page.nextCursor is None:
            break
        cursor = page.nextCursor
    logger.info("Discovered %d MCP tools", len(tools))
    return tools


async def invoke_tool(
    session: ClientSession,
    name: str,
    arguments: dict[str, Any] | None,
    *,
    sensitive_tools: frozenset[str] = frozenset({"verify_customer_pin"}),
) -> CallToolResult:
    """Thin wrapper around tools/call; logs tool name only for sensitive calls."""
    args = arguments or {}
    if name in sensitive_tools:
        logger.info("MCP tools/call: %s (arguments redacted)", name)
    else:
        logger.debug("MCP tools/call: %s %s", name, args)
    return await session.call_tool(name, args)
