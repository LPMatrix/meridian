from __future__ import annotations

import logging
import os

import uvicorn

from meridian_support.settings import get_settings

logging.basicConfig(
    level=getattr(logging, get_settings().log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    uvicorn.run(
        "meridian_api.server:app",
        host="0.0.0.0",
        port=port,
        log_level=get_settings().log_level.lower(),
    )
