"""Shared pytest fixtures for the cymatics project."""

import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from cymatics.api.dependencies import reset_services
from cymatics.api.main import app as fastapi_app


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment with dotenv loading."""
    try:
        import dotenv

        dotenv.load_dotenv()
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def reset_app_state():
    """Reset application state before each test."""
    reset_services()
    yield
    reset_services()


@pytest.fixture()
def app() -> FastAPI:
    """Return the FastAPI application under test."""
    return fastapi_app


@pytest.fixture()
async def async_client(app: FastAPI) -> AsyncClient:
    """Provide an async HTTP client for exercising the API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture()
def temp_data_dir():
    """Create a temporary data directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        (data_dir / "incoming").mkdir()
        (data_dir / "processing").mkdir()
        (data_dir / "completed").mkdir()
        (data_dir / "failed").mkdir()
        yield data_dir


@pytest.fixture()
def sample_audio_path(temp_data_dir: Path) -> Path:
    """Create a minimal sample audio file for testing."""
    # Create a minimal valid MP3-like file (just header bytes for testing)
    # In real tests, you might use a proper test audio file
    audio_path = temp_data_dir / "incoming" / "test_audio.mp3"
    # Write some bytes to simulate a file
    audio_path.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 1000)
    return audio_path
