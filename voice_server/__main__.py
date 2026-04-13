"""Entry point: python -m voice_server"""

import logging
import sys

from .config import OneShotConfig, ServerConfig, parse_args


def main(argv: list[str] | None = None):
    config = parse_args(argv)

    # List voices mode
    if isinstance(config, list):
        backend_name, models_dir = config
        logging.basicConfig(level=logging.WARNING)
        from .backends import get_backend
        backend = get_backend(backend_name)
        backend.init(models_dir)
        voices = backend.list_voices()
        if not voices:
            print(f"No voices found for backend '{backend_name}' in {models_dir}")
            print("Download model files and place them in the models directory.")
            sys.exit(1)
        print(f"Available voices ({backend_name}):\n")
        for v in voices:
            extra = f"  ({v.description})" if v.description else ""
            print(f"  {v.id:<40s} {v.language:<8s} {v.gender:<10s}{extra}")
        backend.shutdown()
        return

    # One-shot mode
    if isinstance(config, OneShotConfig):
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        from .backends import get_backend
        from .wav_utils import duration_ms, pcm_to_wav_bytes

        backend = get_backend(config.backend)
        backend.init(config.models_dir)

        voice_id = config.voice
        if not voice_id:
            voices = backend.list_voices()
            if not voices:
                print(f"No voices found for backend '{config.backend}' in {config.models_dir}")
                sys.exit(1)
            voice_id = voices[0].id

        print(f"Synthesizing with voice '{voice_id}'...")
        samples, sample_rate = backend.synthesize(config.text, voice_id, config.speed)
        wav_bytes = pcm_to_wav_bytes(samples, sample_rate)

        with open(config.output, "wb") as f:
            f.write(wav_bytes)

        dur = duration_ms(len(samples), sample_rate)
        print(f"Wrote {config.output} ({dur} ms, {sample_rate} Hz)")
        backend.shutdown()
        return

    # Server mode
    assert isinstance(config, ServerConfig)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from .server import create_app
    import uvicorn

    create_app(config.backend, config.models_dir)
    print(f"Starting voice server on {config.host}:{config.port} (backend={config.backend})")
    uvicorn.run(
        "voice_server.server:app",
        host=config.host,
        port=config.port,
        log_level=config.log_level,
    )


if __name__ == "__main__":
    main()
