.PHONY: help install format lint type-check test test-cov test-system ci run \
	migrate migration downgrade compose-up compose-down compose-clean

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

CODE = app tests
MANAGER = poetry run
COMPOSE = docker compose -f deploy/docker-compose.yml --env-file deploy/.env

help:  ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:  ## poetry install со всеми группами
	poetry install --with dev

format:  ## ruff: import-sort + format
	$(MANAGER) ruff check --select I --fix $(CODE)
	$(MANAGER) ruff format $(CODE)

lint:  ## ruff check + mypy
	$(MANAGER) ruff format --diff $(CODE)
	$(MANAGER) ruff check $(CODE)
	$(MANAGER) mypy app

type-check:  ## только mypy
	$(MANAGER) mypy app

test:  ## unit + integration (без system)
	$(MANAGER) pytest -v

test-cov:  ## pytest с coverage
	$(MANAGER) pytest -v --cov=app --cov-report=term-missing --cov-report=xml

test-system:  ## только системные тесты (нужен живой Langflow + LANGFLOW_TEST_FLOW_ID)
	$(MANAGER) pytest -v tests/system --system

ci: format lint test  ## всё, что должно быть зелёным перед PR

run:  ## uvicorn с --reload (локально, postgres — из docker или на хосте)
	$(MANAGER) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

migrate:  ## применить миграции
	$(MANAGER) alembic upgrade head

migration:  ## сгенерировать миграцию: make migration name="add field X"
	$(MANAGER) alembic revision --autogenerate -m "$(name)"

downgrade:  ## откатить на 1 миграцию
	$(MANAGER) alembic downgrade -1

compose-up:  ## поднять postgres + migrator + сервис
	$(COMPOSE) up --build

compose-down:  ## остановить всё
	$(COMPOSE) down

compose-clean:  ## остановить + удалить volume БД
	$(COMPOSE) down -v
