.PHONY: help setup dev check-env test lint logs down

help:
	@echo "AI-SATHI - Development Commands"
	@echo "===================================="
	@echo "make setup      - first-time setup: copy .env, validate, bring up DB"
	@echo "make dev        - start the full stack (docker compose up --build)"
	@echo "make check-env  - verify required .env values are filled in"
	@echo "make test       - run unit + integration tests (offline, no API keys)"
	@echo "make test-fast  - run core smoke tests only (~2s)"
	@echo "make lint       - ruff + mypy"
	@echo "make logs       - tail app logs"
	@echo "make down       - stop everything"

setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env - fill in the REQUIRED section before continuing."; else echo ".env already exists."; fi
	python3 backend/scripts/check_env.py || true

check-env:
	python3 backend/scripts/check_env.py

dev: check-env
	docker compose up --build

test:
	python -m pytest tests/ -q

test-fast:
	python -m pytest tests/unit/test_ledger_node.py tests/unit/test_intent_router.py tests/unit/test_ledger_confirm_node.py -q

lint:
	ruff check backend/ && mypy backend/shared/ backend/services/

logs:
	docker compose logs -f app

down:
	docker compose down
