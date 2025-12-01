# Style and Conventions
- Follow PEP 484 type hints where practical; modules rely on pydantic models and FastAPI typing.
- Formatting, linting, and type checking are enforced by `ruff` (py312 target, E,F,I rules, ignore E501) and `mypy`. Run `just check` before commits.
- Tests use `pytest` with asyncio auto mode; fixtures configured via layered `conftest.py` files.
- Keep dependency container registrations explicit; prefer constructor injection patterns used across the codebase.