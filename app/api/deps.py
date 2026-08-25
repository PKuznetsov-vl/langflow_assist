from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.external.db import get_session_maker
from app.external.langflow import LangflowClient, get_langflow_client


class Role(StrEnum):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


@dataclass(frozen=True, slots=True)
class RequestContext:
    user_id: str
    project_id: str
    role: Role


async def get_context(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    x_project_id: Annotated[str | None, Header(alias="X-Project-Id")] = None,
    x_role: Annotated[str | None, Header(alias="X-Role")] = None,
) -> RequestContext:
    if not (x_user_id and x_project_id and x_role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tenant headers (X-User-Id, X-Project-Id, X-Role)",
        )
    try:
        role = Role(x_role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid X-Role: {x_role}. Expected one of: {', '.join(r.value for r in Role)}",
        ) from exc

    return RequestContext(user_id=x_user_id, project_id=x_project_id, role=role)


def require_roles(*allowed: Role) -> Callable[[RequestContext], RequestContext]:
    """DI-фабрика для разграничения по ролям.

    На текущий момент все три эндпоинта доступны любой роли — вызывается как
    `require_roles(Role.MEMBER, Role.ADMIN, Role.OWNER)`. Заголовок валидируется,
    но по факту не рестриктит.

    Когда появится "удалять может только admin/owner" — заменяется одной строкой.
    """
    allowed_set = frozenset(allowed)

    def _check(ctx: Annotated[RequestContext, Depends(get_context)]) -> RequestContext:
        if ctx.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{ctx.role.value}' is not allowed for this endpoint",
            )
        return ctx

    return _check


# Типовые алиасы, чтобы сигнатуры хендлеров были короткими.
type Ctx = Annotated[RequestContext, Depends(get_context)]
type SessionMaker = Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)]
type Langflow = Annotated[LangflowClient, Depends(get_langflow_client)]
