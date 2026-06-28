.PHONY: install test lint typecheck widget-build widget-zip

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check backend

typecheck:
	mypy backend || true

widget-build:
	cd widget && npm install && npm run build

widget-zip:
	cd widget && npm run zip:private && npm run zip:public
