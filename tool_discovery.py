import asyncio
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = os.environ.get(
    "MCP_SERVER_URL",
    "https://order-mcp-74afyau24q-uc.a.run.app/mcp",
)


async def discover() -> None:
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"\n--- {tool.name} ---")
                print(tool.description)
                print(tool.inputSchema)

asyncio.run(discover())