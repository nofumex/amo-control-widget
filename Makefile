.PHONY: install lint format typecheck test test-cov migrate run-api run-worker widget-install widget-build package-widget ci

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check backend

format:
	ruff format backend
	ruff check backend --fix

typecheck:
	mypy backend

test:
	pytest

test-cov:
	pytest --cov=app --cov-report=term-missing

migrate:
	cd backend && alembic -c app/db/alembic.ini upgrade head

run-api:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	cd backend && python -m app.worker.main

widget-install:
	cd widget && npm install

widget-build:
	cd widget && npm run typecheck && npm run build

package-widget:
	cd widget && npm run build && npm run zip:private && npm run zip:public

ci: lint typecheck test widget-build package-widget
