"""Error definitions for NoPause SDK."""

from typing import Optional

class APIError(Exception):
    """Base class for all NoPause API errors."""

    def __init__(self, message: str, code: Optional[int] = None):
        """Initialize an API error.

        Args:
            message: A human-readable error message.
            code: An optional error code.
        """
        self.message = message
        self.code = code

    def __str__(self):
        if self.code is None:
            return f"{self.message}"
        else:
            return f"{self.message} (code={self.code})"

    def __repr__(self):
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"

class FormatError(APIError):
    """Raised when the format is invalid."""

class InvalidRequestError(APIError):
    """Raised when the request is invalid."""

class NoPauseError(APIError):
    """Raised when the NoPause API returns an error."""
