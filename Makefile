.PHONY: install check lint types test audit

install:
	pip install -r requirements-dev.txt

check: lint types test

lint:
	ruff check service tools
	ruff format --check service tools

types:
	mypy

# Tests, a 90% overall coverage floor, then 90% branch coverage on the business rules.
test:
	coverage run -m pytest -q
	coverage report
	coverage json -q
	python tools/check_branch_coverage.py coverage.json

audit:
	pip-audit -r requirements.txt
