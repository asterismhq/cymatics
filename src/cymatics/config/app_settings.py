"""Application-level settings for cymatics."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Settings for the cymatics transcription service."""

    app_name: str = Field(
        default="cymatics",
        alias="CYMATICS_APP_NAME",
        description="Public-facing service name reported in responses and logs.",
    )

    # Data directory settings
    data_dir: Path = Field(
        default=Path("/app/data"),
        alias="DATA_DIR",
        description="Base directory for file processing (incoming/processing/completed/failed).",
    )

    # Whisper model settings
    whisper_model: str = Field(
        default="medium",
        alias="WHISPER_MODEL",
        description="Whisper model to use (tiny, base, small, medium, large).",
    )

    # Model lifecycle settings
    model_unload_timeout: int = Field(
        default=300,
        alias="MODEL_UNLOAD_TIMEOUT",
        description="Seconds of idle time before unloading the model from memory.",
    )

    # Cycle scheduler settings
    debounce_seconds: float = Field(
        default=2.0,
        alias="DEBOUNCE_SECONDS",
        description="Seconds to wait for file write completion before processing.",
    )
    cycle_poll_interval: float = Field(
        default=5.0,
        alias="CYCLE_POLL_INTERVAL",
        description="Seconds between directory polling cycles.",
    )

    # Development/testing settings
    use_mock_transmutation: bool = Field(
        default=False,
        alias="CYMATICS_USE_MOCK_TRANSMUTATION",
        description="Toggle to inject the mock transmutation service for local dev and tests.",
    )

    @property
    def incoming_dir(self) -> Path:
        """Directory for files awaiting processing."""
        return self.data_dir / "incoming"

    @property
    def processing_dir(self) -> Path:
        """Directory for files currently being processed."""
        return self.data_dir / "processing"

    @property
    def completed_dir(self) -> Path:
        """Directory for successfully processed files."""
        return self.data_dir / "completed"

    @property
    def failed_dir(self) -> Path:
        """Directory for files that failed processing."""
        return self.data_dir / "failed"


settings = AppSettings()
