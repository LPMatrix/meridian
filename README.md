---

## title: Meridian Electronics — MCP Support Bot
emoji: 🛒
colorFrom: slate
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false

# Meridian Electronics · Customer Support

Gradio chat UI that connects to Meridian’s **Streamable HTTP MCP** ordering service and drives **OpenAI tool-calling** (default `gpt-4o-mini`) so the model only asserts facts returned by backend tools (`list_products`, `search_products`, `get_product`, customer auth, orders, `create_order`, etc.).

## Architecture


| Layer                              | Responsibility                                                                                                          |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `meridian_support/mcp_bridge.py`   | MCP session lifecycle (`initialize` before anything else), paginated `list_tools`, redacted logging for sensitive tools |
| `meridian_support/openai_tools.py` | Maps MCP `inputSchema` → OpenAI function parameters (no hardcoded shapes)                                               |
| `meridian_support/results.py`      | MCP `CallToolResult` → compact JSON text for LLM (`tool_result_to_llm_text`)                                            |
| `meridian_support/agent.py`        | Tool loop: completions ↔ MCP `invoke_tool`; connectivity errors surfaced to users                                       |
| `app.py`                           | Gradio UI only (`type="messages"`), wires secrets from the environment                                                  |


## Local run

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
python app.py
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860) — set `PORT` if needed.

## Hugging Face Spaces

1. New Space → **Gradio**, clone/push this repo.
2. **Settings → Secrets**: `OPENAI_API_KEY` (required). Optionally `MCP_SERVER_URL`, `LLM_MODEL`.
3. Default MCP URL matches the assessment (`order-mcp-…run.app/mcp`).
4. Capture screenshots into `screenshots/` for your submission packet.

## Configuration


| Variable          | Purpose                          |
| ----------------- | -------------------------------- |
| `OPENAI_API_KEY`  | Required for chat                |
| `MCP_SERVER_URL`  | MCP Streamable HTTP endpoint     |
| `LLM_MODEL`       | e.g. `gpt-4o-mini`               |
| `OPENAI_BASE_URL` | Optional (Azure/proxy)           |
| `MAX_TOOL_ROUNDS` | Cap tool iterations (cost guard) |


## Tests

```bash
pytest
```

## Limitations

- Single-tenant demo: no org-level RBAC, no human handoff queue.
- LLM may still mis-summarize tool text — mitigated by grounding policy in `prompts.py`, not eliminated.
- One MCP session per user turn (fresh `initialize` each time): simple and correct, higher latency than a pooled session.
- Gradio UI has **no end-user login**; “customer” identity is whatever the user types and what MCP tools return (suitable for a demo, not full production).

