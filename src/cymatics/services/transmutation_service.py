"""Transmutation service for audio-to-text conversion using Whisper."""

import asyncio
import gc
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

from cymatics.models import (
    ModelState,
    TranscriptionMeta,
    TranscriptionResult,
    TranscriptionSegment,
)
from cymatics.protocols import TransmutationServiceProtocol

logger = logging.getLogger(__name__)


class TransmutationService(TransmutationServiceProtocol):
    """Whisper-based transcription service with lazy loading and auto-unload."""

    # Supported file extensions
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aac"}
    VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov"}

    def __init__(
        self,
        model_name: str = "medium",
        unload_timeout: int = 300,
    ) -> None:
        """
        Initialize the transmutation service.

        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large).
            unload_timeout: Seconds of idle time before unloading the model.
        """
        self._model_name = model_name
        self._unload_timeout = unload_timeout
        self._model: Optional[Any] = None
        self._state = ModelState.UNLOADED
        self._last_used_at: Optional[float] = None
        self._lock = asyncio.Semaphore(1)  # Single concurrency
        self._unload_task: Optional[asyncio.Task[None]] = None

    def get_state(self) -> ModelState:
        """Get the current state of the model."""
        return self._state

    async def _load_model(self) -> None:
        """Load the Whisper model into memory."""
        if self._state != ModelState.UNLOADED:
            return

        self._state = ModelState.LOADING
        logger.info(f"Loading Whisper model: {self._model_name}")

        try:
            # Import whisper here to avoid loading at startup
            import whisper

            # Run model loading in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None,
                lambda: whisper.load_model(self._model_name, device="cpu"),
            )
            self._state = ModelState.READY
            logger.info(f"Whisper model {self._model_name} loaded successfully")
        except Exception as e:
            self._state = ModelState.UNLOADED
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    async def unload_model(self) -> None:
        """Unload the model from memory to free resources."""
        if self._state == ModelState.UNLOADED:
            return

        logger.info("Unloading Whisper model to free memory")
        self._model = None
        self._state = ModelState.UNLOADED
        gc.collect()
        logger.info("Whisper model unloaded")

    async def _schedule_unload(self) -> None:
        """Schedule model unload after idle timeout."""
        if self._unload_task is not None:
            self._unload_task.cancel()
            try:
                await self._unload_task
            except asyncio.CancelledError:
                pass

        async def _unload_after_timeout() -> None:
            await asyncio.sleep(self._unload_timeout)
            if self._last_used_at is not None:
                elapsed = time.time() - self._last_used_at
                if elapsed >= self._unload_timeout:
                    await self.unload_model()

        self._unload_task = asyncio.create_task(_unload_after_timeout())

    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        """
        Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio or video file.

        Returns:
            TranscriptionResult containing the transcribed text and metadata.
        """
        async with self._lock:
            # Ensure model is loaded
            if self._state == ModelState.UNLOADED:
                await self._load_model()

            logger.info(f"Starting transcription: {audio_path.name}")
            start_time = time.time()

            try:
                # Import whisper for transcription
                import whisper

                # Run transcription in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: whisper.transcribe(
                        self._model,
                        str(audio_path),
                        fp16=False,  # CPU mode
                        verbose=False,
                    ),
                )

                duration = time.time() - start_time
                self._last_used_at = time.time()

                # Schedule unload after timeout
                await self._schedule_unload()

                # Generate file hash for ID
                file_hash = self._compute_file_hash(audio_path)

                # Build transcription result
                transcription = self._build_result(
                    file_hash=file_hash,
                    whisper_result=result,
                    duration=duration,
                )

                logger.info(
                    f"Transcription completed: {audio_path.name} "
                    f"({duration:.2f}s, {len(result.get('segments', []))} segments)"
                )

                return transcription

            except Exception as e:
                logger.error(f"Transcription failed for {audio_path.name}: {e}")
                raise

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]

    def _build_result(
        self,
        file_hash: str,
        whisper_result: dict[str, Any],
        duration: float,
    ) -> TranscriptionResult:
        """Build a TranscriptionResult from Whisper output."""
        segments = []
        for seg in whisper_result.get("segments", []):
            segments.append(
                TranscriptionSegment(
                    id=seg.get("id", 0),
                    start=seg.get("start", 0.0),
                    end=seg.get("end", 0.0),
                    text=seg.get("text", ""),
                    tokens=seg.get("tokens", []),
                    temperature=seg.get("temperature", 0.0),
                    avg_logprob=seg.get("avg_logprob", 0.0),
                    compression_ratio=seg.get("compression_ratio", 0.0),
                    no_speech_prob=seg.get("no_speech_prob", 0.0),
                )
            )

        meta = TranscriptionMeta(
            model=self._model_name,
            device="cpu",
            compute_type="float32",
            duration=duration,
            language=whisper_result.get("language", "ja"),
        )

        return TranscriptionResult(
            id=file_hash,
            meta=meta,
            text=whisper_result.get("text", ""),
            segments=segments,
        )

    @staticmethod
    def save_artifacts(
        result: TranscriptionResult, output_dir: Path, stem: str
    ) -> None:
        """
        Save transcription artifacts (JSON and TXT) to output directory.

        Args:
            result: The transcription result.
            output_dir: Directory to save files.
            stem: Base filename without extension.
        """
        # Save JSON metadata
        json_path = output_dir / f"{stem}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

        # Save plain text
        txt_path = output_dir / f"{stem}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(result.text)


# Type check
_: TransmutationServiceProtocol = TransmutationService()
