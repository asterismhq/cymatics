"""Data models for transcription results and metadata."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ModelState(str, Enum):
    """State of the Whisper model in memory."""

    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"


class TranscriptionSegment(BaseModel):
    """A single segment of transcribed text with timing information."""

    id: int
    start: float
    end: float
    text: str
    tokens: list[int] = Field(default_factory=list)
    temperature: float = 0.0
    avg_logprob: float = 0.0
    compression_ratio: float = 0.0
    no_speech_prob: float = 0.0


class TranscriptionMeta(BaseModel):
    """Metadata about the transcription process."""

    model: str
    device: str
    compute_type: str
    duration: float
    language: str = "ja"


class TranscriptionResult(BaseModel):
    """Complete transcription result with segments and metadata."""

    id: str
    meta: TranscriptionMeta
    text: str
    segments: list[TranscriptionSegment] = Field(default_factory=list)


class FileInfo(BaseModel):
    """Information about a file being processed."""

    id: UUID
    filename: str
    file_hash: str
    size: int
    created_at: datetime = Field(default_factory=datetime.now)


class QueueStatus(BaseModel):
    """Current status of the processing queue."""

    queue_length: int
    current_file: Optional[str] = None
    model_state: ModelState
    recent_completed: list[str] = Field(default_factory=list)


class TranscribeResponse(BaseModel):
    """Response from the transcribe endpoint."""

    id: str
    status: str = "queued"


class CycleStatusResponse(BaseModel):
    """Response from the cycle status endpoint."""

    queue_length: int
    current_file: Optional[str] = None
    model_state: str
    recent_completed: list[str] = Field(default_factory=list)
