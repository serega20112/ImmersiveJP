from __future__ import annotations

import uvicorn

from src.backend.create_app import create_app
from src.backend.dependencies.settings import Settings

app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=Settings.app_host,
        port=Settings.app_port,
        reload=Settings.app_debug,
    )
