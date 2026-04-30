from __future__ import annotations

from mcp.types import CallToolResult, TextContent

from meridian_support.results import tool_result_to_llm_text


def test_tool_result_formats_text_and_error_flag() -> None:
    result = CallToolResult(
        content=[TextContent(type="text", text="Stock: 3")],
        isError=False,
    )
    raw = tool_result_to_llm_text(result)
    assert "Stock: 3" in raw
    assert '"is_error": false' in raw
