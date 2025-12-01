"""Integration tests for cymatics component interactions."""

import io
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient

from cymatics.api.dependencies import reset_services


@pytest.fixture(autouse=True)
def clear_services():
    """Clear services before and after each test."""
    reset_services()
    yield
    reset_services()


class TestTranscribeIntegration:
    """Integration tests for transcription flow."""

    @pytest.mark.asyncio
    async def test_transcribe_endpoint_accepts_file(
        self, monkeypatch, async_client: AsyncClient
    ):
        """Test that the transcribe endpoint accepts file uploads."""
        # Use mock transmutation to avoid loading real Whisper
        monkeypatch.setenv("CYMATICS_USE_MOCK_TRANSMUTATION", "true")

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("DATA_DIR", tmpdir)
            Path(tmpdir, "incoming").mkdir()
            Path(tmpdir, "processing").mkdir()
            Path(tmpdir, "completed").mkdir()
            Path(tmpdir, "failed").mkdir()

            reset_services()

            # Create a fake audio file
            audio_content = b"\xff\xfb\x90\x00" + b"\x00" * 1000
            files = {
                "file": ("test_audio.mp3", io.BytesIO(audio_content), "audio/mpeg")
            }

            response = await async_client.post("/v1/transcribe", files=files)

            assert response.status_code == 202
            data = response.json()
            assert "id" in data
            assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_transcribe_endpoint_rejects_unsupported_format(
        self, monkeypatch, async_client: AsyncClient
    ):
        """Test that unsupported file formats are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("DATA_DIR", tmpdir)
            Path(tmpdir, "incoming").mkdir()

            reset_services()

            # Create a fake file with unsupported extension
            files = {
                "file": ("document.pdf", io.BytesIO(b"pdf content"), "application/pdf")
            }

            response = await async_client.post("/v1/transcribe", files=files)

            assert response.status_code == 400
            assert "Unsupported file type" in response.json()["detail"]


class TestCycleStatusIntegration:
    """Integration tests for cycle status endpoint."""

    @pytest.mark.asyncio
    async def test_cycle_status_returns_queue_info(
        self, monkeypatch, async_client: AsyncClient
    ):
        """Test that cycle status returns queue information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("DATA_DIR", tmpdir)
            monkeypatch.setenv("CYMATICS_USE_MOCK_TRANSMUTATION", "true")
            Path(tmpdir, "incoming").mkdir()
            Path(tmpdir, "processing").mkdir()
            Path(tmpdir, "completed").mkdir()
            Path(tmpdir, "failed").mkdir()

            reset_services()

            response = await async_client.get("/v1/cycle/status")

            assert response.status_code == 200
            data = response.json()
            assert "queue_length" in data
            assert "model_state" in data
            assert "recent_completed" in data

    @pytest.mark.asyncio
    async def test_health_check_integration(self, async_client: AsyncClient):
        """Test that the health check endpoint integrates properly with the application."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
