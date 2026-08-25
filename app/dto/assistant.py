from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateAssistantDTO(BaseModel):
    """Тело POST /assistants."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    langflow_flow_id: str = Field(min_length=1, max_length=64)


class AssistantDTO(BaseModel):
    """Ответ POST /assistants и элемент массива в GET /assistants."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    langflow_flow_id: str
    created_at: datetime


class RunAssistantDTO(BaseModel):
    """Тело POST /assistants/{id}/run."""

    input: str = Field(min_length=1)


class RunAssistantResponseDTO(BaseModel):
    """Ответ POST /assistants/{id}/run."""

    assistant_id: UUID
    output: str
