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

# ----------- PRODUCTION COMMANDS ----------- #

# waiting...

# ----------- HELPERS ----------- #

help:
	@echo "Usage: make <target>"
	@awk 'BEGIN {FS = ":.*##"} /^[0-9a-zA-Z_-]+:.*?## / { printf "  * %-20s -%s\n", $$1, $$2 }' $(MAKEFILE_LIST)
