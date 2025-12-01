"""Unit tests for the transmutation service."""

import tempfile
from pathlib import Path

import pytest

from cymatics.models import ModelState
from dev.mocks.services.mock_transmutation_service import MockTransmutationService


class TestMockTransmutationService:
    """Unit tests for the mock transmutation service."""

    @pytest.fixture
    def service(self) -> MockTransmutationService:
        """Create a mock transmutation service."""
        return MockTransmutationService()

    def test_initial_state_is_unloaded(self, service: MockTransmutationService):
        """Test that the service starts in UNLOADED state."""
        assert service.get_state() == ModelState.UNLOADED

    @pytest.mark.asyncio
    async def test_transcribe_changes_state_to_ready(
        self, service: MockTransmutationService
    ):
        """Test that transcription changes state to READY."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio content")
            audio_path = Path(f.name)

        result = await service.transcribe(audio_path)

        assert service.get_state() == ModelState.READY
        assert result.id == "mock_id_12345678"
        assert "[mock]" in result.text
        audio_path.unlink()

    @pytest.mark.asyncio
    async def test_unload_model_changes_state(self, service: MockTransmutationService):
        """Test that unload_model changes state back to UNLOADED."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio content")
            audio_path = Path(f.name)

        await service.transcribe(audio_path)
        assert service.get_state() == ModelState.READY

        await service.unload_model()
        assert service.get_state() == ModelState.UNLOADED

        audio_path.unlink()

    @pytest.mark.asyncio
    async def test_transcription_result_structure(
        self, service: MockTransmutationService
    ):
        """Test the structure of transcription result."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio content")
            audio_path = Path(f.name)

        result = await service.transcribe(audio_path)

        assert result.meta.model == "mock"
        assert result.meta.device == "cpu"
        assert result.meta.compute_type == "float32"
        assert len(result.segments) == 1
        assert result.segments[0].start == 0.0
        assert result.segments[0].end == 1.0

        audio_path.unlink()
