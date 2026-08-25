import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import RequestContext
from app.dto.assistant import CreateAssistantDTO, RunAssistantResponseDTO
from app.exceptions import AssistantNotFound
from app.external.langflow import LangflowClient
from app.models.assistant import Assistant
from app.repositories.assistant_repository import AssistantRepository

logger = logging.getLogger(__name__)


class AssistantService:
    """Бизнес-логика реестра ассистентов.

    Транзакциями управляет сам: `async with session_maker() as session, session.begin()`.
    Репозиторий инстанцируется на месте с переданной сессией.
    """

    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        langflow: LangflowClient | None = None,
    ) -> None:
        self._session_maker = session_maker
        self._langflow = langflow

    async def create(self, body: CreateAssistantDTO, ctx: RequestContext) -> Assistant:
        async with self._session_maker() as session, session.begin():
            assistant = Assistant(
                project_id=ctx.project_id,
                created_by=ctx.user_id,
                name=body.name,
                description=body.description,
                langflow_flow_id=body.langflow_flow_id,
            )
            await AssistantRepository(session).add(assistant)
            logger.info(
                "assistant registered",
                extra={
                    "assistant_id": str(assistant.id),
                    "project_id": ctx.project_id,
                    "user_id": ctx.user_id,
                    "flow_id": assistant.langflow_flow_id,
                },
            )
            return assistant

    async def list(self, ctx: RequestContext) -> list[Assistant]:
        async with self._session_maker() as session:
            return await AssistantRepository(session).list_by_project(ctx.project_id)

    async def run(
        self, assistant_id: UUID, input_value: str, ctx: RequestContext
    ) -> RunAssistantResponseDTO:
        if self._langflow is None:
            raise RuntimeError("LangflowClient not injected into AssistantService")

        async with self._session_maker() as session:
            assistant = await AssistantRepository(session).get_for_project(
                assistant_id, ctx.project_id
            )

        if assistant is None:
            raise AssistantNotFound()

        logger.info(
            "assistant run started",
            extra={
                "assistant_id": str(assistant.id),
                "project_id": ctx.project_id,
                "user_id": ctx.user_id,
                "flow_id": assistant.langflow_flow_id,
                "input_len": len(input_value),
            },
        )
        output = await self._langflow.run_flow(
            flow_id=assistant.langflow_flow_id,
            input_value=input_value,
        )
        logger.info(
            "assistant run finished",
            extra={
                "assistant_id": str(assistant.id),
                "project_id": ctx.project_id,
                "output_len": len(output),
            },
        )
        return RunAssistantResponseDTO(assistant_id=assistant.id, output=output)
