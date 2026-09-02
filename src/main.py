import uvicorn

from src.config.settings import Settings
from src.infrastructures.observability import configure_logging
from src.presentation.http.app import create_app

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
