from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.v1 import api_router
from app.config import settings
from app.external.db import dispose_engine
from app.external.langflow import LangflowClient
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level)
    app.state.langflow = LangflowClient(
        base_url=settings.langflow_base_url,
        timeout=settings.langflow_timeout_seconds,
        api_key=settings.langflow_api_key,
    )
    try:
        yield
    finally:
        await app.state.langflow.aclose()
        await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="assistant-service", lifespan=lifespan)
    app.include_router(api_router)
    register_exception_handlers(app)

    @app.get("/health", tags=["probes"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
