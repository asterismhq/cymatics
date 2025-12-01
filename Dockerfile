# syntax=docker/dockerfile:1.7-labs
# ==============================================================================
# Dockerfile for cymatics - Audio/Video Transcription Service
# Optimized for ARM64 (Apple Silicon) with CPU-only PyTorch
# ==============================================================================

# ==============================================================================
# Stage: base
# - Python base image with system dependencies and uv
# ==============================================================================
FROM --platform=linux/arm64 python:3.12-slim AS base

WORKDIR /app

# System dependencies: ffmpeg for audio processing, git for whisper install
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./


# ==============================================================================
# Stage: dev-deps
# - All dependencies including development packages
# ==============================================================================
FROM base AS dev-deps

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# For ARM64, PyTorch CPU wheels are installed directly without CUDA
# Set link mode to copy to avoid hardlink issues in Docker
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache \
    uv pip install --system torch torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    uv sync


# ==============================================================================
# Stage: prod-deps
# - Production dependencies only
# ==============================================================================
FROM base AS prod-deps

# For ARM64, PyTorch CPU wheels are installed directly without CUDA
ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache \
    uv pip install --system torch torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    uv sync --no-dev


# ==============================================================================
# Stage: runtime-base
# - Common runtime setup for development and production
# ==============================================================================
FROM --platform=linux/arm64 python:3.12-slim AS runtime-base

# System dependencies needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/appuser -m appuser

WORKDIR /app
RUN chown appuser:appgroup /app

# Create data directories
RUN mkdir -p /app/data/incoming /app/data/processing /app/data/completed /app/data/failed /app/cache && \
    chown -R appuser:appgroup /app/data /app/cache

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/src"

# CPU optimization for PyTorch
ENV OMP_NUM_THREADS=4
ENV MKL_NUM_THREADS=4
ENV XDG_CACHE_HOME=/app/cache
ENV DATA_DIR=/app/data

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