FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry>=2.0,<3.0"

WORKDIR /app

# Зависимости — отдельный слой, чтобы docker кешировал их при изменении кода.
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root

# Код
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
