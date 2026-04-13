"""Kokoro TTS backend -- high quality 82M parameter synthesis via ONNX."""

import logging
from pathlib import Path

import numpy as np

from . import register
from .base import TTSBackend, VoiceInfo

log = logging.getLogger(__name__)

# Voice metadata for known Kokoro voices
_VOICE_META = {
    "af": ("Default Female", "female", "american"),
    "af_alloy": ("Alloy", "female", "american"),
    "af_aoede": ("Aoede", "female", "american"),
    "af_bella": ("Bella", "female", "american"),
    "af_heart": ("Heart", "female", "american"),
    "af_jessica": ("Jessica", "female", "american"),
    "af_kore": ("Kore", "female", "american"),
    "af_nicole": ("Nicole", "female", "american"),
    "af_nova": ("Nova", "female", "american"),
    "af_river": ("River", "female", "american"),
    "af_sarah": ("Sarah", "female", "american"),
    "af_sky": ("Sky", "female", "american"),
    "am_adam": ("Adam", "male", "american"),
    "am_echo": ("Echo", "male", "american"),
    "am_eric": ("Eric", "male", "american"),
    "am_liam": ("Liam", "male", "american"),
    "am_michael": ("Michael", "male", "american"),
    "am_onyx": ("Onyx", "male", "american"),
    "bf_emma": ("Emma", "female", "british"),
    "bf_isabella": ("Isabella", "female", "british"),
    "bf_lily": ("Lily", "female", "british"),
    "bm_daniel": ("Daniel", "male", "british"),
    "bm_fable": ("Fable", "male", "british"),
    "bm_george": ("George", "male", "british"),
    "bm_lewis": ("Lewis", "male", "british"),
}


class KokoroBackend(TTSBackend):

    def __init__(self):
        self._model_dir: Path | None = None
        self._kokoro = None  # Lazy loaded

    def init(self, model_dir: str) -> None:
        self._model_dir = Path(model_dir)
        kokoro_dir = self._model_dir / "kokoro"
        model_path = kokoro_dir / "kokoro.onnx"
        voices_path = kokoro_dir / "voices.bin"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Kokoro model not found at {model_path}. "
                f"Download kokoro.onnx and voices.bin into {kokoro_dir}"
            )
        if not voices_path.exists():
            raise FileNotFoundError(
                f"Kokoro voices not found at {voices_path}. "
                f"Download voices.bin into {kokoro_dir}"
            )

        log.info("Kokoro backend: model at %s", kokoro_dir)

    def _get_kokoro(self):
        """Lazy-load the Kokoro model on first synthesis."""
        if self._kokoro is not None:
            return self._kokoro

        from kokoro_onnx import Kokoro

        kokoro_dir = self._model_dir / "kokoro"
        log.info("Loading Kokoro model...")
        self._kokoro = Kokoro(
            model_path=str(kokoro_dir / "kokoro.onnx"),
            voices_path=str(kokoro_dir / "voices.bin"),
        )
        log.info("Kokoro loaded. %d voices available.", len(self._kokoro.get_voices()))
        return self._kokoro

    def list_voices(self) -> list[VoiceInfo]:
        kokoro = self._get_kokoro()
        result = []
        for voice_id in sorted(kokoro.get_voices()):
            meta = _VOICE_META.get(voice_id, (voice_id, "unknown", "unknown"))
            name, gender, accent = meta
            result.append(VoiceInfo(
                id=voice_id,
                name=name,
                gender=gender,
                language=f"en_{accent[:2].upper()}",
                model="kokoro",
                description=f"{accent} {gender}",
            ))
        return result

    def synthesize(
        self, text: str, voice_id: str, speed: float = 1.0
    ) -> tuple[np.ndarray, int]:
        kokoro = self._get_kokoro()

        available = kokoro.get_voices()
        if voice_id not in available:
            raise ValueError(
                f"Unknown voice {voice_id!r}. "
                f"Available: {', '.join(available[:10])}..."
            )

        samples, sample_rate = kokoro.create(text, voice=voice_id, speed=speed)
        if len(samples) == 0:
            raise RuntimeError(f"Kokoro produced no audio for: {text!r}")

        return samples, sample_rate

    def shutdown(self) -> None:
        self._kokoro = None
        log.info("Kokoro backend shut down.")


register("kokoro", KokoroBackend)
