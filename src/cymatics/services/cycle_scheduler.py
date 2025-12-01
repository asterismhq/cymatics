"""Cycle scheduler service for directory monitoring and task queuing."""

import asyncio
import logging
import shutil
from collections import deque
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from cymatics.models import ModelState, QueueStatus
from cymatics.protocols import CycleSchedulerProtocol, TransmutationServiceProtocol
from cymatics.services.transmutation_service import TransmutationService

logger = logging.getLogger(__name__)


class CycleSchedulerService(CycleSchedulerProtocol):
    """Directory watcher and task scheduler for audio transcription."""

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".m4a",
        ".flac",
        ".aac",  # Audio
        ".mp4",
        ".mkv",
        ".mov",  # Video
    }

    def __init__(
        self,
        data_dir: Path,
        transmutation_service: TransmutationServiceProtocol,
        poll_interval: float = 5.0,
        debounce_seconds: float = 2.0,
    ) -> None:
        """
        Initialize the cycle scheduler.

        Args:
            data_dir: Base directory containing incoming/processing/completed/failed.
            transmutation_service: Service for transcription.
            poll_interval: Seconds between directory polling.
            debounce_seconds: Seconds to wait for file write completion.
        """
        self._data_dir = data_dir
        self._transmutation_service = transmutation_service
        self._poll_interval = poll_interval
        self._debounce_seconds = debounce_seconds

        # Directory paths
        self._incoming_dir = data_dir / "incoming"
        self._processing_dir = data_dir / "processing"
        self._completed_dir = data_dir / "completed"
        self._failed_dir = data_dir / "failed"

        # State tracking
        self._current_file: Optional[str] = None
        self._recent_completed: deque[str] = deque(maxlen=10)
        self._file_sizes: dict[str, int] = {}  # For debouncing
        self._running: bool = False

        # Scheduler
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._processing_lock = asyncio.Lock()

        # Run recovery on init
        self._ensure_directories()
        self._recover_orphaned_files()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for dir_path in [
            self._incoming_dir,
            self._processing_dir,
            self._completed_dir,
            self._failed_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _recover_orphaned_files(self) -> None:
        """Move orphaned files from processing back to incoming on startup."""
        if not self._processing_dir.exists():
            return

        orphaned = list(self._processing_dir.iterdir())
        if orphaned:
            logger.warning(
                f"Found {len(orphaned)} orphaned files in processing directory, "
                "rolling back to incoming"
            )
            for file_path in orphaned:
                if file_path.is_file():
                    dest = self._incoming_dir / file_path.name
                    shutil.move(str(file_path), str(dest))
                    logger.info(f"Recovered orphaned file: {file_path.name}")

    async def start(self) -> None:
        """Start the scheduler and begin monitoring directories."""
        logger.info("Starting cycle scheduler")

        # Ensure directories exist
        self._ensure_directories()

        # Recover any orphaned files from previous run
        self._recover_orphaned_files()

        # Create and start scheduler
        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._poll_cycle,
            "interval",
            seconds=self._poll_interval,
            id="poll_cycle",
        )
        self._scheduler.start()
        self._running = True
        logger.info(f"Cycle scheduler started (poll interval: {self._poll_interval}s)")

    async def stop(self) -> None:
        """Stop the scheduler and cleanup."""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
        self._running = False
        logger.info("Cycle scheduler stopped")

    def get_queue_status(self) -> QueueStatus:
        """Get the current status of the processing queue."""
        # Count files in incoming directory
        queue_length = 0
        if self._incoming_dir.exists():
            queue_length = sum(
                1
                for f in self._incoming_dir.iterdir()
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
            )

        # Get model state
        if isinstance(self._transmutation_service, TransmutationService):
            model_state = self._transmutation_service.get_state()
        else:
            model_state = ModelState.UNLOADED

        return QueueStatus(
            queue_length=queue_length,
            current_file=self._current_file,
            model_state=model_state,
            recent_completed=list(self._recent_completed),
        )

    async def _poll_cycle(self) -> None:
        """Poll for new files and process them."""
        # Skip if already processing
        if self._processing_lock.locked():
            return

        async with self._processing_lock:
            await self._process_incoming_files()

    async def _process_incoming_files(self) -> None:
        """Process all files in the incoming directory."""
        if not self._incoming_dir.exists():
            return

        # Get list of supported files
        files = self._discover_files()

        for file_path in files:
            # Check if file is stable (debouncing)
            if not self._is_file_stable(file_path):
                logger.debug(f"File not stable yet: {file_path.name}")
                continue

            # Validate file
            if not self._is_valid_file(file_path):
                logger.warning(f"Invalid file, moving to failed: {file_path.name}")
                await self._move_to_failed(
                    file_path, "Invalid file (zero bytes or unreadable)"
                )
                continue

            # Process the file
            await self._process_file(file_path)

    def _discover_files(self) -> list[Path]:
        """Discover supported files in the incoming directory."""
        if not self._incoming_dir.exists():
            return []

        return sorted(
            f
            for f in self._incoming_dir.iterdir()
            if f.is_file()
            and f.suffix.lower() in self.SUPPORTED_EXTENSIONS
            and f.stat().st_size > 0  # Skip zero-byte files
        )

    def _move_file(self, src: Path, dest_dir: Path) -> Path:
        """Move a file to a destination directory."""
        dest_path = dest_dir / src.name
        shutil.move(str(src), str(dest_path))
        return dest_path

    def _is_file_stable(self, file_path: Path) -> bool:
        """Check if file size is stable (write complete)."""
        try:
            current_size = file_path.stat().st_size
            key = str(file_path)
            mtime = file_path.stat().st_mtime

            # Check if file was modified recently
            import time

            if time.time() - mtime < self._debounce_seconds:
                return False

            if key not in self._file_sizes:
                self._file_sizes[key] = current_size
                return False

            if self._file_sizes[key] != current_size:
                self._file_sizes[key] = current_size
                return False

            # Clean up tracking
            del self._file_sizes[key]
            return True

        except OSError:
            return False

    def _is_valid_file(self, file_path: Path) -> bool:
        """Check if file is valid (non-zero size)."""
        try:
            return file_path.stat().st_size > 0
        except OSError:
            return False

    async def _process_file(self, file_path: Path) -> None:
        """Process a single file."""
        filename = file_path.name
        self._current_file = filename
        logger.info(f"Processing file: {filename}")

        # Move to processing directory
        processing_path = self._processing_dir / filename
        try:
            shutil.move(str(file_path), str(processing_path))
        except Exception as e:
            logger.error(f"Failed to move file to processing: {e}")
            self._current_file = None
            return

        try:
            # Run transcription
            result = await self._transmutation_service.transcribe(processing_path)

            # Save artifacts to completed directory
            stem = processing_path.stem
            TransmutationService.save_artifacts(result, self._completed_dir, stem)

            # Move original file to completed
            completed_path = self._completed_dir / filename
            shutil.move(str(processing_path), str(completed_path))

            # Track completion
            self._recent_completed.append(filename)
            logger.info(f"Successfully processed: {filename}")

        except Exception as e:
            logger.error(f"Transcription failed for {filename}: {e}")
            await self._move_to_failed(processing_path, str(e))

        finally:
            self._current_file = None

    async def _move_to_failed(self, file_path: Path, reason: str) -> None:
        """Move a file to the failed directory with error log."""
        try:
            failed_path = self._failed_dir / file_path.name
            if file_path.exists():
                shutil.move(str(file_path), str(failed_path))

            # Write error log
            error_log_path = self._failed_dir / f"{file_path.stem}.error.txt"
            with open(error_log_path, "w", encoding="utf-8") as f:
                f.write(f"File: {file_path.name}\nError: {reason}\n")

            logger.info(f"Moved to failed: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to move file to failed directory: {e}")


# Type check
_transmutation = TransmutationService()
_: CycleSchedulerProtocol = CycleSchedulerService(Path("/tmp"), _transmutation)
