"""Mock transmutation service for testing."""

from pathlib import Path

from cymatics.models import (
    ModelState,
    TranscriptionMeta,
    TranscriptionResult,
    TranscriptionSegment,
)
from cymatics.protocols import TransmutationServiceProtocol


class MockTransmutationService(TransmutationServiceProtocol):
    """Mock implementation of the transmutation service for testing."""

    def __init__(self) -> None:
        self._state = ModelState.UNLOADED

    def get_state(self) -> ModelState:
        """Get the current state of the model."""
        return self._state

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """Return a mock transcription result."""
        self._state = ModelState.READY

        return TranscriptionResult(
            id="mock_id_12345678",
            meta=TranscriptionMeta(
                model="mock",
                device="cpu",
                compute_type="float32",
                duration=0.1,
                language="en",
            ),
            text=f"[mock] Transcription of {audio_path.name}",
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=0.0,
                    end=1.0,
                    text=f"[mock] Transcription of {audio_path.name}",
                )
            ],
        )

    async def unload_model(self) -> None:
        """Unload the mock model."""
        self._state = ModelState.UNLOADED


# Type check
_: TransmutationServiceProtocol = MockTransmutationService()
