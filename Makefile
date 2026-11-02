.PHONY: install check lint types test coverage audit

install:
	pip install -r requirements-dev.txt

check: lint types test

lint:
	ruff check service
	ruff format --check service

types:
	mypy

# Exit code 5 means pytest found no tests. Remove the allowance in slice 1.
test:
	pytest -q || test $$? -eq 5

coverage:
	coverage run -m pytest -q
	coverage report

audit:
	pip-audit -r requirements.txt
