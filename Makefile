.PHONY: help run dev test test-v lint fmt db-up db-down db-logs

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
	podman compose -f podman/compose.yml up -d

db-down: ## Stop MongoDB
	podman compose -f podman/compose.yml down

db-logs: ## Show MongoDB logs
	podman compose -f podman/compose.yml logs -f
