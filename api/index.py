"""Vercel Python serverless entry — POST https://<deployment>/api"""

from meridian_api.server import create_vercel_chat_app

app = create_vercel_chat_app()
