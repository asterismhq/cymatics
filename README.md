# cymatics

`cymatics` is an audio/video transcription service using OpenAI Whisper with CPU-optimized inference for Apple Silicon (ARM64). It provides asynchronous file processing through directory monitoring, making it ideal for batch transcription workflows.

## 🎯 Features

- **Audio/Video Transcription:** Convert audio files (MP3, WAV, M4A, FLAC, AAC) and video files (MP4, MKV, MOV) to text
- **CPU-Optimized:** Runs on Apple Silicon without GPU dependencies
- **Lazy Loading:** Model only loads when needed, auto-unloads after idle period
- **Directory Monitoring:** Automatic processing of files placed in `~/cymatics/incoming`
- **REST API:** Upload files via HTTP for queued processing
- **Structured Output:** JSON metadata with timestamps + plain text files

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Docker and Docker Compose (for production deployment)
- Mac with Apple Silicon (M1/M2/M3) recommended

### Quick Start

1. **Initialize directories:**
```shell
just init
```
This creates the data directory structure at `~/cymatics/`.

2. **Install dependencies:**
```shell
just setup
```

3. **Run the application:**
```shell
just dev
```

The service will be available at `http://127.0.0.1:8000/health`.

### Drop Files for Transcription

Simply copy audio/video files to `~/cymatics/incoming/`. The service will automatically:
1. Detect new files
2. Process them with Whisper
3. Output results to `~/cymatics/completed/`

## 📁 Data Directory Structure

```
~/cymatics/
├── incoming/    # Drop files here for processing
├── processing/  # System internal use (locked)
├── completed/   # Output files (.mp3, .json, .txt)
└── failed/      # Error logs for failed files
```

## 🔧 Configuration

Environment variables (set in `.env` or export directly):

| Variable | Default | Description |
|----------|---------|-------------|
| `CYMATICS_APP_NAME` | `cymatics` | Application name |
| `DATA_DIR` | `/app/data` | Base data directory |
| `WHISPER_MODEL` | `medium` | Whisper model (tiny/base/small/medium/large) |
| `MODEL_UNLOAD_TIMEOUT` | `300` | Seconds before unloading idle model |
| `DEBOUNCE_SECONDS` | `2` | Wait time for file write completion |
| `CYCLE_POLL_INTERVAL` | `5` | Directory polling interval |

## ✅ API Endpoints

### Health Check
```http
GET /health -> {"status": "ok"}
```

### Upload File for Transcription
```http
POST /v1/transcribe
Content-Type: multipart/form-data
file: <audio/video file>

Response (202 Accepted):
{"id": "abc12345", "status": "queued"}
```

### Get Processing Status
```http
GET /v1/cycle/status

Response:
{
  "queue_length": 3,
  "current_file": "recording.mp3",
  "model_state": "ready",
  "recent_completed": ["file1.mp3", "file2.wav"]
}
```

## 🐳 Docker Deployment

Build and run for production:

```shell
just build
docker compose up -d
```

The container:
- Runs on `linux/arm64` platform
- Mounts `~/cymatics` for file I/O
- Caches Whisper models in `~/cymatics/cache`
- Exposes port 8000

## 🧪 Testing

```shell
just test     # Run full test suite
just unit-test   # Unit tests only
just intg-test   # Integration tests
just check    # Linting and type checking
```

## 🧱 Project Structure

```
├── src/cymatics/
│   ├── api/
│   │   ├── main.py           # FastAPI app with lifespan
│   │   ├── router.py         # API endpoints
│   │   └── dependencies.py   # Dependency injection
│   ├── config/
│   │   └── app_settings.py   # Pydantic settings
│   ├── models/               # Data models (Pydantic)
│   ├── protocols/            # Service interfaces
│   └── services/
│       ├── transmutation_service.py  # Whisper integration
│       └── cycle_scheduler.py        # Directory monitoring
├── dev/mocks/                # Mock services for testing
├── tests/
│   ├── unit/
│   ├── intg/
│   └── e2e/
├── justfile
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## 📝 Output Format

### JSON Metadata (`*.json`)
```json
{
  "id": "file_hash",
  "meta": {
    "model": "medium",
    "device": "cpu",
    "compute_type": "float32",
    "duration": 120.5,
    "language": "ja"
  },
  "text": "Full transcribed text...",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "Segment text..."
    }
  ]
}
```

### Plain Text (`*.txt`)
Contains just the transcribed text without metadata.
