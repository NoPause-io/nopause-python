"""Configuration dataclasses for the api module.
"""
from pydantic import BaseModel


class AudioConfig(BaseModel):
    """Control audio behavior.
    (Currently, we don't have any customizable audio parameters.)
    """

class DualStreamConfig(BaseModel):
    """Control dual-stream synthesis behavior."""
    stream_in: bool = True
    stream_out: bool = True

class ModelConfig(BaseModel):
    voice_id: str
    model_name: str
    language: str
    dual_stream: DualStreamConfig
