# Yuzu — Project Makefile
# Quick commands for code quality, testing, and development

.PHONY: help install dev-install lint format type test test-cov all clean docker-up docker-down

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help message
	@echo "🍋 Yuzu — Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	poetry install --only main

dev-install:  ## Install all dependencies including dev tools
	poetry install --with dev

lint:  ## Run Ruff linter (check only)
	@echo "🔍 Running Ruff linter..."
	poetry run ruff check src tests

format:  ## Format code with Ruff
	@echo "✨ Formatting code with Ruff..."
	poetry run ruff format src tests
	poetry run ruff check --fix src tests

type:  ## Run mypy type checker
	@echo "🔎 Running mypy type checker..."
	poetry run mypy src tests

test:  ## Run pytest tests
	@echo "🧪 Running tests..."
	poetry run pytest

test-cov:  ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	poetry run pytest --cov=src/yuzu --cov-report=term-missing --cov-report=html

all: format lint type test  ## Run all quality checks (format, lint, type, test)
	@echo "✅ All checks passed!"

clean:  ## Clean build artifacts and caches
	@echo "🧹 Cleaning up..."
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docker-up:  ## Start Docker services (PostgreSQL + PostGIS)
	docker compose up -d

docker-down:  ## Stop Docker services
	docker compose down

docker-logs:  ## Show Docker logs
	docker compose logs -f

db-shell:  ## Connect to PostgreSQL shell
	docker compose exec postgres psql -U yuzu -d yuzu
