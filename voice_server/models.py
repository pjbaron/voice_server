"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field


class SpeakRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=10000)
    voice: str = Field(default="", description="Voice ID. Empty = first available voice.")
    speed: float = Field(default=1.0, ge=0.1, le=5.0, description="Speed multiplier (1.0 = normal)")
    expression: str = Field(default="", description="Expression hints (e.g. 'warm, professional')")
    output: str = Field(default="stream", pattern="^(stream|file)$", description="'stream' returns WAV bytes, 'file' saves to disk")
    path: str = Field(default="", description="Output file path (required when output='file')")


class SpeakFileResponse(BaseModel):
    status: str
    path: str
    duration_ms: int


class VoiceEntry(BaseModel):
    id: str
    name: str
    gender: str
    language: str
    model: str
    description: str = ""


class VoicesResponse(BaseModel):
    voices: list[VoiceEntry]


class ModelEntry(BaseModel):
    id: str
    name: str
    voices: int
    loaded: bool


class ModelsResponse(BaseModel):
    models: list[ModelEntry]


class HealthResponse(BaseModel):
    status: str
    active_backend: str
    uptime_s: int
