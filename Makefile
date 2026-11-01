.PHONY: test deploy
APP := codex-e2e-lab-sg-20261031
IMAGE := registry.fly.io/$(APP):prototype-e2e
PYTHON := secrets/venv/bin/python

test:
	$(PYTHON) -m unittest discover -s service/tests -t .

deploy:
	$(PYTHON) -m service.scripts.deploy
