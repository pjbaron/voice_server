"""CLI argument parsing and server configuration."""

import argparse
from dataclasses import dataclass


@dataclass
class ServerConfig:
    port: int = 5050
    host: str = "127.0.0.1"
    backend: str = "piper"
    models_dir: str = "./models"
    log_level: str = "info"


@dataclass
class OneShotConfig:
    text: str
    voice: str
    output: str
    speed: float = 1.0
    backend: str = "piper"
    models_dir: str = "./models"


def parse_args(argv: list[str] | None = None) -> ServerConfig | OneShotConfig | list:
    parser = argparse.ArgumentParser(
        prog="voice-server",
        description="Standalone TTS server with pluggable model backends",
    )

    parser.add_argument("--port", type=int, default=5050, help="Server port (default: 5050)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--backend", default="piper", help="TTS backend (default: piper)")
    parser.add_argument("--models-dir", default="./models", help="Path to model files")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])

    # One-shot mode
    parser.add_argument("--text", help="Text to synthesize (one-shot mode, no server)")
    parser.add_argument("--voice", default="", help="Voice ID")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier")
    parser.add_argument("--output", help="Output WAV file path (one-shot mode)")

    # List mode
    parser.add_argument("--list-voices", action="store_true", help="List available voices and exit")

    args = parser.parse_args(argv)

    if args.list_voices:
        return [args.backend, args.models_dir]

    if args.text:
        if not args.output:
            parser.error("--output is required when using --text (one-shot mode)")
        return OneShotConfig(
            text=args.text,
            voice=args.voice,
            output=args.output,
            speed=args.speed,
            backend=args.backend,
            models_dir=args.models_dir,
        )

    return ServerConfig(
        port=args.port,
        host=args.host,
        backend=args.backend,
        models_dir=args.models_dir,
        log_level=args.log_level,
    )
