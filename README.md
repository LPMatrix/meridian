# Meridian Electronics · Customer Support

Web chat (static **HTML/CSS/JS** in `public/`) talks to a **FastAPI** backend (`POST /api`, alias `POST /api/chat`) that drives **OpenAI tool-calling** (default `gpt-4o-mini`) and Meridian’s **Streamable HTTP MCP** ordering service, so the model only asserts facts returned by tools (`list_products`, `search_products`, `get_product`, customer auth, orders, `create_order`, etc.).

## Architecture

| Layer                              | Responsibility                                                                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `meridian_support/mcp_bridge.py`   | MCP session lifecycle (`initialize` before anything else), paginated `list_tools`, redacted logging for sensitive tools   |
| `meridian_support/openai_tools.py` | Maps MCP `inputSchema` → OpenAI function parameters (no hardcoded shapes)                                                |
| `meridian_support/results.py`      | MCP `CallToolResult` → compact JSON text for LLM (`tool_result_to_llm_text`)                                              |
| `meridian_support/agent.py`        | Tool loop: completions ↔ MCP `invoke_tool`; connectivity errors surfaced to users                                        |
| `meridian_api/server.py`           | FastAPI: `POST /api` (and `/api/chat`), local static files from `public/`                                                 |
| `public/`                          | `index.html`, `css/style.css`, `js/app.js` — CDN on Vercel                                                               |
| `src/index.py`                     | **Vercel** FastAPI entry — re-exports `app` (see [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)) |
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
   - Serve **`public/`** from the edge CDN (`/`, `/css/…`, `/js/…`).
   - Build the FastAPI app from **`src/index.py`** (single Fluid compute function). Chat: **`POST /api`** (same as local).
4. In the project dashboard, increase **Function max duration** if MCP/LLM runs time out (defaults are lower than local `uvicorn`).
5. Upgrade the CLI if prompted (`npm i -g vercel@latest`).

Avoid a root **`api/*.py`** layout for this repo: Vercel’s FastAPI preset expects entries like **`src/index.py`** or **`app/main.py`**, and `vercel.json` → `functions` patterns only match files Vercel actually emits as serverless functions — which often excludes ad‑hoc `api/chat.py` style files when the project is detected as FastAPI + static.

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
