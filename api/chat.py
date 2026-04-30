"""Vercel Python Serverless Function → POST https://<deployment>/api/chat"""

from meridian_api.server import create_vercel_chat_app

app = create_vercel_chat_app()
