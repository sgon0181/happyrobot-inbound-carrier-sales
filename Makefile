.PHONY: install check lint types test audit run secrets deploy

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

# The settings the service reads, and nothing else from .env (config.py lists the same names).
SECRETS := TMS_HOST|TMS_PORT|TMS_TOKEN|FMCSA_API_KEY|HAPPYROBOT_API_KEY|HAPPYROBOT_ORG_ID|AGENT_API_KEY|OPS_API_KEY|OTP_HASH_SECRET|PRICING_SECRET|OTP_EMAIL_USER|OTP_EMAIL_CREDENTIAL|DEMO_OTP_EMAIL|CALL_COHORT|LIVE_BOOKING
APP := $(shell sed -n 's/^app = "\(.*\)"/\1/p' fly.toml)

# Run the image locally with the local .env.
run:
	docker build -t carrier-sales .
	docker run --rm -p 8080:8080 --env-file .env carrier-sales

# Copy the service's settings from .env into Fly secrets. Values are never printed.
secrets:
	grep -E '^($(SECRETS))=' .env | fly secrets import --app $(APP) --stage

deploy:
	fly deploy --app $(APP) --ha=false
