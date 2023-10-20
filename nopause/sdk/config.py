"""Configuration dataclasses for the api module.
"""
from pydantic import BaseModel, Field, root_validator


class AudioConfig(BaseModel):
    """Control audio behavior.
    """
    # todo
    # audio_encoding: str = "wav"
    # speaking_rate: float = 1.0
    # volume_gain_db: float = 0.0
    sample_rate: int = Field(24000, ge=8000, le=24000, alias='sample_rate_hertz', description="sample rate hertz")

    @root_validator(pre=True)
    def multi_alias(cls, values: dict):
        if 'sample_rate' in values:
            values['sample_rate_hertz'] = values['sample_rate']
        return values

class DualStreamConfig(BaseModel):
    """Control dual-stream synthesis behavior."""
    stream_in: bool = True
    stream_out: bool = True

class ModelConfig(BaseModel):
    voice_id: str
    model_name: str
    language: str
    dual_stream: DualStreamConfig
