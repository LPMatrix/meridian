from __future__ import annotations

from mcp.types import Tool

from meridian_support.openai_tools import mcp_tool_to_openai_chat_tool, mcp_tools_to_openai


def test_mcp_tool_to_openai_maps_schema() -> None:
    tool = Tool(
        name="get_product",
        description="Get SKU",
        inputSchema={
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
    )
    spec = mcp_tool_to_openai_chat_tool(tool)
    assert spec["type"] == "function"
    assert spec["function"]["name"] == "get_product"
    assert spec["function"]["description"] == "Get SKU"
    assert spec["function"]["parameters"]["required"] == ["sku"]


def test_mcp_tools_to_openai_empty() -> None:
    assert mcp_tools_to_openai([]) == []
