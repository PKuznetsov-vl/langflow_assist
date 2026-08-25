from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import Langflow, RequestContext, Role, SessionMaker, require_roles
from app.dto.assistant import (
    AssistantDTO,
    CreateAssistantDTO,
    RunAssistantDTO,
    RunAssistantResponseDTO,
)
from app.services.assistant_service import AssistantService

router = APIRouter(prefix="/assistants", tags=["assistants"])

# По задаче все три эндпоинта доступны любой роли.
# Валидация роли встроена в require_roles — placeholder на будущее.
_any_role = require_roles(Role.MEMBER, Role.ADMIN, Role.OWNER)
AnyRoleCtx = Annotated[RequestContext, Depends(_any_role)]


@router.post(
    "",
    response_model=AssistantDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать ассистента",
)
async def create_assistant(
    body: CreateAssistantDTO, ctx: AnyRoleCtx, session_maker: SessionMaker
) -> AssistantDTO:
    service = AssistantService(session_maker=session_maker)
    assistant = await service.create(body, ctx)
    return AssistantDTO.model_validate(assistant)


@router.get(
    "",
    response_model=list[AssistantDTO],
    summary="Список ассистентов текущего тенанта",
)
async def list_assistants(ctx: AnyRoleCtx, session_maker: SessionMaker) -> list[AssistantDTO]:
    service = AssistantService(session_maker=session_maker)
    assistants = await service.list(ctx)
    return [AssistantDTO.model_validate(a) for a in assistants]


@router.post(
    "/{assistant_id}/run",
    response_model=RunAssistantResponseDTO,
    summary="Запустить ассистента (проксирует в Langflow)",
)
async def run_assistant(
    assistant_id: UUID,
    body: RunAssistantDTO,
    ctx: AnyRoleCtx,
    session_maker: SessionMaker,
    langflow: Langflow,
) -> RunAssistantResponseDTO:
    service = AssistantService(session_maker=session_maker, langflow=langflow)
    return await service.run(assistant_id, body.input, ctx)
