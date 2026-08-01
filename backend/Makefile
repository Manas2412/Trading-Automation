.PHONY: install fmt lint type test check

install:
	pip install -e ".[dev]"

fmt:
	ruff format src tests

lint:
	ruff check src tests

type:
	mypy src

test:
	pytest -q

check: lint type test
