# -- General
SHELL := /bin/bash

# ==============================================================================
# RULES

default: help

# -- Files
.secrets.toml:
	ln -s src/onzr/.secrets.toml.dist .secrets.toml

settings.toml:
	ln -s src/onzr/settings.toml.dist settings.toml

# -- Build
bootstrap: ## bootstrap the project for development
bootstrap: \
	.secrets.toml \
	settings.toml \
	build
.PHONY: bootstrap

build: ## install project
	poetry install
.PHONY: build

# -- Quality
lint: ## lint all sources
lint: \
	lint-black \
	lint-ruff \
  lint-mypy
.PHONY: lint

lint-black: ## lint python sources with black
	@echo 'lint:black started…'
	poetry run black src/onzr tests
.PHONY: lint-black

lint-black-check: ## check python sources with black
	@echo 'lint:black check started…'
	poetry run black --check src/onzr tests
.PHONY: lint-black-check

lint-ruff: ## lint python sources with ruff
	@echo 'lint:ruff started…'
	poetry run ruff check src/onzr tests
.PHONY: lint-ruff

lint-ruff-fix: ## lint and fix python sources with ruff
	@echo 'lint:ruff-fix started…'
	poetry run ruff check --fix src/onzr tests
.PHONY: lint-ruff-fix

lint-mypy: ## lint python sources with mypy
	@echo 'lint:mypy started…'
	poetry run mypy src/onzr tests
.PHONY: lint-mypy

test: ## run tests
	poetry run pytest
.PHONY: test

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
