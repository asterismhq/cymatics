# cymatics Agent Notes

## Overview
- Audio/video transcription service using OpenAI Whisper with CPU-optimized inference
- Designed for Mac ARM64 (Apple Silicon) deployment
- Single container monolith with filesystem-based state management
- Lazy loading model to minimize memory usage when idle

## Design Philosophy
- CPU-first strategy for stability on Apple Silicon (no MPS/GPU dependencies)
- FileSystem as database: State managed via host-mounted directories
- Fire-and-forget: Callers don't wait for processing completion
- Atomic operations: Each file gets a complete output or error

## Core Components

### TransmutationService
- Wraps OpenAI Whisper for audio-to-text conversion
- Model state machine: UNLOADED → LOADING → READY
- Auto-unloads after idle timeout (default 5 minutes)
- Uses `device="cpu"`, `fp16=False` for stability
- Single concurrency via asyncio Semaphore

### CycleSchedulerService
- APScheduler-based directory monitoring
- Polls `incoming/` directory for new files
- Debouncing: Waits for file write completion
- Crash recovery: Orphaned files in `processing/` are rolled back on startup
- File lifecycle: incoming → processing → completed/failed

### API Layer
- `POST /v1/transcribe`: Upload file, returns 202 with job ID
- `GET /v1/cycle/status`: Queue length, current task, model state
- `GET /health`: Health check

## Data Directory Structure
```
~/cymatics/
├── incoming/    # Drop files here
├── processing/  # System lock directory
├── completed/   # Output: original + .json + .txt
└── failed/      # Error logs
```

## Key Files
- `src/cymatics/services/transmutation_service.py`: Whisper integration
- `src/cymatics/services/cycle_scheduler.py`: Directory watcher
- `src/cymatics/api/router.py`: HTTP endpoints
- `src/cymatics/config/app_settings.py`: Environment configuration

## Tooling
- `just init`: Create `~/cymatics` directory structure
- `just setup`: Install dependencies with uv
- `just dev`: Run local development server
- `just test`: Run full test suite

## Supported Formats
- Audio: `.mp3`, `.wav`, `.m4a`, `.flac`, `.aac`
- Video: `.mp4`, `.mkv`, `.mov` (audio track extracted)
