# -- General
SHELL := /bin/bash

# -- Docs
DOCS_TAPES_PATH = scripts/docs
DOCS_GIFS_PATH  = docs/img/tapes
DOCS_TAPES      = $(wildcard $(DOCS_TAPES_PATH)/*.tape)
DOCS_GIFS       = $(addprefix $(DOCS_GIFS_PATH)/,$(patsubst %.tape,%.gif,$(notdir $(DOCS_TAPES))))

# ==============================================================================
# RULES

default: help

docs/openapi.json:
	uv run onzr openapi > docs/openapi.json

$(DOCS_GIFS_PATH)/%.gif: $(DOCS_TAPES_PATH)/%.tape 
	@echo -e "---\n📼 $< → $@"
	# Unset MAILCHECK to avoid notification in generated GIFs
	unset MAILCHECK; uv run vhs $< -o $@

# -- Build
bootstrap: ## bootstrap the project for development
bootstrap: \
  docs/openapi.json \
  build
.PHONY: bootstrap

build: ## install project
	uv sync --locked --all-extras --dev
.PHONY: build

docs-gifs: ## compile all tapes included in the docs
docs-gifs: $(DOCS_GIFS)
	@echo "✅ Documentation GIFs updated"
.PHONY: docs-gifs

docs-serve: ## run documentation server 
	# Force OpenAPI schema generation
	uv run onzr openapi > docs/openapi.json
	uv run mkdocs serve
.PHONY: docs-serve

docs-publish: ## publish documentation
	uv run mkdocs gh-deploy --force
.PHONY: docs-publish

run: ## run onzr server in development mode
	uv run uvicorn onzr.server:app --host localhost --port 9473 --reload --log-config logging-config.yaml
.PHONY: run

# -- Quality
lint: ## lint all sources
lint: \
  lint-black \
  lint-ruff \
  lint-mypy
.PHONY: lint

lint-black: ## lint python sources with black
	@echo 'lint:black started…'
	uv run black src/onzr tests
.PHONY: lint-black

lint-black-check: ## check python sources with black
	@echo 'lint:black check started…'
	uv run black --check src/onzr tests
.PHONY: lint-black-check

lint-ruff: ## lint python sources with ruff
	@echo 'lint:ruff started…'
	uv run ruff check src/onzr tests
.PHONY: lint-ruff

lint-ruff-fix: ## lint and fix python sources with ruff
	@echo 'lint:ruff-fix started…'
	uv run ruff check --fix src/onzr tests
.PHONY: lint-ruff-fix

lint-mypy: ## lint python sources with mypy
	@echo 'lint:mypy started…'
	uv run mypy src/onzr tests
.PHONY: lint-mypy

test: ## run tests
	uv run pytest
.PHONY: test

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
