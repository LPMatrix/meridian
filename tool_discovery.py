import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def discover():
    async with streamablehttp_client("https://order-mcp-74afyau24q-uc.a.run.app/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"\n--- {tool.name} ---")
                print(tool.description)
                print(tool.inputSchema)

asyncio.run(discover())