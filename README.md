# voice-server

Standalone TTS server with pluggable model backends. Accepts JSON requests, returns WAV audio. Runs as a local HTTP server or a one-shot CLI tool.

Licensed GPL-3.0 (due to espeak-ng dependency for phonemization).

## Quick Start

```bash
# Install
pip install -e .

# Download Kokoro model (recommended)
mkdir -p models/kokoro && cd models/kokoro
curl -L -o kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/kokoro-v1.0.onnx
curl -L -o voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/voices-v1.0.bin
cd ../..

# Start server
python -m voice_server --backend kokoro --port 5050

# Generate speech (from another terminal)
curl -X POST http://localhost:5050/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"af_bella"}' \
  --output speech.wav
```

Or without a server:
```bash
python -m voice_server --backend kokoro --text "Hello world" --voice af_bella --output speech.wav
```

To build as an executable:
```pyinstaller voice-server.spec
```

## Requirements

- Python 3.10+
- ~400MB disk for Kokoro model, ~65MB for Piper model

## Installation

```bash
git clone <this-repo>
cd voice-server
pip install -e .
```

## Model Downloads

Models are not included in the repo. Download them into the `models/` directory.

### Kokoro (recommended)

54 voices, high quality, 24kHz output. Best with GPU but works on CPU.

```bash
mkdir -p models/kokoro
cd models/kokoro

# Model (310MB)
curl -L -o kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/kokoro-v1.0.onnx

# Voices (27MB)
curl -L -o voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/latest/download/voices-v1.0.bin
```

Smaller model variants (same voices file):
| Variant | Size | Download |
|---------|------|----------|
| fp32 | 310 MB | `kokoro-v1.0.onnx` |
| fp16 | 169 MB | `kokoro-v1.0.fp16.onnx` (rename to `kokoro.onnx`) |
| int8 | 88 MB | `kokoro-v1.0.int8.onnx` (rename to `kokoro.onnx`) |

All variants available at: `https://github.com/thewh1teagle/kokoro-onnx/releases/latest`

### Piper

900+ voices, very fast on CPU, 22kHz output. Each voice is a separate download.

```bash
mkdir -p models

# Example: en_US-lessac-medium (63MB)
curl -L -o models/en_US-lessac-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx

curl -L -o models/en_US-lessac-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

Each Piper voice needs two files: `<name>.onnx` + `<name>.onnx.json`. Browse all voices at:
`https://huggingface.co/rhasspy/piper-voices/tree/main/en`

Multi-speaker model (904 voices in one download):
```bash
curl -L -o models/en_US-libritts_r-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx

curl -L -o models/en_US-libritts_r-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json
```

## Supported Models

| Backend | Voices | Quality | Speed (CPU) | Speed (GPU) | Sample Rate | Model Size |
|---------|--------|---------|-------------|-------------|-------------|------------|
| `kokoro` | 54 (American/British, M/F) | High | ~0.5x real-time | ~25x real-time | 24 kHz | 88-310 MB |
| `piper` | 900+ (many languages) | Medium | ~5x real-time | N/A | 22 kHz | 22-75 MB per voice |

## Usage

### Server Mode

```bash
# Start with Kokoro (recommended)
python -m voice_server --backend kokoro --port 5050

# Start with Piper
python -m voice_server --backend piper --port 5050

# Custom models directory
python -m voice_server --backend kokoro --models-dir /path/to/models --port 5050
```

Server binds to `127.0.0.1` (localhost only) by default. Use `--host 0.0.0.0` to expose on the network.

### One-Shot Mode (no server)

```bash
# Generate a WAV file directly
python -m voice_server --backend kokoro --text "Hello world" --voice af_bella --output hello.wav

# Use default voice
python -m voice_server --backend kokoro --text "Hello world" --output hello.wav
```

### List Voices

```bash
python -m voice_server --backend kokoro --list-voices
python -m voice_server --backend piper --list-voices
```

### All CLI Options

```
--port PORT         Server port (default: 5050)
--host HOST         Bind address (default: 127.0.0.1)
--backend NAME      TTS backend: kokoro, piper (default: piper)
--models-dir PATH   Path to model files (default: ./models)
--log-level LEVEL   debug, info, warning, error (default: info)
--text TEXT         One-shot mode: text to synthesize
--voice ID          Voice ID (default: first available)
--speed FLOAT       Speed multiplier (default: 1.0)
--output PATH       One-shot mode: output WAV path
--list-voices       List available voices and exit
```

## API Reference

Base URL: `http://localhost:5050`

Interactive docs at `http://localhost:5050/docs` (auto-generated by FastAPI).

### GET /health

Returns server status.

**Response** `200 application/json`:
```json
{
  "status": "ok",
  "active_backend": "kokoro",
  "uptime_s": 3600
}
```

### GET /voices

Returns available voices for the active backend.

**Response** `200 application/json`:
```json
{
  "voices": [
    {
      "id": "af_bella",
      "name": "Bella",
      "gender": "female",
      "language": "en_US",
      "model": "kokoro",
      "description": "american female"
    }
  ]
}
```

### GET /models

Returns all registered backends and their status.

**Response** `200 application/json`:
```json
{
  "models": [
    {"id": "kokoro", "name": "Kokoro", "voices": 54, "loaded": true},
    {"id": "piper", "name": "Piper", "voices": 0, "loaded": false}
  ]
}
```

### POST /speak

Synthesize speech from text.

**Request** `application/json`:
```json
{
  "text": "Hello, welcome aboard captain.",
  "voice": "af_bella",
  "speed": 1.0,
  "expression": "warm, professional",
  "output": "stream"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | string | required | Text to synthesize (1-10000 chars) |
| `voice` | string | `""` | Voice ID. Empty = first available voice. |
| `speed` | float | `1.0` | Speed multiplier (0.1 - 5.0) |
| `expression` | string | `""` | Expression hints (reserved for future use) |
| `output` | string | `"stream"` | `"stream"` returns WAV bytes, `"file"` saves to disk |
| `path` | string | `""` | File path (required when output is `"file"`) |

**Response (stream mode)** `200 audio/wav`:

Raw WAV file bytes (16-bit PCM, mono). Custom headers:
- `X-Sample-Rate`: e.g. `24000`
- `X-Duration-Ms`: audio duration in milliseconds
- `X-Synthesis-Ms`: time taken to synthesize

**Response (file mode)** `200 application/json`:
```json
{
  "status": "ok",
  "path": "./output.wav",
  "duration_ms": 1850
}
```

**Errors** `400` or `500 application/json`:
```json
{
  "detail": "Unknown voice 'xyz'. Available: af_alloy, af_bella, ..."
}
```

## Integration Examples

### curl

```bash
# Get WAV to file
curl -X POST http://localhost:5050/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"af_bella"}' \
  --output speech.wav

# Save server-side
curl -X POST http://localhost:5050/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"af_bella","output":"file","path":"speech.wav"}'
```

### Python

```python
import requests

resp = requests.post("http://localhost:5050/speak", json={
    "text": "Hello world",
    "voice": "af_bella",
    "speed": 1.0,
})
with open("speech.wav", "wb") as f:
    f.write(resp.content)
```

### C (libcurl)

```c
CURL *curl = curl_easy_init();
curl_easy_setopt(curl, CURLOPT_URL, "http://localhost:5050/speak");
curl_easy_setopt(curl, CURLOPT_POSTFIELDS,
    "{\"text\":\"Hello world\",\"voice\":\"af_bella\"}");

struct curl_slist *headers = NULL;
headers = curl_slist_append(headers, "Content-Type: application/json");
curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);

curl_easy_perform(curl);
// write_callback receives raw WAV bytes
```

## WAV Output Format

All backends produce:
- **Format**: PCM signed 16-bit little-endian
- **Channels**: 1 (mono)
- **Sample rate**: backend-dependent (Kokoro: 24000 Hz, Piper: 22050 Hz)
- **Header**: Standard 44-byte RIFF/WAV header

The `X-Sample-Rate` response header provides the exact rate for the active backend.

## Adding a New Backend

Create `voice_server/backends/mybackend.py`:

```python
from . import register
from .base import TTSBackend, VoiceInfo

class MyBackend(TTSBackend):
    def init(self, model_dir: str) -> None:
        # Load model files from model_dir
        ...

    def list_voices(self) -> list[VoiceInfo]:
        return [VoiceInfo(id="voice1", name="Voice 1", model="mybackend")]

    def synthesize(self, text: str, voice_id: str, speed: float = 1.0):
        # Return (numpy_float32_array, sample_rate)
        ...

    def shutdown(self) -> None:
        ...

register("mybackend", MyBackend)
```

Then add to `voice_server/backends/__init__.py`:
```python
from . import mybackend  # noqa
```

## Project Structure

```
voice-server/
  voice_server/
    __init__.py
    __main__.py            Entry point
    server.py              FastAPI routes
    config.py              CLI argument parsing
    models.py              Pydantic request/response schemas
    wav_utils.py           PCM-to-WAV encoding
    backends/
      __init__.py          Backend registry
      base.py              Abstract base class
      piper_backend.py     Piper TTS
      kokoro_backend.py    Kokoro TTS
  models/                  Model files (gitignored)
    kokoro/
      kokoro.onnx
      voices.bin
    en_US-lessac-medium.onnx
    en_US-lessac-medium.onnx.json
  tests/
```
