"""Configuration dataclasses for the api module.
"""
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Control audio behavior.
    (Currently, we don't have any customizable audio parameters.)
    """


@dataclass
class DualStreamConfig:
    """Control dual-stream synthesis behavior."""
    stream_in: bool = True
    stream_out: bool = True
