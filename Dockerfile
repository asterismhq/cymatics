# syntax=docker/dockerfile:1.7-labs
# ==============================================================================
# Multi-stage Dockerfile for FastAPI application
# ==============================================================================

# ==============================================================================
# Stage: base
# - Python base image with uv and dependency files
# ==============================================================================
FROM python:3.12-slim AS base

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./


# ==============================================================================
# Stage: dev-deps
# - All dependencies including development packages
# ==============================================================================
FROM base AS dev-deps

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache uv sync


# ==============================================================================
# Stage: prod-deps
# - Production dependencies only
# ==============================================================================
FROM base AS prod-deps

RUN --mount=type=cache,target=/root/.cache uv sync --no-dev


# ==============================================================================
# Stage: runtime-base
# - Common runtime setup for development and production
# ==============================================================================
FROM python:3.12-slim AS runtime-base

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/appuser -m appuser

WORKDIR /app
RUN chown appuser:appgroup /app

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/src"
EXPOSE 8000


# ==============================================================================
# Stage: development
# - Development environment with all tools and dependencies
# ==============================================================================
FROM runtime-base AS development

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=dev-deps /app/.venv ./.venv
COPY --chown=appuser:appgroup src/ ./src
COPY --chown=appuser:appgroup dev/ ./dev
COPY --chown=appuser:appgroup pyproject.toml entrypoint.sh ./

RUN chmod +x entrypoint.sh

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/health').getcode() == 200 else sys.exit(1)"

ENTRYPOINT ["/app/entrypoint.sh"]


# ==============================================================================
# Stage: production
# - Minimal production image
# ==============================================================================
FROM runtime-base AS production

COPY --from=prod-deps /app/.venv ./.venv
COPY --chown=appuser:appgroup src/ ./src
COPY --chown=appuser:appgroup pyproject.toml entrypoint.sh ./

RUN chmod +x entrypoint.sh

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/health').getcode() == 200 else sys.exit(1)"

ENTRYPOINT ["/app/entrypoint.sh"]