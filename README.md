# Meridian Electronics · Customer Support

Web chat (static **HTML/CSS/JS** in `public/`) talks to a **FastAPI** backend (`POST /api/chat`) that drives **OpenAI tool-calling** (default `gpt-4o-mini`) and Meridian’s **Streamable HTTP MCP** ordering service, so the model only asserts facts returned by tools (`list_products`, `search_products`, `get_product`, customer auth, orders, `create_order`, etc.).

## Architecture

| Layer                              | Responsibility                                                                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `meridian_support/mcp_bridge.py`   | MCP session lifecycle (`initialize` before anything else), paginated `list_tools`, redacted logging for sensitive tools   |
| `meridian_support/openai_tools.py` | Maps MCP `inputSchema` → OpenAI function parameters (no hardcoded shapes)                                                |
| `meridian_support/results.py`      | MCP `CallToolResult` → compact JSON text for LLM (`tool_result_to_llm_text`)                                              |
| `meridian_support/agent.py`        | Tool loop: completions ↔ MCP `invoke_tool`; connectivity errors surfaced to users                                        |
| `meridian_api/server.py`           | FastAPI: `POST /api/chat`, local static files from `public/`                                                             |
| `public/`                          | `index.html`, `css/style.css`, `js/app.js` — deployable as static assets on Vercel                                       |
| `api/chat.py`                      | Same FastAPI chat routes at `POST /` for **Vercel Python Serverless** (`/api/chat`)                                       |
| `app.py`                           | Local entry: `uvicorn` on `PORT` (default 7860)                                                                         |

## Local run

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
python app.py
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860) — static UI and API share one origin.

## Deploy on Vercel

1. Connect this repo to Vercel.
2. **Environment variables** (Project → Settings → Environment Variables): same as below (`OPENAI_API_KEY`, optional `MCP_SERVER_URL`, `LLM_MODEL`, etc.).
3. Vercel will:
   - Serve files in **`public/`** at `/` (CSS/JS paths like `/css/style.css` work as-is).
   - Run **`api/chat.py`** as a Python function at **`POST /api/chat`** (see `vercel.json` for `maxDuration`).
4. Upgrade the CLI if prompted (`npm i -g vercel@latest`).

If the UI loads but chat fails, confirm secrets exist for **Production** (and Preview if you test previews).

## Hugging Face Spaces

Use a **Docker** Space or a **custom command** that runs `uvicorn meridian_api.server:app --host 0.0.0.0 --port 7860` with `OPENAI_API_KEY` in Space secrets (Gradio is no longer required).

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
- No end-user login; “customer” identity is whatever the user types and what MCP tools return (suitable for a demo, not full production).
