import asyncio
import os

from meridian_support.mcp_bridge import list_tools_paginated, mcp_client_session

MCP_URL = os.environ.get(
    "MCP_SERVER_URL",
    "https://order-mcp-74afyau24q-uc.a.run.app/mcp",
)


async def discover() -> None:
    async with mcp_client_session(MCP_URL) as session:
        tools = await list_tools_paginated(session)
        for tool in tools:
            print(f"\n--- {tool.name} ---")
            print(tool.description)
            print(tool.inputSchema)


asyncio.run(discover())
