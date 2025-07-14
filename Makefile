.PHONY: help install-dev format lint type-check fix test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

format: ## Format code with Black and isort
	black --line-length=120 .
	isort --profile=black --line-length=120 .

lint: ## Run Ruff linter
	ruff check .

lint-fix: ## Run Ruff linter with auto-fix
	ruff check --fix .

lint-fix-unsafe: ## Run Ruff linter with auto-fix unsafe-fixes
	ruff check --fix --unsafe-fixes .

type-check: ## Run mypy type checking
	mypy .

fix: ## Auto-fix all linting issues
	ruff check --fix .
	black --line-length=120 .
	isort --profile=black --line-length=120 .

test: ## Run tests with pytest
	pytest

test-watch: ## Run tests in watch mode
	pytest --watch

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -delete
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

setup: ## Set up pre-commit hooks
	pre-commit install

check-all: ## Run all checks (lint, format, type-check)
	ruff check .
	black --check --line-length=120 .
	isort --check-only --profile=black --line-length=120 .
	mypy .
