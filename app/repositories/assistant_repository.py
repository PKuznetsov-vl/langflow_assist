from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AssistantAlreadyExists
from app.models.assistant import Assistant


class AssistantRepository:
    """CRUD по таблице assistants. Всегда фильтрует по project_id.

    Не коммитит сам — коммит делает сервис.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, assistant: Assistant) -> Assistant:
        self._session.add(assistant)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise AssistantAlreadyExists() from exc
        return assistant

    async def list_by_project(self, project_id: str) -> list[Assistant]:
        stmt = (
            select(Assistant)
            .where(Assistant.project_id == project_id)
            .order_by(Assistant.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_for_project(self, assistant_id: UUID, project_id: str) -> Assistant | None:
        stmt = select(Assistant).where(
            Assistant.id == assistant_id,
            Assistant.project_id == project_id,
        )
        result = await self._session.scalars(stmt)
        return result.one_or_none()
