"""Protocol for the transmutation (transcription) service."""

from pathlib import Path
from typing import Protocol

from cymatics.models import ModelState, TranscriptionResult


class TransmutationServiceProtocol(Protocol):
    """Interface for audio-to-text transcription service."""

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio or video file.

        Returns:
            TranscriptionResult containing the transcribed text and metadata.
        """
        ...

    def get_state(self) -> ModelState:
        """Get the current state of the model."""
        ...

    async def unload_model(self) -> None:
        """Unload the model from memory to free resources."""
        ...
