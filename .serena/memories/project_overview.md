# Project Overview
- Purpose: FastAPI-based API that orchestrates Ollama-hosted LLMs to perform autonomous web research and summarization.
- Tech Stack: Python 3.12+, FastAPI, LangChain/langgraph integrations, httpx, uvicorn; managed with uv (Poetry backend) and Docker.
- Structure: Application code lives in `src/olm_d_rch` with API setup under `api/`, DI container in `container.py`, plus supporting modules (`services`, `clients`, `graph`, `nodes`, `prompts`). Tests split into `tests/unit`, `tests/intg`, and `tests/e2e`. Demo scripts under `demo/`, Docker/CI assets at repo root.