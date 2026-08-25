import os

# Ставим переменные до первого импорта app.config.
# DATABASE_URL — валидный postgres URL, но НЕ используется:
# модульный engine создаётся (lazy, соединений не открывает),
# а тесты гоняют через собственный SQLite engine + dependency_overrides.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("LANGFLOW_BASE_URL", "http://langflow.test")

from collections.abc import AsyncIterator  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.external.db import get_session_maker  # noqa: E402
from app.external.langflow import LangflowClient, get_langflow_client  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.assistant import Base  # noqa: E402


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--system",
        action="store_true",
        default=False,
        help="Run system tests against live local Langflow",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--system"):
        return
    skip_system = pytest.mark.skip(reason="need --system flag and a running Langflow to run these")
    for item in items:
        if "system" in item.keywords:
            item.add_marker(skip_system)


@pytest_asyncio.fixture
async def test_engine() -> AsyncIterator:
    """Свежий SQLite in-memory на каждый тест — полностью изолирован."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def test_session_maker(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(test_session_maker) -> AsyncIterator[AsyncSession]:
    async with test_session_maker() as session:
        yield session


@pytest.fixture
def fake_langflow() -> LangflowClient:
    """Мок LangflowClient. Каждый тест переопределяет run_flow под свои нужды."""
    client = AsyncMock(spec=LangflowClient)
    client.run_flow = AsyncMock(return_value="mocked langflow output")
    return client


@pytest_asyncio.fixture
async def app(test_session_maker, fake_langflow):
    application = create_app()

    def _get_session_maker_override() -> async_sessionmaker[AsyncSession]:
        return test_session_maker

    def _get_langflow_override() -> LangflowClient:
        return fake_langflow

    application.dependency_overrides[get_session_maker] = _get_session_maker_override
    application.dependency_overrides[get_langflow_client] = _get_langflow_override
    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def tenant_headers() -> dict[str, str]:
    return {
        "X-User-Id": "user-1",
        "X-Project-Id": "project-1",
        "X-Role": "member",
    }


@pytest.fixture
def other_tenant_headers() -> dict[str, str]:
    return {
        "X-User-Id": "user-2",
        "X-Project-Id": "project-2",
        "X-Role": "member",
    }
