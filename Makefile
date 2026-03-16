.PHONY: setup install lint lint-fix format typecheck pre-commit test test-unit test-integration clean

# ============================================================================
# Setup
# ============================================================================

setup: install hooks ## Full setup: install deps + git hooks
	@echo "Setup complete."

install: ## Install all dependencies
	uv sync

hooks: ## Install pre-commit hooks
	uv run pre-commit install

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run ruff linter
	uv run ruff check src/ tests/

lint-fix: ## Run ruff linter with auto-fix
	uv run ruff check --fix src/ tests/

format: ## Run ruff formatter + linter fix
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

typecheck: ## Run mypy type checking
	uv run mypy src/

pre-commit: ## Run all pre-commit hooks on all files
	uv run pre-commit run --all-files

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	uv run pytest tests/ -v

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	uv run pytest tests/integration/ -v -m integration

# ============================================================================
# CLI Shortcuts
# ============================================================================

attendees: ## List attendees (usage: make attendees event=startsummitxhack2026)
	uv run brella attendees list --event $(event)

campaign-dry: ## Dry-run campaign (usage: make campaign-dry event=startsummitxhack2026)
	uv run brella campaign run --event $(event) --dry-run

campaign-send: ## Send campaign (usage: make campaign-send event=startsummitxhack2026)
	uv run brella campaign run --event $(event) --no-dry-run

sync: ## Sync attendees + interests (usage: make sync event=startsummitxhack2026)
	uv run brella sync attendees --event $(event)
	uv run brella sync interests --event $(event)

# ============================================================================
# Database
# ============================================================================

db-reset: ## Delete local SQLite database
	rm -f brella_outbound.db
	@echo "Database reset."

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
