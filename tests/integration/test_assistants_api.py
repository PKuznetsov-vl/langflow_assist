from uuid import uuid4


class TestCreateAssistant:
    async def test_returns_201_and_body(self, client, tenant_headers):
        r = await client.post(
            "/assistants",
            headers=tenant_headers,
            json={
                "name": "Помощник рекрутера",
                "description": "Анализирует резюме",
                "langflow_flow_id": "flow-1",
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Помощник рекрутера"
        assert body["langflow_flow_id"] == "flow-1"
        assert "id" in body and "created_at" in body

    async def test_missing_headers_returns_400(self, client):
        r = await client.post(
            "/assistants",
            json={"name": "x", "description": None, "langflow_flow_id": "f"},
        )
        assert r.status_code == 400

    async def test_invalid_role_returns_400(self, client, tenant_headers):
        headers = {**tenant_headers, "X-Role": "superuser"}
        r = await client.post(
            "/assistants",
            headers=headers,
            json={"name": "x", "description": None, "langflow_flow_id": "f"},
        )
        assert r.status_code == 400

    async def test_short_name_returns_422(self, client, tenant_headers):
        r = await client.post(
            "/assistants",
            headers=tenant_headers,
            json={"name": "", "description": None, "langflow_flow_id": "f"},
        )
        assert r.status_code == 422

    async def test_duplicate_flow_in_tenant_returns_409(self, client, tenant_headers):
        payload = {"name": "A", "description": None, "langflow_flow_id": "dup-flow"}
        r1 = await client.post("/assistants", headers=tenant_headers, json=payload)
        r2 = await client.post("/assistants", headers=tenant_headers, json=payload)
        assert r1.status_code == 201
        assert r2.status_code == 409


class TestListAssistants:
    async def test_lists_only_own_tenant(self, client, tenant_headers, other_tenant_headers):
        await client.post(
            "/assistants",
            headers=tenant_headers,
            json={"name": "mine", "description": None, "langflow_flow_id": "f-mine"},
        )
        await client.post(
            "/assistants",
            headers=other_tenant_headers,
            json={"name": "other", "description": None, "langflow_flow_id": "f-other"},
        )

        r = await client.get("/assistants", headers=tenant_headers)
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["name"] == "mine"

    async def test_empty_list(self, client, tenant_headers):
        r = await client.get("/assistants", headers=tenant_headers)
        assert r.status_code == 200
        assert r.json() == []


class TestRunAssistant:
    async def test_happy_path(self, client, tenant_headers, fake_langflow):
        created = await client.post(
            "/assistants",
            headers=tenant_headers,
            json={"name": "A", "description": None, "langflow_flow_id": "flow-run"},
        )
        assistant_id = created.json()["id"]

        r = await client.post(
            f"/assistants/{assistant_id}/run",
            headers=tenant_headers,
            json={"input": "Оцени это резюме"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["assistant_id"] == assistant_id
        assert body["output"] == "mocked langflow output"
        fake_langflow.run_flow.assert_awaited_once_with(
            flow_id="flow-run", input_value="Оцени это резюме"
        )

    async def test_cross_tenant_returns_404(self, client, tenant_headers, other_tenant_headers):
        created = await client.post(
            "/assistants",
            headers=tenant_headers,
            json={"name": "A", "description": None, "langflow_flow_id": "flow-x"},
        )
        assistant_id = created.json()["id"]

        r = await client.post(
            f"/assistants/{assistant_id}/run",
            headers=other_tenant_headers,
            json={"input": "hi"},
        )
        assert r.status_code == 404

    async def test_unknown_id_returns_404(self, client, tenant_headers):
        r = await client.post(
            f"/assistants/{uuid4()}/run",
            headers=tenant_headers,
            json={"input": "hi"},
        )
        assert r.status_code == 404

    async def test_empty_input_returns_422(self, client, tenant_headers):
        created = await client.post(
            "/assistants",
            headers=tenant_headers,
            json={"name": "A", "description": None, "langflow_flow_id": "flow-empty"},
        )
        r = await client.post(
            f"/assistants/{created.json()['id']}/run",
            headers=tenant_headers,
            json={"input": ""},
        )
        assert r.status_code == 422
