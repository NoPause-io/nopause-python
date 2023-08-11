""" A simple wrapper of returned audio data from NoPause
"""
from pydantic import BaseModel

class AudioChunk(BaseModel):
    """A simple wrapper of returned audio data from NoPause
    """
    data: bytes
    chunk_id: int
    sample_rate: int
    channels: int
    rtf: float
    chunk_size_us: int
    # is_last_chunk: bool

    @property
    def duration(self) -> float:
        """Return the duration of the audio in seconds."""
        return self.chunk_size_us / 1e6

    @property
    def n_samples(self):
        """Return number of samples."""
        return len(self.data) // 2

class TextChunk(BaseModel):
    text: str
    is_end: bool = False
