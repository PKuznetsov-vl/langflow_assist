from uuid import uuid4

import pytest

from app.api.deps import RequestContext, Role
from app.dto.assistant import CreateAssistantDTO
from app.exceptions import AssistantAlreadyExists, AssistantNotFound
from app.services.assistant_service import AssistantService


def _ctx(project_id: str = "project-1", user_id: str = "user-1") -> RequestContext:
    return RequestContext(user_id=user_id, project_id=project_id, role=Role.MEMBER)


class TestCreate:
    async def test_saves_with_tenant_and_author(self, test_session_maker):
        service = AssistantService(session_maker=test_session_maker)
        body = CreateAssistantDTO(name="Assistant 1", description=None, langflow_flow_id="flow-1")
        result = await service.create(body, _ctx())
        assert result.project_id == "project-1"
        assert result.created_by == "user-1"
        assert result.name == "Assistant 1"

    async def test_duplicate_flow_in_project_raises(self, test_session_maker):
        service = AssistantService(session_maker=test_session_maker)
        body = CreateAssistantDTO(name="A", description=None, langflow_flow_id="flow-dup")
        await service.create(body, _ctx())
        with pytest.raises(AssistantAlreadyExists):
            await service.create(body, _ctx())

    async def test_same_flow_in_different_projects_is_allowed(self, test_session_maker):
        service = AssistantService(session_maker=test_session_maker)
        body = CreateAssistantDTO(name="A", description=None, langflow_flow_id="flow-shared")
        await service.create(body, _ctx(project_id="project-1"))
        result_b = await service.create(body, _ctx(project_id="project-2"))
        assert result_b.project_id == "project-2"


class TestList:
    async def test_returns_only_own_tenant(self, test_session_maker):
        service = AssistantService(session_maker=test_session_maker)
        await service.create(
            CreateAssistantDTO(name="mine", description=None, langflow_flow_id="f1"),
            _ctx(project_id="project-1"),
        )
        await service.create(
            CreateAssistantDTO(name="other", description=None, langflow_flow_id="f2"),
            _ctx(project_id="project-2"),
        )

        listed = await service.list(_ctx(project_id="project-1"))
        assert len(listed) == 1
        assert listed[0].name == "mine"


class TestRun:
    async def test_delegates_to_langflow(self, test_session_maker, fake_langflow):
        service = AssistantService(session_maker=test_session_maker, langflow=fake_langflow)
        assistant = await service.create(
            CreateAssistantDTO(name="A", description=None, langflow_flow_id="f-run"),
            _ctx(),
        )
        result = await service.run(assistant.id, "hello", _ctx())
        assert result.assistant_id == assistant.id
        assert result.output == "mocked langflow output"
        fake_langflow.run_flow.assert_awaited_once_with(flow_id="f-run", input_value="hello")

    async def test_cross_tenant_run_raises_not_found(self, test_session_maker, fake_langflow):
        service = AssistantService(session_maker=test_session_maker, langflow=fake_langflow)
        assistant = await service.create(
            CreateAssistantDTO(name="A", description=None, langflow_flow_id="f-x"),
            _ctx(project_id="project-1"),
        )
        with pytest.raises(AssistantNotFound):
            await service.run(assistant.id, "hi", _ctx(project_id="project-2"))
        fake_langflow.run_flow.assert_not_awaited()

    async def test_unknown_id_raises_not_found(self, test_session_maker, fake_langflow):
        service = AssistantService(session_maker=test_session_maker, langflow=fake_langflow)
        with pytest.raises(AssistantNotFound):
            await service.run(uuid4(), "hi", _ctx())
