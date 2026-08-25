import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    AssistantAlreadyExists,
    AssistantNotFound,
    LangflowError,
    LangflowFlowNotFound,
    LangflowUnavailable,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AssistantNotFound)
    async def _not_found(_: Request, exc: AssistantNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc) or "assistant not found"},
        )

    @app.exception_handler(AssistantAlreadyExists)
    async def _conflict(_: Request, exc: AssistantAlreadyExists) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(LangflowFlowNotFound)
    async def _flow_not_found(_: Request, exc: LangflowFlowNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(LangflowError)
    async def _upstream(_: Request, exc: LangflowError) -> JSONResponse:
        logger.warning(
            "langflow error",
            extra={"status_code": exc.status_code, "detail": exc.detail},
        )
        return JSONResponse(
            status_code=502,
            content={"detail": f"Langflow: {exc.detail}"},
        )

    @app.exception_handler(LangflowUnavailable)
    async def _unavailable(_: Request, exc: LangflowUnavailable) -> JSONResponse:
        logger.warning("langflow unavailable", extra={"detail": str(exc)})
        return JSONResponse(status_code=503, content={"detail": str(exc)})
