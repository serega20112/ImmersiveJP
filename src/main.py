import uvicorn

from src.backend.create_app import create_app
from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.observability import configure_logging

configure_logging(Settings.log_level)
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=Settings.app_host,
        port=Settings.app_port,
        reload=Settings.app_debug,
        log_config=None,
    )
