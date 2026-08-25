from typing import Any

import httpx
from fastapi import Request

from app.exceptions import (
    LangflowError,
    LangflowFlowNotFound,
    LangflowUnavailable,
)


class LangflowClient:
    """Обёртка над httpx.AsyncClient для запуска flow в Langflow.

    Один экземпляр на приложение — создаётся в lifespan, закрывается там же.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        api_key: str | None = None,
    ) -> None:
        headers = {"x-api-key": api_key} if api_key else None
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def run_flow(self, flow_id: str, input_value: str) -> str:
        payload = {
            "input_value": input_value,
            "output_type": "chat",
            "input_type": "chat",
        }
        try:
            response = await self._client.post(f"/api/v1/run/{flow_id}", json=payload)
        except httpx.RequestError as exc:
            raise LangflowUnavailable(f"Langflow request failed: {exc}") from exc

        if response.status_code == 404:
            raise LangflowFlowNotFound(
                f"flow {flow_id} not found in Langflow — re-register assistant"
            )
        if response.status_code >= 400:
            raise LangflowError.from_response(response)

        return self._extract_message(response.json())

    @staticmethod
    def _extract_message(payload: dict[str, Any]) -> str:
        try:
            return str(payload["outputs"][0]["outputs"][0]["results"]["message"]["text"])
        except (KeyError, IndexError, TypeError) as exc:
            raise LangflowError(502, f"Unexpected Langflow payload: {exc}") from exc


def get_langflow_client(request: Request) -> LangflowClient:
    """DI: достаём singleton, положенный в app.state.langflow в lifespan."""
    client: LangflowClient = request.app.state.langflow
    return client
