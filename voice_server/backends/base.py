"""Abstract base class for TTS backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import numpy as np


@dataclass
class VoiceInfo:
    id: str
    name: str
    gender: str = "unknown"
    language: str = "en"
    model: str = ""
    description: str = ""


class TTSBackend(ABC):
    """All TTS backends implement this interface."""

    @abstractmethod
    def init(self, model_dir: str) -> None:
        """Load models / prepare for synthesis. Called once."""
        ...

    @abstractmethod
    def list_voices(self) -> list[VoiceInfo]:
        """Return available voices for this backend."""
        ...

    @abstractmethod
    def synthesize(
        self, text: str, voice_id: str, speed: float = 1.0
    ) -> tuple[np.ndarray, int]:
        """Synthesize speech from text.

        Returns:
            (pcm_samples, sample_rate) where pcm_samples is float32 in [-1, 1].
        """
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Release resources."""
        ...
