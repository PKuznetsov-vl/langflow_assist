import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app

pytestmark = pytest.mark.system

FLOW_ID = os.getenv("LANGFLOW_TEST_FLOW_ID")


@pytest.fixture
def require_env() -> None:
    if not FLOW_ID:
        pytest.skip("LANGFLOW_TEST_FLOW_ID not set")
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")
    if not os.getenv("LANGFLOW_BASE_URL"):
        pytest.skip("LANGFLOW_BASE_URL not set")


async def test_register_list_and_run_against_live_langflow(require_env) -> None:
    app = create_app()
    headers = {
        "X-User-Id": "u-sys",
        "X-Project-Id": "p-sys",
        "X-Role": "member",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Регистрация
        r = await client.post(
            "/assistants",
            headers=headers,
            json={
                "name": "sys-test-assistant",
                "description": None,
                "langflow_flow_id": FLOW_ID,
            },
        )
        assert r.status_code in (201, 409), r.text
        if r.status_code == 201:
            assistant_id = r.json()["id"]
        else:
            # уже существует от прошлого прогона — достанем из списка
            listed = await client.get("/assistants", headers=headers)
            found = next((a for a in listed.json() if a["langflow_flow_id"] == FLOW_ID), None)
            assert found is not None
            assistant_id = found["id"]

        # 2. Список — должен содержать нашего
        r = await client.get("/assistants", headers=headers)
        assert r.status_code == 200
        assert any(a["id"] == assistant_id for a in r.json())

        # 3. Запуск против живого Langflow
        r = await client.post(
            f"/assistants/{assistant_id}/run",
            headers=headers,
            json={"input": "ping"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["assistant_id"] == assistant_id
        assert isinstance(body["output"], str) and len(body["output"]) > 0
