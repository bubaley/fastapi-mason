ifneq (,$(wildcard .env))
	include .env
	export $(shell sed 's/=.*//' .env)
endif

timestamp = $(shell date +"%Y-%m-%d %H:%M:%S.%3N")
log = echo $(call timestamp) $(1)
wait-for = $(call log,"👀$(2) waiting...") && wait-for $(1) && $(call log,"☑️$(2) ready")

# ----------- SHORT COMMANDS ----------- #

r: run ## short run runserver

# ----------- BASE COMMANDS ----------- #

run: ## run runserver
	uvicorn app.main:app --reload

lint: ## run lint
	pre-commit run --all-files

# ----------- DOCUMENTATION COMMANDS ----------- #

docs-install:  ## Install documentation dependencies
	uv sync --group docs

docs-serve:  ## Serve documentation locally
	uv run mkdocs serve -a 0.0.0.0:9999

docs-build:  ## Build documentation
	uv run mkdocs build --clean --strict

docs-check:  ## Check documentation for issues
	@echo "Checking documentation..."
	uv run python scripts/test-docs.py

docs-clean:  ## Clean documentation build artifacts
	rm -rf site/

help:
	@echo "Usage: make <target>"
	@awk 'BEGIN {FS = ":.*##"} /^[0-9a-zA-Z_-]+:.*?## / { printf "  * %-20s -%s\n", $$1, $$2 }' $(MAKEFILE_LIST)
