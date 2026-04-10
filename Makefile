.PHONY: help dev test lint fmt run sync clean ui-dev ui-build ui-install

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

sync: ## Install/sync all dependencies
	uv sync --all-groups

run: ## Run the server locally
	uv run uvicorn openoma_server.app:app --reload --host 0.0.0.0 --port 8000

dev: ## Start MongoDB + run server with hot-reload
	podman-compose up -d mongo
	@echo "Waiting for MongoDB..."
	@sleep 2
	uv run uvicorn openoma_server.app:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	uv run pytest -v

lint: ## Run ruff linter
	uv run ruff check src/ tests/

fmt: ## Format code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

up: ## Start all services via podman-compose
	podman-compose up -d

down: ## Stop all services
	podman-compose down

mongo: ## Start only MongoDB
	podman-compose up -d mongo

clean: ## Remove containers and volumes
	podman-compose down -v

ui-install: ## Install UI dependencies
	cd ui && npm install

ui-dev: ## Start UI dev server (Vite)
	cd ui && npm run dev

ui-build: ## Build UI for production
	cd ui && npm run build
