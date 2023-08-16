""" NoPause Python SDK
"""

import os

from .core import AudioChunk, TextChunk
from .sdk import (
    Synthesis,
    AudioConfig,
    ModelConfig,
    DualStreamConfig,
    APIError,
    InvalidRequestError,
    NoPauseError,
)
from .version import VERSION

api_key = None
api_base = 'wss://api.nopause.io/'
api_version = 'v1'

__version__ = VERSION

__all__ = [
    "APIError",
    "AudioConfig",
    "AudioChunk",
    "TextChunk",
    "AudioConfig",
    "DualStreamConfig",
    "ModelConfig",
    "InvalidRequestError",
    "NoPauseError",
    "Synthesis",
    "api_base",
    "api_key",
    "api_version",
]
