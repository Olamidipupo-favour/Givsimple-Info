.PHONY: help init-db run test lint clean install dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

init-db: ## Initialize database
	flask db init
	flask db migrate -m "Initial migration"
	flask db upgrade

run: ## Run the application
	flask run --host=0.0.0.0 --port=8000

dev: ## Run in development mode
	FLASK_ENV=development flask run --host=0.0.0.0 --port=8000 --reload

test: ## Run tests
	pytest -v --cov=app tests/

test-html: ## Run tests with HTML coverage report
	pytest --cov=app --cov-report=html tests/
	@echo "Coverage report generated in htmlcov/"

lint: ## Run linters
	flake8 app/ tests/
	black --check app/ tests/

format: ## Format code
	black app/ tests/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop services with Docker Compose
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in running container
	docker-compose exec web bash

docker-db-shell: ## Open database shell
	docker-compose exec db psql -U givsimple -d givsimple

migrate: ## Run database migrations
	flask db upgrade

create-migration: ## Create new migration
	@read -p "Enter migration message: " msg; \
	flask db migrate -m "$$msg"

import-tags: ## Import tags from CSV (requires CSV file)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make import-tags FILE=path/to/tags.csv"; \
		exit 1; \
	fi
	python scripts/import_tags.py $(FILE)

export-tags: ## Export tags to CSV
	python scripts/export_tags.py

setup: install init-db ## Complete setup (install + init-db)

ci: lint test ## Run CI checks (lint + test)
