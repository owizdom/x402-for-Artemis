.PHONY: help build up down logs shell dbt-run dbt-test dbt-docs clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose -f config/docker-compose.yml build

up: ## Start services
	docker-compose -f config/docker-compose.yml up -d

down: ## Stop services
	docker-compose -f config/docker-compose.yml down

logs: ## View logs
	docker-compose -f config/docker-compose.yml logs -f x402-pipeline

shell: ## Open shell in container
	docker-compose -f config/docker-compose.yml exec x402-pipeline /bin/bash

dbt-run: ## Run dbt transformations
	docker-compose -f config/docker-compose.yml run --rm dbt dbt run --profiles-dir dbt

dbt-test: ## Run dbt tests
	docker-compose -f config/docker-compose.yml run --rm dbt dbt test --profiles-dir dbt

dbt-docs: ## Generate dbt documentation
	docker-compose -f config/docker-compose.yml run --rm dbt dbt docs generate --profiles-dir dbt

dbt-compile: ## Compile dbt models
	docker-compose -f config/docker-compose.yml run --rm dbt dbt compile --profiles-dir dbt

clean: ## Clean up generated files
	rm -rf dbt/target dbt/dbt_packages
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

install: ## Install dependencies in virtual environment
	python3 -m venv venv || true
	. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

setup: ## Run complete setup script
	bash scripts/setup.sh

test-local: ## Test pipeline locally (with venv)
	. venv/bin/activate && python src/x402_pipeline.py list

fetch-all: ## Fetch all queries locally (with venv)
	. venv/bin/activate && python src/x402_pipeline.py fetch-all

export: ## Export data locally (with venv)
	. venv/bin/activate && python src/x402_pipeline.py export

dbt-local: ## Run dbt locally (with venv)
	. venv/bin/activate && dbt run --profiles-dir dbt --project-dir .

dbt-test-local: ## Run dbt tests locally (with venv)
	. venv/bin/activate && dbt test --profiles-dir dbt --project-dir .
