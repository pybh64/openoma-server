.PHONY: help run dev test test-v lint fmt db-up db-down db-logs ui-dev ui-build ui-codegen \
        stack-up stack-down stack-restart stack-logs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Start the server
	uv run python main.py

dev: ## Start with auto-reload
	OPENOMA_DEBUG=true uv run python main.py

test: ## Run all tests
	uv run pytest

test-v: ## Run tests with verbose output
	uv run pytest -v

lint: ## Run ruff linter
	uv run ruff check src/ tests/

fmt: ## Auto-format code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

db-up: ## Start MongoDB via Podman
	podman-compose -f podman/compose.yml up -d

db-down: ## Stop MongoDB
	podman-compose -f podman/compose.yml down

db-logs: ## Show MongoDB logs
	podman-compose -f podman/compose.yml logs -f

ui-dev: ## Start UI dev server
	cd ui && npm run dev

ui-build: ## Build UI for production
	cd ui && npm run build

ui-codegen: ## Regenerate GraphQL types from server schema
	cd ui && npx graphql-codegen

stack-up: ## Build images and start full stack — UI on http://localhost:8080, API at /api/
	podman-compose -f podman/compose.full.yml up -d --build

stack-down: ## Stop and remove the full stack containers
	podman-compose -f podman/compose.full.yml down

stack-restart: ## Restart all full stack containers
	podman-compose -f podman/compose.full.yml restart

stack-logs: ## Stream logs from the full stack
	podman-compose -f podman/compose.full.yml logs -f
