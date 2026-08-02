.PHONY: help install start moo server test lint lint-fix format check-all clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	npm install

start: ## Start the web server
	npm start

moo: ## Start the interactive shell
	node bin/moo.js

server: ## Start the telnet server
	node bin/moo.js -s

test: ## Run tests
	npm test

lint: ## Run Biome linter
	npx biome check .

lint-fix: ## Run Biome linter with auto-fix
	npx biome check --write .

format: ## Format code with Biome
	npx biome format --write .

check-all: ## Run all checks (lint, tests)
	npx biome check .
	npm test

clean: ## Clean up generated files
	rm -rf node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} +
