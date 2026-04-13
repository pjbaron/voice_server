"""FastAPI application -- route handlers for the TTS server."""

import logging
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from .backends import get_backend, list_backends
from .backends.base import TTSBackend
from .models import (
    HealthResponse,
    ModelEntry,
    ModelsResponse,
    SpeakFileResponse,
    SpeakRequest,
    VoiceEntry,
    VoicesResponse,
)
from .wav_utils import duration_ms, pcm_to_wav_bytes

log = logging.getLogger(__name__)

app = FastAPI(title="Voice Server", version="0.1.0")

# Module-level state -- set by create_app()
_backend: TTSBackend | None = None
_backend_name: str = ""
_start_time: float = 0.0


def create_app(backend_name: str, models_dir: str) -> FastAPI:
    """Initialize the backend and return the configured FastAPI app."""
    global _backend, _backend_name, _start_time

    _backend_name = backend_name
    _backend = get_backend(backend_name)
    _backend.init(models_dir)
    _start_time = time.time()

    return app


def _get_backend() -> TTSBackend:
    if _backend is None:
        raise HTTPException(status_code=503, detail="Backend not initialized")
    return _backend


def _resolve_voice(backend: TTSBackend, voice_id: str) -> str:
    """If voice_id is empty, return the first available voice."""
    if voice_id:
        return voice_id
    voices = backend.list_voices()
    if not voices:
        raise HTTPException(status_code=503, detail="No voices available")
    return voices[0].id


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        active_backend=_backend_name,
        uptime_s=int(time.time() - _start_time),
    )


@app.get("/voices", response_model=VoicesResponse)
def voices():
    backend = _get_backend()
    voice_list = backend.list_voices()
    return VoicesResponse(
        voices=[
            VoiceEntry(
                id=v.id,
                name=v.name,
                gender=v.gender,
                language=v.language,
                model=v.model,
                description=v.description,
            )
            for v in voice_list
        ]
    )


@app.get("/models", response_model=ModelsResponse)
def models():
    entries = []
    for name in list_backends():
        is_active = name == _backend_name
        num_voices = 0
        if is_active and _backend:
            num_voices = len(_backend.list_voices())
        entries.append(ModelEntry(
            id=name,
            name=name.title(),
            voices=num_voices,
            loaded=is_active,
        ))
    return ModelsResponse(models=entries)


@app.post("/speak")
def speak(req: SpeakRequest):
    backend = _get_backend()
    voice_id = _resolve_voice(backend, req.voice)

    t0 = time.time()
    try:
        samples, sample_rate = backend.synthesize(req.text, voice_id, req.speed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("Synthesis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synthesis error: {e}")

    elapsed_ms = int((time.time() - t0) * 1000)
    dur_ms = duration_ms(len(samples), sample_rate)
    log.info(
        "Synthesized %d ms audio in %d ms (voice=%s, text=%.40s...)",
        dur_ms, elapsed_ms, voice_id, req.text,
    )

    wav_bytes = pcm_to_wav_bytes(samples, sample_rate)

    if req.output == "file":
        if not req.path:
            raise HTTPException(status_code=400, detail="'path' required when output='file'")
        try:
            with open(req.path, "wb") as f:
                f.write(wav_bytes)
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")
        return SpeakFileResponse(status="ok", path=req.path, duration_ms=dur_ms)

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={
            "X-Sample-Rate": str(sample_rate),
            "X-Duration-Ms": str(dur_ms),
            "X-Synthesis-Ms": str(elapsed_ms),
        },
    )
