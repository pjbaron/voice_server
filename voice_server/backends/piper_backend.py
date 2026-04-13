"""Piper TTS backend -- fast VITS-based synthesis with 900+ voices."""

import logging
import os
from pathlib import Path

import numpy as np

from . import register
from .base import TTSBackend, VoiceInfo

log = logging.getLogger(__name__)


class PiperBackend(TTSBackend):

    def __init__(self):
        self._model_dir: Path | None = None
        self._voices: dict[str, Path] = {}  # voice_id -> onnx path
        self._loaded: dict[str, object] = {}  # voice_id -> PiperVoice (lazy)

    def init(self, model_dir: str) -> None:
        self._model_dir = Path(model_dir)
        self._scan_voices()
        log.info("Piper backend: found %d voice(s) in %s", len(self._voices), model_dir)

    def _scan_voices(self) -> None:
        """Find all .onnx files with matching .onnx.json configs."""
        self._voices.clear()
        if not self._model_dir or not self._model_dir.is_dir():
            return
        for onnx_file in self._model_dir.rglob("*.onnx"):
            config_file = Path(str(onnx_file) + ".json")
            if config_file.exists():
                voice_id = onnx_file.stem
                self._voices[voice_id] = onnx_file
                log.debug("  found voice: %s", voice_id)

    def _get_voice(self, voice_id: str):
        """Lazy-load a PiperVoice model."""
        if voice_id in self._loaded:
            return self._loaded[voice_id]

        if voice_id not in self._voices:
            raise ValueError(
                f"Unknown voice {voice_id!r}. "
                f"Available: {', '.join(sorted(self._voices)) or '(none)'}"
            )

        from piper import PiperVoice

        path = self._voices[voice_id]
        log.info("Loading Piper voice: %s from %s", voice_id, path)
        voice = PiperVoice.load(str(path))
        self._loaded[voice_id] = voice
        return voice

    def list_voices(self) -> list[VoiceInfo]:
        result = []
        for voice_id, path in sorted(self._voices.items()):
            # Parse voice ID convention: {lang}_{REGION}-{name}-{quality}
            # e.g. en_US-lessac-medium -> language=en_US, name=lessac
            parts = voice_id.split("-")
            if parts and "_" in parts[0]:
                language = parts[0]  # en_US
                name = parts[1] if len(parts) >= 2 else voice_id
            else:
                language = parts[0] if parts else "en"
                name = parts[1] if len(parts) >= 2 else voice_id

            # Check for multi-speaker
            voice_obj = None
            description = ""
            try:
                voice_obj = self._get_voice(voice_id)
                num_speakers = getattr(voice_obj.config, "num_speakers", 0)
                if num_speakers and num_speakers > 1:
                    description = f"{num_speakers} speakers"
            except Exception:
                pass

            result.append(VoiceInfo(
                id=voice_id,
                name=name.replace("_", " ").title(),
                language=language,
                model="piper",
                description=description,
            ))
        return result

    def synthesize(
        self, text: str, voice_id: str, speed: float = 1.0
    ) -> tuple[np.ndarray, int]:
        voice = self._get_voice(voice_id)

        from piper import SynthesisConfig

        config = SynthesisConfig()
        if speed != 1.0:
            config.length_scale = 1.0 / speed  # length_scale < 1 = faster

        chunks = []
        for audio_chunk in voice.synthesize(text, config):
            chunks.append(audio_chunk.audio_float_array)

        if not chunks:
            raise RuntimeError(f"Piper produced no audio for: {text!r}")

        samples = np.concatenate(chunks)
        sample_rate = voice.config.sample_rate
        return samples, sample_rate

    def shutdown(self) -> None:
        self._loaded.clear()
        self._voices.clear()
        log.info("Piper backend shut down.")


register("piper", PiperBackend)
