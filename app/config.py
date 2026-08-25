from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = Field(..., validation_alias="DATABASE_URL")

    langflow_base_url: str = Field(
        default="http://langflow:7860", validation_alias="LANGFLOW_BASE_URL"
    )
    langflow_api_key: str | None = Field(default=None, validation_alias="LANGFLOW_API_KEY")
    langflow_timeout_seconds: float = 30.0

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")


settings = Settings()
