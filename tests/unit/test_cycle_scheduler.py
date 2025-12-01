"""Unit tests for the cycle scheduler service."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from cymatics.models import ModelState
from cymatics.services.cycle_scheduler import CycleSchedulerService
from dev.mocks.services.mock_transmutation_service import MockTransmutationService


class TestCycleSchedulerService:
    """Unit tests for the cycle scheduler service."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "incoming").mkdir()
            (data_dir / "processing").mkdir()
            (data_dir / "completed").mkdir()
            (data_dir / "failed").mkdir()
            yield data_dir

    @pytest.fixture
    def mock_transmutation(self) -> MockTransmutationService:
        """Create a mock transmutation service."""
        return MockTransmutationService()

    @pytest.fixture
    def scheduler(
        self, temp_dir: Path, mock_transmutation: MockTransmutationService
    ) -> CycleSchedulerService:
        """Create a cycle scheduler service."""
        return CycleSchedulerService(
            data_dir=temp_dir,
            transmutation_service=mock_transmutation,
            poll_interval=0.1,
            debounce_seconds=0.1,
        )

    def test_initial_queue_status(self, scheduler: CycleSchedulerService):
        """Test initial queue status is empty."""
        status = scheduler.get_queue_status()
        assert status.queue_length == 0
        assert status.current_file is None
        assert status.model_state == ModelState.UNLOADED

    def test_discover_files_finds_audio_files(
        self, scheduler: CycleSchedulerService, temp_dir: Path
    ):
        """Test that discover_files finds audio files."""
        # Create test files
        (temp_dir / "incoming" / "test1.mp3").write_bytes(b"audio data")
        (temp_dir / "incoming" / "test2.wav").write_bytes(b"audio data")
        (temp_dir / "incoming" / "readme.txt").write_text("not audio")

        files = scheduler._discover_files()

        assert len(files) == 2
        filenames = [f.name for f in files]
        assert "test1.mp3" in filenames
        assert "test2.wav" in filenames
        assert "readme.txt" not in filenames

    def test_discover_files_ignores_zero_byte_files(
        self, scheduler: CycleSchedulerService, temp_dir: Path
    ):
        """Test that zero-byte files are ignored."""
        (temp_dir / "incoming" / "empty.mp3").write_bytes(b"")
        (temp_dir / "incoming" / "valid.mp3").write_bytes(b"audio data")

        files = scheduler._discover_files()

        assert len(files) == 1
        assert files[0].name == "valid.mp3"

    def test_move_file_to_processing(
        self, scheduler: CycleSchedulerService, temp_dir: Path
    ):
        """Test moving file to processing directory."""
        src_path = temp_dir / "incoming" / "test.mp3"
        src_path.write_bytes(b"audio data")

        dest_path = scheduler._move_file(src_path, temp_dir / "processing")

        assert dest_path.exists()
        assert not src_path.exists()
        assert dest_path.parent == temp_dir / "processing"

    def test_recovery_moves_orphaned_files(
        self, temp_dir: Path, mock_transmutation: MockTransmutationService
    ):
        """Test that startup recovery moves orphaned files from processing."""
        # Create orphaned file in processing
        (temp_dir / "processing" / "orphan.mp3").write_bytes(b"orphaned audio")

        # Create scheduler - recovery should happen during init
        CycleSchedulerService(
            data_dir=temp_dir,
            transmutation_service=mock_transmutation,
            poll_interval=0.1,
            debounce_seconds=0.1,
        )

        # File should be moved to incoming
        assert not (temp_dir / "processing" / "orphan.mp3").exists()
        assert (temp_dir / "incoming" / "orphan.mp3").exists()

    @pytest.mark.asyncio
    async def test_start_and_stop(self, scheduler: CycleSchedulerService):
        """Test starting and stopping the scheduler."""
        await scheduler.start()
        assert scheduler._running is True

        await scheduler.stop()
        assert scheduler._running is False

    def test_is_file_stable(self, scheduler: CycleSchedulerService, temp_dir: Path):
        """Test file stability check."""
        file_path = temp_dir / "incoming" / "test.mp3"
        file_path.write_bytes(b"audio data")

        # Update mtime to be in the past to simulate stable file
        old_time = time.time() - 1.0  # 1 second ago
        os.utime(file_path, (old_time, old_time))

        # First check marks the file for tracking (returns False)
        assert scheduler._is_file_stable(file_path) is False

        # Second check with same size and old mtime should return True
        assert scheduler._is_file_stable(file_path) is True
