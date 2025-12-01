"""FastAPI application entry point for cymatics."""

import logging
from contextlib import asynccontextmanager
from importlib import metadata
from typing import AsyncGenerator

from fastapi import FastAPI

from .dependencies import get_app_settings, get_cycle_scheduler
from .router import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_safe_version(package_name: str, fallback: str = "0.1.0") -> str:
    """
    Safely get the version of a package.

    Args:
        package_name: Name of the package
        fallback: Default version if retrieval fails

    Returns:
        Version string
    """
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return fallback


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle."""
    settings = get_app_settings()
    logger.info(f"Starting cymatics with data_dir={settings.data_dir}")

    # Ensure data directories exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.incoming_dir.mkdir(parents=True, exist_ok=True)
    settings.processing_dir.mkdir(parents=True, exist_ok=True)
    settings.completed_dir.mkdir(parents=True, exist_ok=True)
    settings.failed_dir.mkdir(parents=True, exist_ok=True)

    # Start the cycle scheduler
    scheduler = get_cycle_scheduler()
    await scheduler.start()
    logger.info("Cycle scheduler started")

    yield

    # Stop the cycle scheduler
    await scheduler.stop()
    logger.info("Cycle scheduler stopped")


app = FastAPI(
    title="cymatics",
    version=get_safe_version("cymatics"),
    description="Audio/video transcription service using OpenAI Whisper",
    lifespan=lifespan,
)
app.include_router(router)
