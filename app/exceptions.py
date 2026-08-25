import httpx


class DomainError(Exception):
    """Базовое доменное исключение.

    У каждого подкласса — атрибут ``message`` с предзаданным текстом,
    который handler возвращает клиенту в поле ``detail``.
    Кастомный текст можно передать в конструктор, он переопределит дефолт.
    """

    message: str = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        text = message or self.message
        super().__init__(text)
        self.message = text


class AssistantNotFound(DomainError):
    message = "Assistant not found"


class AssistantAlreadyExists(DomainError):
    message = "Assistant with this langflow_flow_id already registered in tenant"


class LangflowFlowNotFound(DomainError):
    message = "Flow no longer exists in Langflow — re-register assistant"


class LangflowUnavailable(DomainError):
    message = "Could not reach Langflow (network error or timeout)"


class LangflowError(DomainError):
    message = "Langflow returned an error"

    def __init__(self, status_code: int, detail: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = self.message  # синоним для совместимости с exception handler

    @classmethod
    def from_response(cls, response: httpx.Response) -> LangflowError:
        try:
            detail = str(response.json()["detail"])
        except (ValueError, KeyError, TypeError):
            detail = response.text
        return cls(status_code=response.status_code, detail=detail)
