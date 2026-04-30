"""
Vercel FastAPI entrypoint.

Vercel discovers `app` at `src/index.py` (see FastAPI on Vercel docs), not under
root `api/` — that layout is legacy per-file functions and often yields empty
matches for `vercel.json` `functions` patterns.
"""

from meridian_api.server import app

__all__ = ["app"]
