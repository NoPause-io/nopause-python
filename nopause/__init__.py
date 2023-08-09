""" NoPause Python SDK
"""

import os

from .core import AudioChunk
from .sdk import (
    Synthesis,
    AudioConfig,
    DualStreamConfig,
    APIError,
    InvalidRequestError,
    NoPauseError,
)
from .version import VERSION

api_key = os.environ.get("NOPAUSE_API_KEY")

api_base = os.environ.get("NOPAUSE_API_BASE", "wss://api.nopause.com/v1")

api_version = os.environ.get(
    "NOPAUSE_API_VERSION",
)

__version__ = VERSION
__all__ = [
    "APIError",
    "AudioConfig",
    "AudioChunk",
    "DualStreamConfig",
    "InvalidRequestError",
    "NoPauseError",
    "Synthesis",
    "api_base",
    "api_key",
    "api_version",
]
