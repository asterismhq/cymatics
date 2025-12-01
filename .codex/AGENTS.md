# fapi-tmpl Agent Notes

## Overview
- Minimal FastAPI template intended as a clean starting point for new services.
- Ships only the essentials: modern dependency injection using FastAPI's `Depends`, protocols for interfaces, factory pattern for services, health and greeting routes, and test/CI/Docker wiring.

## Design Philosophy
- Stay database-agnostic; add persistence only when the target project needs it.
- Use FastAPI-native dependency injection (`Depends`) with protocols for service interfaces and factory pattern for implementations to maximize extensibility, maintainability, and testability.
- Keep settings and dependencies explicit via `AppSettings` and dependency providers.
- Maintain parity between local, Docker, and CI flows with a single source of truth (`just`, `uv`, `.env`).

## First Steps When Creating a Real API
1. Clone or copy the template and run `just setup` to install dependencies.
2. Rename the Python package from `fapi_tmpl` if you need a project-specific namespace.
3. Extend `src/fapi_tmpl/api/router.py` with domain routes and register required dependencies in `dependencies.py`.
4. Update `.env.example` and documentation to reflect new environment variables or external services.

## Key Files
- `src/fapi_tmpl/dependencies.py`: central place to wire settings and service providers.
- `src/fapi_tmpl/api/main.py`: FastAPI app instantiation; attach new routers here.
- `src/fapi_tmpl/protocols/`: protocol definitions for service interfaces.
- `src/fapi_tmpl/services/`: concrete service implementations.
- `tests/`: unit/intg/e2e layout kept light so additional checks can drop in without restructuring.

## Tooling Snapshot
- `justfile`: run/lint/test/build tasks used locally and in CI.
- `uv.lock` + `pyproject.toml`: reproducible dependency graph; regenerate with `uv pip compile` when deps change.
