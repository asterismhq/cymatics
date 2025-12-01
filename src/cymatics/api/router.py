"""HTTP routes for cymatics transcription API."""

import uuid
from pathlib import Path

import aiofiles  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from cymatics.models import CycleStatusResponse, TranscribeResponse
from cymatics.protocols import CycleSchedulerProtocol

from .dependencies import get_app_settings, get_cycle_scheduler

router = APIRouter()

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


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a simple health status payload."""
    return {"status": "ok"}


@router.post(
    "/v1/transcribe",
    response_model=TranscribeResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def transcribe(
    file: UploadFile = File(...),
) -> TranscribeResponse:
    """
    Accept a file upload and queue it for transcription.

    Returns 202 Accepted with a job ID. The file will be processed asynchronously.
    """
    settings = get_app_settings()

    # Validate file extension
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    # Generate unique ID for the job
    job_id = str(uuid.uuid4())[:8]

    # Save file to incoming directory
    incoming_dir = settings.incoming_dir
    incoming_dir.mkdir(parents=True, exist_ok=True)

    # Use original filename with job_id prefix to avoid collisions
    dest_filename = f"{job_id}_{file.filename}"
    dest_path = incoming_dir / dest_filename

    try:
        async with aiofiles.open(dest_path, "wb") as f:
            while chunk := await file.read(8192):
                await f.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    return TranscribeResponse(id=job_id, status="queued")


@router.get("/v1/cycle/status", response_model=CycleStatusResponse)
async def get_cycle_status(
    scheduler: CycleSchedulerProtocol = Depends(get_cycle_scheduler),
) -> CycleStatusResponse:
    """Get the current status of the transcription queue."""
    status = scheduler.get_queue_status()
    return CycleStatusResponse(
        queue_length=status.queue_length,
        current_file=status.current_file,
        model_state=status.model_state.value,
        recent_completed=status.recent_completed,
    )
