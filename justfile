# ==============================================================================
# justfile for fapi-tmpl automation
# ==============================================================================

set dotenv-load

APP_NAME := env("FAPI_TMPL_APP_NAME", "fapi-tmpl")
HOST_IP := env("FAPI_TMPL_BIND_IP", "127.0.0.1")
DEV_PORT := env("FAPI_TMPL_DEV_PORT", "8000")

# default target
default: help

# Show available recipes
help:
    @echo "Usage: just [recipe]"
    @echo "Available recipes:"
    @just --list | tail -n +2 | awk '{printf "  \033[36m%-20s\033[0m %s\n", $1, substr($0, index($0, $2))}'

# ==============================================================================
# Environment Setup
# ==============================================================================

# Initialize project: install dependencies and create the .env file
setup:
    @echo "🐍 Installing python dependencies with uv..."
    @uv sync
    @echo "Creating environment file..."
    @if [ ! -f .env ] && [ -f .env.example ]; then \
        echo "Creating .env from .env.example..."; \
        cp .env.example .env; \
        echo "✅ Environment file created (.env)"; \
    else \
        echo ".env already exists. Skipping creation."; \
    fi

# ==============================================================================
# Development Environment Commands
# ==============================================================================

# Run local development server
dev:
    @echo "Starting local development server..."
    @uv run uvicorn fapi_tmpl.api.main:app --reload --host {{HOST_IP}} --port {{DEV_PORT}}

# Start production-like environment with Docker Compose
up:
    @docker compose up -d

# Stop Docker Compose environment
down:
    @docker compose down --remove-orphans

# Build Docker image
build:
    @docker build --target production --tag {{APP_NAME}}:latest .

# ==============================================================================
# CODE QUALITY
# ==============================================================================

# Automatically format and fix code (Ruff)
fix:
    @echo "🔧 Formatting and fixing code..."
    @uv run ruff format .
    @uv run ruff check . --fix

# Run static checks (Ruff, Mypy)
check:
    @echo "🧐 Running static checks..."
    @uv run ruff format --check .
    @uv run ruff check .
    @uv run mypy .

# ==============================================================================
# TESTING
# ==============================================================================

# Run complete test suite
test:
    @just local-test
    @just docker-test
    @echo "✅ All tests passed!"

# Run lightweight local test suite
local-test:
    @just unit-test
    @just intg-test
    @echo "✅ All local tests passed!"

# Run unit tests
unit-test:
    @echo "🚀 Running unit tests..."
    @uv run pytest tests/unit

# Run integration tests
intg-test:
    @echo "🚀 Running integration tests..."
    @uv run pytest tests/intg

# Run all Docker-based tests
docker-test:
    @just build-test
    @just e2e-test
    @echo "✅ All Docker tests passed!"

# Build Docker image for testing without leaving artifacts
build-test:
    @echo "Building Docker image to verify build process..."
    docker build --no-cache --target production -t test-build:temp . || (echo "Docker build failed"; exit 1)
    @echo "✅ Docker build successful"
    @echo "Cleaning up test image..."
    -docker rmi test-build:temp 2>/dev/null || true

# Run e2e tests
e2e-test:
    @echo "🚀 Building temporary image for e2e tests..."
    @docker build --target development -t fapi-tmpl-e2e:latest .
    @echo "🚀 Running e2e tests..."
    @uv run pytest tests/e2e
    @echo "🧹 Cleaning up e2e test image..."
    -@docker rmi fapi-tmpl-e2e:latest 2>/dev/null || true

# ==============================================================================
# CLEANUP
# ==============================================================================

# Remove __pycache__ and .venv to make project lightweight
clean:
    @echo "🧹 Cleaning up project..."
    @find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @rm -rf .venv
    @rm -rf .pytest_cache
    @rm -rf .ruff_cache
    @rm -rf .aider.tags.cache.v4
    @rm -rf .serena/cache
    @rm -rf .uv-cache
    @rm -rf .tmp
    @echo "✅ Cleanup completed"