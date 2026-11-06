.PHONY: install hooks check lint types test audit run secrets deploy review review-down zip

install:
	pip install -r requirements-dev.txt

# Run make check before every commit, as CI does on every push.
hooks:
	git config core.hooksPath .githooks

check: lint types test

lint:
	ruff check service tools
	ruff format --check service tools
	python tools/check_service_shape.py
	python tools/check_docs.py

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

# The cloud target and native App are explicit. No default targets the preserved release.
export APP APP_URL

# Run the production image locally with intentionally supplied settings.
run:
	docker build -t carrier-sales .
	docker run --rm -p 127.0.0.1:8080:8080 --env-file .env carrier-sales

# Disposable local App, identity provider, Twin, mailbox and real loopback TCP simulator.
review:
	python3 tools/launch.py review

review-down:
	python3 tools/launch.py review-down

# Copies only service settings from .env and environment. Never prints their values.
secrets:
	python3 tools/launch.py secrets

deploy:
	python3 tools/launch.py deploy

# Source ZIP of the committed HEAD for the portal. .gitattributes leaves out study material.
zip:
	mkdir -p ../submission-release
	git archive --format=zip --prefix=carrier-sales/ \
		-o ../submission-release/carrier-sales-$$(git rev-parse --short HEAD).zip HEAD
