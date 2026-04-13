"""WAV encoding utilities -- float32 PCM to WAV bytes."""

import io
import struct

import numpy as np


def pcm_to_wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    """Convert float32 PCM samples to a complete WAV file in memory.

    Args:
        samples: float32 array in [-1.0, 1.0], mono.
        sample_rate: e.g. 22050.

    Returns:
        Complete WAV file as bytes (16-bit PCM, mono).
    """
    # Clip and convert to int16
    clipped = np.clip(samples, -1.0, 1.0)
    int16_samples = (clipped * 32767).astype(np.int16)
    raw_data = int16_samples.tobytes()

    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    data_size = len(raw_data)

    buf = io.BytesIO()
    # RIFF header
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    # fmt chunk
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))  # chunk size
    buf.write(struct.pack("<H", 1))  # PCM format
    buf.write(struct.pack("<H", num_channels))
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", byte_rate))
    buf.write(struct.pack("<H", block_align))
    buf.write(struct.pack("<H", bits_per_sample))
    # data chunk
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(raw_data)

    return buf.getvalue()


def duration_ms(num_samples: int, sample_rate: int) -> int:
    """Calculate audio duration in milliseconds."""
    return int(num_samples / sample_rate * 1000)
