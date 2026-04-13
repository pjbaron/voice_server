"""Backend registry -- maps backend names to classes."""

from .base import TTSBackend, VoiceInfo

_REGISTRY: dict[str, type[TTSBackend]] = {}


def register(name: str, cls: type[TTSBackend]) -> None:
    _REGISTRY[name] = cls


def get_backend(name: str) -> TTSBackend:
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise ValueError(f"Unknown backend {name!r}. Available: {available}")
    return _REGISTRY[name]()


def list_backends() -> list[str]:
    return sorted(_REGISTRY)


# Import backends so they self-register
from . import piper_backend  # noqa: E402, F401
from . import kokoro_backend  # noqa: E402, F401
