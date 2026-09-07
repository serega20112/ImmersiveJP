import uvicorn

from src.config.settings import settings
from src.infrastructures.observability import configure_logging
from src.presentation.http.app import create_app

configure_logging(settings.app.log_level)
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.app.app_host,
        port=settings.app.app_port,
        reload=settings.app.app_debug,
        log_config=None,
    )
