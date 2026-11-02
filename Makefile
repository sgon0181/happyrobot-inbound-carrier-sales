.PHONY: install check lint types test audit

install:
	pip install -r requirements-dev.txt

check: lint types test

lint:
	ruff check service
	ruff format --check service

types:
	mypy

# Tests, then the branch coverage gate set in pyproject.toml.
test:
	coverage run -m pytest -q
	coverage report

audit:
	pip-audit -r requirements.txt
